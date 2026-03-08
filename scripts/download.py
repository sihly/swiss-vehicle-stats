#!/usr/bin/env python3
"""Download ASTRA vehicle registration data (NEUZU) files."""

import os
import sys
import requests
from pathlib import Path

BASE_URL = "https://opendata.astra.admin.ch/ivzod/1000-Fahrzeuge_IVZ/1200-Neuzulassungen/1210-Datensaetze_monatlich"
CURRENT_URL = f"{BASE_URL}/NEUZU.txt"
ARCHIVE_URL = f"{BASE_URL}/1213-Vorjahresdaten/NEUZU-{{year}}.txt"

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

# Available archive years on the ASTRA server
ARCHIVE_YEARS = range(2016, 2026)


def download_file(url: str, dest: Path, force: bool = False) -> bool:
    """Download a file if it doesn't already exist."""
    if dest.exists() and not force:
        print(f"  Skip (exists): {dest.name}")
        return True

    print(f"  Downloading: {url}")
    try:
        resp = requests.get(url, stream=True, timeout=120)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  ERROR: {e}")
        return False

    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)

    size_mb = dest.stat().st_size / (1024 * 1024)
    print(f"  Saved: {dest.name} ({size_mb:.1f} MB)")
    return True


def main():
    force = "--force" in sys.argv
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print("=== ASTRA NEUZU Data Download ===\n")

    # Download current year
    print("Current year (NEUZU.txt):")
    download_file(CURRENT_URL, RAW_DIR / "NEUZU.txt", force=True)  # Always refresh current

    # Download archives
    print("\nArchive years:")
    for year in ARCHIVE_YEARS:
        url = ARCHIVE_URL.format(year=year)
        dest = RAW_DIR / f"NEUZU-{year}.txt"
        download_file(url, dest, force=force)

    print("\nDone.")


if __name__ == "__main__":
    main()
