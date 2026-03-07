# Build Task

Read SPEC.md and RESEARCH.md for full context. Build the complete MVP:

## What to build

1. `mappings.yaml` — brand-to-country, fuel type normalization, color mapping, plate color (private/commercial)
2. `scripts/download.py` — fetch NEUZU.txt (current year) + all archive years from ASTRA. Save to data/raw/ (gitignored)
3. `scripts/process.py` — parse TSV files using chunked pandas (chunksize=100000, category dtypes, usecols). Apply mappings.yaml. Output aggregated CSVs to data/processed/
4. `scripts/chart.py` — generate 6 matplotlib PNG charts to charts/: total registrations, powertrain split, top brands, manufacturer origin by country, colors, private vs commercial. Professional style, dark background option, "Data: ASTRA/IVZ Open Data" watermark.
5. `scripts/report.py` — generate monthly delta report (MoM + YoY + YTD) to reports/YYYY-MM.md
6. `.github/workflows/update.yml` — monthly cron (5th of month, 8am UTC) + workflow_dispatch. Download, process, chart, report, git commit+push.
7. `README.md` — dashboard with inline chart images, explanation, attribution, MIT license badge
8. `.gitignore` — ignore data/raw/
9. `requirements.txt` — pandas, matplotlib, pyyaml, requests
10. `LICENSE` — MIT

## Key constraints
- Raw files are 100MB+ TSV, must use chunked processing (7GB RAM limit on GitHub Actions)
- Parse by column NAME not position (header row)
- Unknown values → "Other" bucket, never crash
- Filter to Fahrzeugart containing "Personenwagen" for all charts
- Charts: 150 DPI, clean professional style, ~150KB each
- Attribution: "Data: ASTRA/IVZ Open Data" on every chart

## Data source
- Current year: https://opendata.astra.admin.ch/ivzod/1000-Fahrzeuge_IVZ/1200-Neuzulassungen/1210-Datensaetze_monatlich/NEUZU.txt
- Archives: https://opendata.astra.admin.ch/ivzod/1000-Fahrzeuge_IVZ/1200-Neuzulassungen/1210-Datensaetze_monatlich/1213-Vorjahresdaten/NEUZU-{YYYY}.txt (2016-2025)

Delete SPEC.md, RESEARCH.md and TASK.md when done building.

When completely finished, run: openclaw system event --text "Done: Built swiss-vehicle-stats MVP" --mode now
