# Swiss Vehicle Registration Analytics

Automated analytics dashboard for Swiss new vehicle registrations, built from [ASTRA/IVZ Open Data](https://opendata.astra.admin.ch/ivzod/1000-Fahrzeuge_IVZ/1200-Neuzulassungen/).

A GitHub Actions pipeline downloads raw registration data monthly, aggregates it, generates charts, and produces a delta report with MoM, YoY, and YTD comparisons.

## Charts

| Chart | Description |
|-------|-------------|
| [Yearly Registrations](charts/01_yearly_registrations.png) | Total new passenger car registrations per year |
| [Powertrain Split](charts/02_powertrain_split.png) | Market share evolution: ICE vs BEV vs Hybrid |
| [Top Brands](charts/03_top_brands.png) | Top 15 brands by total registrations |
| [Manufacturer Origin](charts/04_manufacturer_origin.png) | Registrations by manufacturer country of origin |
| [Colors](charts/05_colors.png) | Vehicle color distribution |
| [Usage Type](charts/06_usage_type.png) | Private vs commercial registrations |

## How It Works

```
download.py → process.py → chart.py → report.py
```

1. **Download** — fetches NEUZU.txt (current year) and archive files (2016-2025) from ASTRA
2. **Process** — parses TSV files in chunks (memory-efficient), applies `mappings.yaml` classifications, outputs aggregated CSVs
3. **Chart** — generates matplotlib PNGs with professional styling
4. **Report** — produces a monthly delta report (MoM + YoY + YTD) in markdown

Runs automatically on the 5th of each month via GitHub Actions. Can also be triggered manually.

## Classification

All classifications are driven by `mappings.yaml`:
- Brand → country of origin (by heritage, not corporate HQ)
- Fuel type normalization (German → English)
- Color translation
- Plate color → usage type (private/commercial)

Unknown values go to an "Other" bucket and are logged to `warnings.log` for human review. Edit `mappings.yaml` to reclassify — no code changes needed.

## Local Development

```bash
pip install -r requirements.txt

python scripts/download.py    # ~1GB total download
python scripts/process.py     # ~2-5 min
python scripts/chart.py       # ~10 sec
python scripts/report.py      # instant
```

## Data

- **Source:** [ASTRA IVZ Open Data](https://opendata.astra.admin.ch/ivzod/1000-Fahrzeuge_IVZ/1200-Neuzulassungen/1210-Datensaetze_monatlich/)
- **Coverage:** 2016-present (individual vehicle records, ~300k-400k/year)
- **Scope:** Passenger cars (Personenwagen) only
- **License:** Swiss Open Government Data — free to use with attribution

Raw data files (~100MB each) are not committed to this repo. Only aggregated CSVs (~100KB) and chart PNGs are tracked.

## License

Code: [MIT](LICENSE)

Data: [ASTRA/IVZ Open Data](https://www.astra.admin.ch/) — Swiss Federal Roads Office
