#!/usr/bin/env python3
"""Process raw ASTRA NEUZU data into aggregated CSVs.

Uses chunked pandas processing to stay within 7GB RAM (GitHub Actions).
Applies mappings.yaml for classification. Unknown values → "Other".
"""

import os
import sys
import yaml
import pandas as pd
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "processed"
MAPPINGS_FILE = ROOT / "mappings.yaml"
WARNINGS_FILE = ROOT / "warnings.log"

CHUNK_SIZE = 100_000

# Only columns we need (by name, not position)
USE_COLS = [
    "Fahrzeugart",
    "Marke",
    "Treibstoff",
    "Farbe_1",
    "Schildfarbe",
    "Neuzulassungen_von",
    "Neuzulassungen_bis",
    "Antriebsart",  # 4x4 detection
]


def load_mappings() -> dict:
    with open(MAPPINGS_FILE) as f:
        return yaml.safe_load(f)


def safe_map(value: str, mapping: dict, default: str = "Other") -> str:
    """Map a value using a dictionary, returning default if not found."""
    if pd.isna(value):
        return default
    v = str(value).strip().upper()
    # Try exact match first
    for key, val in mapping.items():
        if str(key).upper() == v:
            return val
    return default


def find_raw_files() -> list[Path]:
    """Find all NEUZU*.txt files in raw directory."""
    if not RAW_DIR.exists():
        print(f"ERROR: {RAW_DIR} does not exist. Run download.py first.")
        sys.exit(1)
    files = sorted(RAW_DIR.glob("NEUZU*.txt"))
    if not files:
        print(f"ERROR: No NEUZU*.txt files in {RAW_DIR}. Run download.py first.")
        sys.exit(1)
    return files


def detect_separator(filepath: Path) -> str:
    """Auto-detect TSV vs CSV."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        header = f.readline()
    if "\t" in header:
        return "\t"
    return ","


def process_file(filepath: Path, mappings: dict, warnings: set) -> dict:
    """Process a single NEUZU file in chunks. Returns aggregation dicts."""
    sep = detect_separator(filepath)
    print(f"  Processing: {filepath.name} (sep={'TAB' if sep == chr(9) else 'COMMA'})")

    # Check which of our desired columns actually exist
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        header_cols = [c.strip() for c in f.readline().split(sep)]

    available_cols = [c for c in USE_COLS if c in header_cols]
    missing_cols = [c for c in USE_COLS if c not in header_cols]
    if missing_cols:
        print(f"    Note: missing columns: {missing_cols}")

    agg = {
        "by_month": {},        # (year, month) → count
        "by_fuel": {},         # fuel_type → count
        "by_brand": {},        # brand → count
        "by_origin": {},       # country → count
        "by_continent": {},    # continent → count
        "by_color": {},        # color → count
        "by_usage": {},        # usage → count
        "by_fuel_month": {},   # (year, month, fuel) → count
        "by_4x4": {},          # (year, month, is_4x4) → count
    }

    brand_origin = mappings.get("brand_origin", {})
    country_continent = mappings.get("country_continent", {})
    fuel_types = mappings.get("fuel_types", {})
    colors = mappings.get("colors", {})
    plate_usage = mappings.get("plate_usage", {})

    dtype_map = {c: "str" for c in available_cols}
    rows_total = 0

    try:
        reader = pd.read_csv(
            filepath,
            sep=sep,
            usecols=available_cols,
            dtype=dtype_map,
            chunksize=CHUNK_SIZE,
            encoding="utf-8",
            on_bad_lines="skip",
        )
    except Exception as e:
        print(f"    ERROR reading {filepath.name}: {e}")
        return agg

    for chunk in reader:
        # Filter to Personenwagen only
        if "Fahrzeugart" in chunk.columns:
            chunk = chunk[chunk["Fahrzeugart"].str.contains("Personenwagen", case=False, na=False)]

        if chunk.empty:
            continue

        rows_total += len(chunk)

        # Extract year/month from registration period
        if "Neuzulassungen_von" in chunk.columns:
            dates = pd.to_datetime(chunk["Neuzulassungen_von"], errors="coerce", dayfirst=True)
            chunk["_year"] = dates.dt.year
            chunk["_month"] = dates.dt.month
        else:
            chunk["_year"] = None
            chunk["_month"] = None

        # Monthly totals
        for (y, m), grp in chunk.groupby(["_year", "_month"]):
            if pd.notna(y) and pd.notna(m):
                key = (int(y), int(m))
                agg["by_month"][key] = agg["by_month"].get(key, 0) + len(grp)

        # Fuel type
        if "Treibstoff" in chunk.columns:
            for raw_fuel, grp in chunk.groupby("Treibstoff"):
                fuel = safe_map(raw_fuel, fuel_types)
                if fuel == "Other" and pd.notna(raw_fuel) and str(raw_fuel).strip():
                    warnings.add(f"fuel:{raw_fuel}")
                agg["by_fuel"][fuel] = agg["by_fuel"].get(fuel, 0) + len(grp)

                # Fuel by month
                for (y, m), sub in grp.groupby(["_year", "_month"]):
                    if pd.notna(y) and pd.notna(m):
                        key = (int(y), int(m), fuel)
                        agg["by_fuel_month"][key] = agg["by_fuel_month"].get(key, 0) + len(sub)

        # Brand + origin
        if "Marke" in chunk.columns:
            for raw_brand, grp in chunk.groupby("Marke"):
                brand = str(raw_brand).strip() if pd.notna(raw_brand) else "Other"
                country = safe_map(raw_brand, brand_origin)
                continent = safe_map(country, country_continent)
                if country == "Other" and brand != "Other" and brand:
                    warnings.add(f"brand:{brand}")

                agg["by_brand"][brand] = agg["by_brand"].get(brand, 0) + len(grp)
                agg["by_origin"][country] = agg["by_origin"].get(country, 0) + len(grp)
                agg["by_continent"][continent] = agg["by_continent"].get(continent, 0) + len(grp)

        # Color
        if "Farbe_1" in chunk.columns:
            for raw_color, grp in chunk.groupby("Farbe_1"):
                color = safe_map(raw_color, colors)
                if color == "Other" and pd.notna(raw_color) and str(raw_color).strip():
                    warnings.add(f"color:{raw_color}")
                agg["by_color"][color] = agg["by_color"].get(color, 0) + len(grp)

        # Usage (plate color)
        if "Schildfarbe" in chunk.columns:
            for raw_plate, grp in chunk.groupby("Schildfarbe"):
                usage = safe_map(raw_plate, plate_usage)
                if usage == "Other" and pd.notna(raw_plate) and str(raw_plate).strip():
                    warnings.add(f"plate:{raw_plate}")
                agg["by_usage"][usage] = agg["by_usage"].get(usage, 0) + len(grp)

        # 4x4 detection
        if "Antriebsart" in chunk.columns:
            for (y, m), grp in chunk.groupby(["_year", "_month"]):
                if pd.notna(y) and pd.notna(m):
                    key_4x4 = (int(y), int(m), True)
                    key_other = (int(y), int(m), False)
                    is_4x4 = grp["Antriebsart"].str.contains("allrad|4x4|4WD|AWD", case=False, na=False)
                    agg["by_4x4"][key_4x4] = agg["by_4x4"].get(key_4x4, 0) + int(is_4x4.sum())
                    agg["by_4x4"][key_other] = agg["by_4x4"].get(key_other, 0) + int((~is_4x4).sum())

    print(f"    Personenwagen rows: {rows_total:,}")
    return agg


def merge_aggs(total: dict, new: dict) -> dict:
    """Merge two aggregation dicts."""
    for key in new:
        if key not in total:
            total[key] = {}
        for k, v in new[key].items():
            total[key][k] = total[key].get(k, 0) + v
    return total


def save_csvs(agg: dict):
    """Save aggregated data to CSV files."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Monthly totals
    rows = [{"year": k[0], "month": k[1], "count": v} for k, v in sorted(agg["by_month"].items())]
    if rows:
        pd.DataFrame(rows).to_csv(OUT_DIR / "monthly_totals.csv", index=False)

    # Fuel totals
    rows = [{"fuel_type": k, "count": v} for k, v in sorted(agg["by_fuel"].items(), key=lambda x: -x[1])]
    if rows:
        pd.DataFrame(rows).to_csv(OUT_DIR / "fuel_totals.csv", index=False)

    # Fuel by month
    rows = [{"year": k[0], "month": k[1], "fuel_type": k[2], "count": v}
            for k, v in sorted(agg["by_fuel_month"].items())]
    if rows:
        pd.DataFrame(rows).to_csv(OUT_DIR / "fuel_by_month.csv", index=False)

    # Brand totals
    rows = [{"brand": k, "count": v} for k, v in sorted(agg["by_brand"].items(), key=lambda x: -x[1])]
    if rows:
        pd.DataFrame(rows).to_csv(OUT_DIR / "brand_totals.csv", index=False)

    # Origin totals
    rows = [{"country": k, "count": v} for k, v in sorted(agg["by_origin"].items(), key=lambda x: -x[1])]
    if rows:
        pd.DataFrame(rows).to_csv(OUT_DIR / "origin_totals.csv", index=False)

    # Continent totals
    rows = [{"continent": k, "count": v} for k, v in sorted(agg["by_continent"].items(), key=lambda x: -x[1])]
    if rows:
        pd.DataFrame(rows).to_csv(OUT_DIR / "continent_totals.csv", index=False)

    # Color totals
    rows = [{"color": k, "count": v} for k, v in sorted(agg["by_color"].items(), key=lambda x: -x[1])]
    if rows:
        pd.DataFrame(rows).to_csv(OUT_DIR / "color_totals.csv", index=False)

    # Usage totals
    rows = [{"usage": k, "count": v} for k, v in sorted(agg["by_usage"].items(), key=lambda x: -x[1])]
    if rows:
        pd.DataFrame(rows).to_csv(OUT_DIR / "usage_totals.csv", index=False)

    # 4x4 by month
    rows = [{"year": k[0], "month": k[1], "is_4x4": k[2], "count": v}
            for k, v in sorted(agg["by_4x4"].items())]
    if rows:
        pd.DataFrame(rows).to_csv(OUT_DIR / "4x4_by_month.csv", index=False)

    print(f"\nSaved CSVs to {OUT_DIR}/")


def save_warnings(warnings: set):
    """Save unmapped values to warnings.log for human review."""
    if not warnings:
        print("No unmapped values.")
        return
    with open(WARNINGS_FILE, "w") as f:
        f.write(f"# Unmapped values — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("# Add these to mappings.yaml to classify them properly.\n\n")
        for w in sorted(warnings):
            f.write(f"{w}\n")
    print(f"\nWarnings: {len(warnings)} unmapped values → {WARNINGS_FILE}")


def main():
    print("=== ASTRA Data Processing ===\n")

    mappings = load_mappings()
    files = find_raw_files()
    warnings = set()
    total_agg = {}

    for f in files:
        agg = process_file(f, mappings, warnings)
        total_agg = merge_aggs(total_agg, agg)

    save_csvs(total_agg)
    save_warnings(warnings)
    print("\nDone.")


if __name__ == "__main__":
    main()
