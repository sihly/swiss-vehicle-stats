# Swiss Vehicle Registrations Dashboard — Brainstorm

**Status:** seed → growing
**Created:** 2026-03-07
**Context:** GitHub repo with auto-generated charts from ASTRA open data, targeted at Milan's Swiss automotive LinkedIn network

## Data Sources (ASTRA Open Data)

### Primary: New Registrations
- **URL:** `https://opendata.astra.admin.ch/ivzod/1000-Fahrzeuge_IVZ/1200-Neuzulassungen/1210-Datensaetze_monatlich/`
- `NEUZU.txt` — current year (rolling, updated ~1st of month), 14MB
- `1213-Vorjahresdaten/NEUZU-{YYYY}.txt` — archive back to **2016** (not 2011), 89-119MB each
- Tab-separated, 67 columns, individual vehicle-level records
- Code table: `Codetabelle_d-f-i.xlsx` (trilingual field definitions)

### Supplementary (free, no contract needed)
| Dataset | Path | Use |
|---------|------|-----|
| Fleet stock (Bestand) | `1300-Fahrzeugbestaende/1320-Datensaetze_monatlich/` | Total registered vehicles over time |
| Used imports | `1500-Gebrauchtimporte/GEBR.txt` + archive | Import trends (Tesla reimports etc.) |
| Market share by region | `1700-Analysen/1745-Marktanteile_nach_Region/` | Pre-made ASTRA analysis (Personenwagen, Motorrad, Traktor) |
| EV fleet by municipality | `1700-Analysen/1740-E-Fahrzeugbestand_nach_Gemeinde/` | Geographic EV density |
| Type approvals (TAS) | `4000-Typengenehmigungen_TAS/4100-json-Files/` | Vehicle type metadata, could help classification |

### Paid (requires contract — skip for now)
- Fleet with PLZ/location of owner (Halter) — `1400-Vertragspflichtige_Datensaetze/`
- Owner demographics (age, nationality) — `1720/1725`

## Key Fields (NEUZU.txt)

| # | Field | Use | Example Values |
|---|-------|-----|----------------|
| 3 | Fahrzeugart | Vehicle type filter | Personenwagen, Motorrad, Lieferwagen |
| 5 | Marke | Brand | TESLA, BMW, VW, TOYOTA |
| 18 | Karosserieform | Body/segment | Stationswagen, Limousine, Kasten |
| 19 | Farbe | Color | Weiss, Schwarz, Grau, Blau, Rot |
| 33 | Leistung | Power (kW) | Numeric |
| 36 | Treibstoff | Fuel type | Benzin, Diesel, Elektrisch, Benzin/Elektrisch |
| 37 | Hybridcode | Hybrid detail | N/A, or specific codes |
| 38 | CO2-WLTP | Emissions g/km | Numeric (0 for BEV) |
| 49/50 | Jahr/Monat | Registration date | 2026/01 |
| 51 | Kanton | Canton | ZH, BE, GE |
| 57 | Schildfarbe | Private/commercial | Weiss=private, Blau=commercial, Grün=agri |

**Fuel type mapping from real data:**
- Benzin = petrol (pure ICE)
- Diesel = diesel (pure ICE)
- Elektrisch = BEV
- Benzin / Elektrisch = PHEV/HEV (petrol hybrid)
- Diesel / Elektrisch = diesel hybrid
- Elektrisch mit RE = range extender (BMW i3 etc.)
- Erdgas, Flüssiggas = rare alternatives

## Design Principles

### 1. Zero-Maintenance Robustness

**Core philosophy: unknown = "Other", never missing.**

The pipeline should gracefully handle:
- New brands appearing (Chinese brands, startups)
- New fuel types
- Changed field values or codes
- Missing/malformed rows
- ASTRA changing file format slightly

**How:**
- Classification mappings stored in a single `mappings.yaml` file in the repo
- Anything not in the mapping → automatically bucketed as "Other"
- Monthly runs produce charts regardless — unknown values show up in "Other" bars/slices
- A `warnings.log` is committed each run showing what fell into "Other" and how many records
- Human reviews `warnings.log` at leisure, updates `mappings.yaml` if needed, next run picks it up

```yaml
# mappings.yaml example
segments:
  SUV: ["Stationswagen"]  # ASTRA calls SUVs "Stationswagen" too
  Sedan: ["Limousine"]
  Van: ["Kasten", "Kasten mit Hebebühne"]
  Convertible: ["Offen", "Offen mit Verdeck / Hardtop"]
  # everything else → "Other"

brands:
  premium: ["BMW", "MERCEDES-BENZ", "AUDI", "PORSCHE", "VOLVO"]
  mass_market: ["VW", "SKODA", "TOYOTA", "HYUNDAI", "KIA", "DACIA"]
  chinese_ev: ["BYD", "NIO", "XPENG", "MG", "XIAOMI", "POLESTAR"]
  tesla: ["TESLA"]
  # everything else → "Other Brands"

fuel_types:
  BEV: ["Elektrisch"]
  PHEV: ["Benzin / Elektrisch", "Diesel / Elektrisch"]
  Petrol: ["Benzin"]
  Diesel: ["Diesel"]
  # everything else → "Other"

colors:
  top_colors: ["Weiss", "Schwarz", "Grau", "Blau", "Rot", "Grün", "Braun", "Silber"]
  # everything else → "Other"
```

### 2. Correction Workflow

When a human spots misclassifications:
1. Edit `mappings.yaml` (e.g., add "ZEEKR" to `chinese_ev`)
2. Commit + push
3. Next scheduled run (or manual trigger) reprocesses all years with updated mappings
4. Charts automatically reflect the correction going forward AND retroactively

**No code changes needed.** All classification logic reads from `mappings.yaml`.

### 3. Delta Reports

Each monthly run generates a `reports/YYYY-MM.md` file with:

```markdown
# Swiss Vehicle Market — February 2026

## Month-over-Month
- Total registrations: 18,432 (+12.3% vs January)
- BEV share: 17.1% (+1.2pp vs January)
- Top gainer: TESLA Model Y (+340 units, +52%)
- Top decliner: VW ID.4 (-180 units, -28%)

## Year-over-Year (vs February 2025)
- Total registrations: -3.2%
- BEV share: 17.1% vs 14.8% (+2.3pp)
- Chinese brands: 4.2% vs 1.8% (+2.4pp)
- Diesel share: 15.9% vs 19.2% (-3.3pp)

## Notable
- First registrations of XIAOMI SU7 in Switzerland (3 units)
- DACIA Spring overtook RENAULT ZOE as cheapest BEV
```

This becomes the LinkedIn post material. Screenshot the delta + 2-3 charts, done.

## Architecture (Revised)

```
swiss-vehicle-stats/
├── README.md                    # Dashboard with inline charts + latest delta
├── mappings.yaml                # Human-editable classification rules
├── .github/workflows/
│   └── update.yml               # Monthly cron + manual dispatch
├── data/
│   └── processed/               # Committed: small aggregated CSVs
│       ├── monthly_summary.csv  # Total regs, BEV/PHEV/ICE counts per month
│       ├── monthly_brands.csv   # Top N brands per month
│       ├── monthly_fuel.csv     # Fuel type breakdown per month
│       ├── monthly_colors.csv   # Color distribution per month
│       ├── monthly_segments.csv # Body type breakdown per month
│       ├── monthly_plate.csv    # Private vs commercial per month
│       └── monthly_canton.csv   # Canton-level registrations per month
├── charts/                      # Committed: PNG charts
│   ├── 01_total_registrations.png
│   ├── 02_powertrain_trend.png
│   ├── 03_top_brands.png
│   ├── 04_tesla_tracker.png
│   ├── 05_chinese_brands.png
│   ├── 06_colors.png
│   ├── 07_private_vs_commercial.png
│   ├── 08_co2_trend.png
│   ├── 09_ev_share_by_canton.png
│   └── 10_segment_trend.png
├── reports/                     # Committed: monthly delta reports
│   ├── 2026-02.md
│   └── latest.md → symlink to newest
├── warnings.log                 # Committed: unclassified values from last run
├── scripts/
│   ├── download.py              # Fetch from ASTRA
│   ├── process.py               # Parse → aggregated CSVs (reads mappings.yaml)
│   ├── chart.py                 # Generate charts from CSVs
│   └── report.py                # Generate delta report
└── requirements.txt             # pandas, matplotlib, pyyaml, requests
```

## Key Design Questions

### Q1: How far back?
Archive goes to 2016. Pre-2019 has almost no Tesla/BEV data. 
**Recommendation:** Start at 2019 (Model 3 launch year in CH). Keeps dataset manageable, trends meaningful. Option to add 2016-2018 later if someone asks.

### Q2: Passenger cars only?
The data includes trucks, trailers, motorcycles, agricultural vehicles. Mixed charts would be confusing.
**Recommendation:** Filter to `Fahrzeugart = Personenwagen` for all charts. Maybe add one "vehicle type mix" chart for context.

### Q3: Chart language?
LinkedIn audience is Swiss professionals — mix of German/English.
**Recommendation:** English chart titles and labels, but keep German brand/color/segment names where they're clearer (e.g., "Stationswagen" is understood).

### Q4: How to handle the "segment" problem?
ASTRA's `Karosserieform` doesn't distinguish SUV from wagon well (both are "Stationswagen"). Options:
- Accept ASTRA's categories as-is (simplest)
- Use weight/height thresholds from type approval data to classify SUV vs wagon
- Manual overrides in `mappings.yaml` per model (e.g., "TESLA Model Y" = SUV)
**Recommendation:** Start with ASTRA categories. If the SUV distinction matters, add a `model_overrides` section in mappings.yaml later. Don't overengineer on day 1.

### Q5: What if ASTRA changes the file format?
Risk: column order changes, new columns added, encoding changes.
**Mitigation:** Parse by column NAME (header row), not position. If a required column is missing, the run fails loudly and creates a GitHub Issue automatically (via the Action).

### Q6: GitHub Actions compute limits?
Processing 10 years × 100MB = ~1GB of raw data. GitHub Actions runners have 7GB RAM and 14GB disk.
**Mitigation:** Process files one year at a time, aggregate immediately, don't hold all years in memory. Should be fine — pandas can handle 100MB TSVs easily.

### Q7: How to keep "5 months unattended" robust?
- `mappings.yaml` "Other" bucket catches everything unknown
- `warnings.log` accumulates what's unclassified
- Charts still render with "Other" bars
- Delta reports still generate (comparing against previous month's CSV)
- No secrets or API keys needed — ASTRA data is public
- GitHub Actions cron just works unless GitHub changes something

## Chart Designs

All charts should have:
- Consistent color palette (brand colors where possible)
- "Last updated: YYYY-MM-DD" watermark
- Source attribution: "Data: ASTRA/IVZ Open Data"
- Y-axis starting at 0 (no truncation tricks)
- Dark background option for LinkedIn screenshots

## Next Steps

1. Pick repo name
2. Build `download.py` + `process.py` (core pipeline)
3. Create initial `mappings.yaml` with current brand/fuel/segment lists
4. Build `chart.py` with 4-5 MVP charts
5. Build `report.py` for monthly deltas
6. Set up GitHub Actions
7. Bootstrap with 2019-2026 data
8. Write README
9. First LinkedIn post
