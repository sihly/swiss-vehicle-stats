#!/usr/bin/env python3
"""Generate analytics charts from processed ASTRA data.

PNG output, professional style, dynamic attribution.
"""

import os
import subprocess
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data" / "processed"
CHART_DIR = ROOT / "charts"

DPI = 150
FIGSIZE = (12, 7)

# Professional color palette
COLORS = [
    "#2563eb", "#dc2626", "#16a34a", "#f59e0b", "#8b5cf6",
    "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#84cc16",
    "#06b6d4", "#e11d48", "#a855f7", "#22c55e", "#eab308",
]


def get_repo_url() -> str:
    """Get repo URL from environment or git remote."""
    repo = os.environ.get("GITHUB_REPOSITORY")
    if repo:
        return f"https://github.com/{repo}"
    try:
        url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
        if url.startswith("git@"):
            url = url.replace(":", "/").replace("git@", "https://")
        return url.removesuffix(".git")
    except Exception:
        return ""


def get_attribution() -> str:
    from datetime import date
    repo = get_repo_url()
    parts = [f"Data: ASTRA/IVZ Open Data | Generated {date.today()}"]
    if repo:
        parts.append(repo)
    return " | ".join(parts)


def style_chart(ax, title: str, xlabel: str = "", ylabel: str = ""):
    ax.set_title(title, fontsize=16, fontweight="bold", pad=15)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=12)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=10)
    ax.grid(axis="y", alpha=0.3, linestyle="--")


def add_attribution(fig):
    fig.text(0.99, 0.01, get_attribution(), ha="right", va="bottom",
             fontsize=7, color="#999999", style="italic")


def save_chart(fig, name: str):
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    path = CHART_DIR / f"{name}.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    size_kb = path.stat().st_size / 1024
    print(f"  Saved: {name}.png ({size_kb:.0f} KB)")


def chart_yearly_registrations():
    """Total registrations as line chart with trend."""
    df = pd.read_csv(DATA_DIR / "monthly_totals.csv")
    yearly = df.groupby("year")["count"].sum().reset_index()
    yearly = yearly[yearly["year"] >= 2016]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.plot(yearly["year"], yearly["count"], marker="o", linewidth=2.5,
            color=COLORS[0], markersize=8, zorder=3)
    ax.fill_between(yearly["year"], yearly["count"], alpha=0.1, color=COLORS[0])

    for _, row in yearly.iterrows():
        ax.annotate(f"{row['count']:,.0f}", (row["year"], row["count"]),
                    textcoords="offset points", xytext=(0, 12),
                    ha="center", fontsize=8, fontweight="bold")

    style_chart(ax, "New Passenger Car Registrations in Switzerland", ylabel="Registrations")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.set_xlim(yearly["year"].min() - 0.5, yearly["year"].max() + 0.5)
    add_attribution(fig)
    save_chart(fig, "01_yearly_registrations")


def chart_powertrain_absolute():
    """Powertrain mix as absolute stacked bar (annual)."""
    df = pd.read_csv(DATA_DIR / "fuel_by_month.csv")
    yearly = df.groupby(["year", "fuel_type"])["count"].sum().reset_index()
    yearly = yearly[yearly["year"] >= 2016]

    order = ["Petrol", "Diesel", "BEV", "PHEV", "Diesel Hybrid", "Hydrogen", "CNG", "LPG", "Other"]
    color_map = {
        "Petrol": "#6b7280", "Diesel": "#374151", "BEV": "#2563eb",
        "PHEV": "#60a5fa", "Diesel Hybrid": "#93c5fd", "Hydrogen": "#16a34a",
        "CNG": "#f59e0b", "LPG": "#f97316", "Other": "#d1d5db",
    }

    pivot = yearly.pivot(index="year", columns="fuel_type", values="count").fillna(0)
    cols = [c for c in order if c in pivot.columns]
    pivot = pivot[cols]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    bottom = pd.Series(0, index=pivot.index)
    for col in cols:
        ax.bar(pivot.index.astype(str), pivot[col], bottom=bottom,
               label=col, color=color_map.get(col, "#999"), width=0.7)
        bottom = bottom + pivot[col]

    style_chart(ax, "New Registrations by Powertrain", ylabel="Registrations")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.legend(loc="upper right", fontsize=9, frameon=False)
    add_attribution(fig)
    save_chart(fig, "02_powertrain_absolute")


def chart_brand_rankings():
    """Brand ranking bump chart — position over time for top brands."""
    path = DATA_DIR / "brand_by_year.csv"
    if not path.exists():
        print("  Skip: brand rankings (no data)")
        return

    df = pd.read_csv(path)
    df = df[df["year"] >= 2016]

    # Get top 10 brands by total volume across all years
    top_brands = df.groupby("brand")["count"].sum().nlargest(10).index.tolist()

    # Calculate rank per year
    ranked = df[df["brand"].isin(top_brands)].copy()
    ranked["rank"] = ranked.groupby("year")["count"].rank(ascending=False, method="min")

    fig, ax = plt.subplots(figsize=(14, 8))

    for i, brand in enumerate(top_brands):
        brand_data = ranked[ranked["brand"] == brand].sort_values("year")
        color = COLORS[i % len(COLORS)]
        ax.plot(brand_data["year"], brand_data["rank"], marker="o", linewidth=2.5,
                label=brand, color=color, markersize=7, zorder=3)
        # Label last point
        if not brand_data.empty:
            last = brand_data.iloc[-1]
            ax.annotate(brand, (last["year"], last["rank"]),
                        textcoords="offset points", xytext=(8, 0),
                        fontsize=9, fontweight="bold", color=color, va="center")

    ax.invert_yaxis()
    ax.set_yticks(range(1, 11))
    ax.set_yticklabels([f"#{i}" for i in range(1, 11)])
    style_chart(ax, "Top 10 Brand Rankings Over Time", ylabel="Position")
    ax.set_xlabel("")
    ax.legend(loc="lower left", fontsize=8, frameon=False, ncol=2)
    ax.grid(axis="x", alpha=0.3, linestyle="--")
    add_attribution(fig)
    save_chart(fig, "03_brand_rankings")


def chart_origin_over_time():
    """Manufacturer origin share over time (stacked area)."""
    path = DATA_DIR / "brand_by_year.csv"
    if not path.exists():
        print("  Skip: origin over time (no data)")
        return

    # Need to map brands to origins using mappings
    import yaml
    with open(ROOT / "mappings.yaml") as f:
        mappings = yaml.safe_load(f)

    brand_origin = mappings.get("brand_origin", {})
    country_continent = mappings.get("country_continent", {})

    df = pd.read_csv(path)
    df = df[df["year"] >= 2016]

    # Map brand to country
    def get_origin(brand):
        b = str(brand).strip().upper()
        for key, val in brand_origin.items():
            if str(key).upper() == b:
                return val
        return "Other"

    df["country"] = df["brand"].apply(get_origin)

    # Aggregate by year + country
    by_country = df.groupby(["year", "country"])["count"].sum().reset_index()

    # Get top countries by total volume
    top_countries = by_country.groupby("country")["count"].sum().nlargest(8).index.tolist()
    by_country.loc[~by_country["country"].isin(top_countries), "country"] = "Other"
    by_country = by_country.groupby(["year", "country"])["count"].sum().reset_index()

    # Calculate share
    totals = by_country.groupby("year")["count"].sum()
    pivot = by_country.pivot(index="year", columns="country", values="count").fillna(0)
    pct = pivot.div(totals, axis=0) * 100

    # Order by average share
    order = pct.mean().sort_values(ascending=False).index.tolist()
    pct = pct[order]

    country_colors = {
        "Germany": "#1a1a1a", "Japan": "#dc2626", "France": "#2563eb",
        "South Korea": "#16a34a", "USA": "#f59e0b", "UK": "#8b5cf6",
        "Czech Republic": "#ec4899", "Italy": "#f97316", "China": "#e11d48",
        "Romania": "#14b8a6", "Sweden": "#6366f1", "Spain": "#84cc16",
        "India": "#06b6d4", "Other": "#d1d5db",
    }

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.stackplot(pct.index, *[pct[c] for c in pct.columns],
                 labels=pct.columns,
                 colors=[country_colors.get(c, "#999") for c in pct.columns],
                 alpha=0.85)

    style_chart(ax, "Market Share by Manufacturer Origin", ylabel="Share (%)")
    ax.set_ylim(0, 100)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=9, frameon=False)
    ax.set_xlabel("")
    add_attribution(fig)
    save_chart(fig, "04_origin_over_time")


def chart_colors_over_time():
    """Color distribution over time (stacked area)."""
    # Need to process from brand_by_year equivalent but for colors
    # We have color_totals but not color_by_year — check if we have the monthly data
    # Actually we need to re-derive this. For now use what we have.
    # Let's check if we can build from the processed data
    path = DATA_DIR / "color_totals.csv"
    if not path.exists():
        print("  Skip: colors (no data)")
        return

    # We only have totals, not by year. Show as horizontal bar for now,
    # and add a TODO for color_by_year in process.py
    df = pd.read_csv(path)
    df = df[df["color"] != "Other"]
    total = df["count"].sum()
    df["pct"] = df["count"] / total * 100

    color_map = {
        "Grey": "#808080", "White": "#d4d4d4", "Black": "#1a1a1a",
        "Blue": "#2563eb", "Red": "#dc2626", "Green": "#16a34a",
        "Yellow": "#eab308", "Orange": "#f97316", "Brown": "#8B4513",
        "Silver": "#c0c0c0", "Beige": "#d4a574", "Purple": "#8b5cf6",
        "Multicolor": "#ff69b4", "Gold": "#daa520",
    }

    fig, ax = plt.subplots(figsize=FIGSIZE)
    bars = ax.barh(df["color"][::-1], df["pct"][::-1],
                   color=[color_map.get(c, "#999") for c in df["color"][::-1]],
                   height=0.7, edgecolor="white", linewidth=0.5)

    for bar, val in zip(bars, df["pct"][::-1]):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", ha="left", va="center", fontsize=9)

    style_chart(ax, "Vehicle Color Distribution (2016-present)", xlabel="Share (%)")
    add_attribution(fig)
    save_chart(fig, "05_colors")


def chart_drive_type():
    """AWD vs FWD vs RWD share over time."""
    path = DATA_DIR / "drive_by_month.csv"
    if not path.exists():
        print("  Skip: drive type (no data)")
        return

    df = pd.read_csv(path)
    yearly = df.groupby(["year", "drive"])["count"].sum().reset_index()
    yearly = yearly[yearly["year"] >= 2016]

    pivot = yearly.pivot(index="year", columns="drive", values="count").fillna(0)
    pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    drive_colors = {"AWD": "#2563eb", "FWD": "#f59e0b", "RWD": "#dc2626", "Other": "#d1d5db"}
    order = [c for c in ["AWD", "FWD", "RWD", "Other"] if c in pct.columns]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.stackplot(pct.index, *[pct[c] for c in order],
                 labels=order,
                 colors=[drive_colors.get(c, "#999") for c in order],
                 alpha=0.85)

    style_chart(ax, "Drive Type Share Over Time", ylabel="Share (%)")
    ax.set_ylim(0, 100)
    ax.legend(loc="upper right", fontsize=10, frameon=False)
    ax.set_xlabel("")
    add_attribution(fig)
    save_chart(fig, "06_drive_type")


def chart_canton_heatmap():
    """[Experimental] Geographic heatmap of registrations by canton.

    Currently hardcoded to Mercedes-Benz, last 3 months of available data.
    Requires geopandas and data/ch-cantons.geojson.
    """
    geojson_path = ROOT / "data" / "ch-cantons.geojson"
    if not geojson_path.exists():
        print("  Skip: canton heatmap (no ch-cantons.geojson)")
        return

    try:
        import geopandas as gpd
        import matplotlib.colors as mcolors
    except ImportError:
        print("  Skip: canton heatmap (geopandas not installed)")
        return

    # Find the two most recent raw files to cover ~3 months
    raw_dir = ROOT / "data" / "raw"
    if not raw_dir.exists():
        print("  Skip: canton heatmap (no raw data)")
        return

    raw_files = sorted(raw_dir.glob("NEUZU*.txt"))
    if not raw_files:
        print("  Skip: canton heatmap (no raw files)")
        return

    # Load last 2 files (current year + previous year archive)
    cols = ["Fahrzeugart", "Marke", "Erstinverkehrsetzung_Kanton",
            "Erstinverkehrsetzung_Jahr", "Erstinverkehrsetzung_Monat"]
    dfs = []
    for f in raw_files[-2:]:
        available = []
        with open(f, "r", encoding="utf-8", errors="replace") as fh:
            header = [c.strip() for c in fh.readline().split("\t")]
        available = [c for c in cols if c in header]
        if len(available) < len(cols):
            continue
        df = pd.read_csv(f, sep="\t", usecols=available, dtype=str)
        dfs.append(df)

    if not dfs:
        print("  Skip: canton heatmap (could not read raw files)")
        return

    df = pd.concat(dfs, ignore_index=True)
    df = df[df["Fahrzeugart"].str.contains("Personenwagen", case=False, na=False)]
    df = df[df["Marke"].str.contains("MERCEDES", case=False, na=False)]
    df["year"] = pd.to_numeric(df["Erstinverkehrsetzung_Jahr"], errors="coerce")
    df["month"] = pd.to_numeric(df["Erstinverkehrsetzung_Monat"], errors="coerce")

    # Find last 3 months in data
    df["ym"] = df["year"] * 100 + df["month"]
    last_3 = sorted(df["ym"].dropna().unique())[-3:]
    recent = df[df["ym"].isin(last_3)]

    if recent.empty:
        print("  Skip: canton heatmap (no recent data)")
        return

    # Determine date range for title
    months = sorted(recent[["year", "month"]].drop_duplicates().values.tolist())
    month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                   7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    date_range = f"{month_names.get(int(months[0][1]))} {int(months[0][0])} - {month_names.get(int(months[-1][1]))} {int(months[-1][0])}"

    # Count by canton
    by_canton = recent.groupby("Erstinverkehrsetzung_Kanton").size().reset_index(name="count")
    by_canton.columns = ["canton", "count"]

    # Load geodata and merge
    cantons = gpd.read_file(geojson_path)
    merged = cantons.merge(by_canton, left_on="id", right_on="canton", how="left")
    merged["count"] = merged["count"].fillna(0)

    # Plot
    fig, ax = plt.subplots(figsize=(14, 10))
    vmax = merged["count"].max()
    norm = mcolors.Normalize(vmin=0, vmax=vmax)
    cmap = plt.cm.YlOrRd

    merged.plot(column="count", ax=ax, cmap=cmap, edgecolor="white",
                linewidth=1.2, legend=False, norm=norm)

    for _, row in merged.iterrows():
        centroid = row.geometry.centroid
        label = f"{row['id']}\n{int(row['count'])}"
        ax.annotate(label, (centroid.x, centroid.y), ha="center", va="center",
                    fontsize=8, fontweight="bold",
                    color="white" if row["count"] > vmax * 0.5 else "black")

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label("New Registrations", fontsize=11)

    ax.set_title(f"Mercedes-Benz New Registrations by Canton\n{date_range}",
                 fontsize=16, fontweight="bold", pad=15)
    ax.set_axis_off()
    add_attribution(fig)
    save_chart(fig, "07_mercedes_canton_heatmap")


def main():
    print("=== Generating Charts ===\n")

    if not (DATA_DIR / "monthly_totals.csv").exists():
        print("ERROR: No processed data. Run process.py first.")
        return

    chart_yearly_registrations()
    chart_powertrain_absolute()
    chart_brand_rankings()
    chart_origin_over_time()
    chart_colors_over_time()
    chart_drive_type()
    chart_canton_heatmap()

    print("\nDone.")


if __name__ == "__main__":
    main()
