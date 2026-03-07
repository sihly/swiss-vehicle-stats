# Changes to implement (PR review + data investigation)

## Critical bugs to fix
1. **Wrong column names**: Use `Farbe` not `Farbe_1`, `Antrieb` not `Antriebsart`, `Erstinverkehrsetzung_Jahr`/`Erstinverkehrsetzung_Monat` for date (NOT `Neuzulassungen_von`/`Neuzulassungen_bis`)
2. **Fuel mapping wrong**: Data has spaces around `/` — e.g. `Benzin / Elektrisch` not `Benzin/Elektrisch`. Also add: `Elektrisch mit RE` and `Elektrisch mit RE (Range Extender)` → BEV, `Erdgas (CNG) / Benzin` and `Erdgas / Benzin (CNG)` → CNG, `Flüssiggas (LPG) / Benzin` → LPG, `Wasserstoff / Elektrisch` → Hydrogen, `Benzin / Alkohol (Ethanol)` → Petrol
3. **All columns exist in ALL files** (2016-2026) — just at different positions. Column matching by name already handles this.

## Architecture changes
1. **Remove chunked processing** — not needed for ~300k rows/file with dtype optimization. Load one file at a time, full read with `usecols` + category dtypes. Simpler code.
2. **SVG instead of PNG** — git-diffable, smaller, GitHub renders in markdown. Use `.svg` extension.
3. **UV instead of pip** — replace `requirements.txt` with `pyproject.toml`. Add `uv.lock`. GitHub Actions uses `astral-sh/setup-uv`.
4. **Dynamic attribution** — read repo URL from `git config --get remote.origin.url` (local) or `GITHUB_REPOSITORY` env var (CI). Embed repo URL + date on every chart.

## Chart changes
1. **Chart 1 (yearly registrations)**: Show all years 2016-present (was only showing 2023+ due to wrong date column — now fixed)
2. **NEW Chart: Winners/Losers**: Diverging horizontal bar chart. Top 5 brands that gained most + top 5 that lost most in absolute registrations vs prior year. One chart per year, or a combined view showing latest year.
3. **Chart 2 (powertrain)**: Change from percentage stacked area to absolute stacked bar (annual). Height = total registrations, segments = powertrain types. Annual resolution, not monthly.
4. **Chart 5 (colors)**: Now works — column is `Farbe` not `Farbe_1`
5. **4x4 chart**: Column is `Antrieb` with values `Allrad`, `Vorderrad`, `Hinterrad`. Can add AWD share chart.

## Mapping changes
1. **Fix all fuel type keys** to match actual data (spaces around `/`)
2. **Add brand_group mapping** (corporate parent): VW Group, Stellantis, Hyundai Motor Group, etc.
3. **Keep brand_origin mapping** (country of heritage) — both dimensions
4. **Add color mapping for military colors**: `Feldgrau (Nur für Militärfahrzeuge)` → Grey, `Fleckentarnung ( Nur für Militärfahrzeuge)` → Camouflage, `Bunt` → Multicolor

## Other
1. **LICENSE**: Keep MIT for code. Add DATA section to README about ASTRA OGD terms. Don't mix in LICENSE file.
2. **README**: Add "Data Attribution" section, disclaimer for informational purposes only
3. **pyproject.toml**: Replace requirements.txt
4. **Intermediate CSVs**: Keep, commit (tiny ~100KB). Useful for charts + reports + debugging.

## Column reference (verified from actual data)
- `Fahrzeugart` — vehicle type (filter to "Personenwagen")
- `Marke` — brand
- `Treibstoff` — fuel type
- `Farbe` — color (column 15 in older files, 19 in newer)
- `Schildfarbe` — plate color (private/commercial)
- `Antrieb` — drive type (Allrad/Vorderrad/Hinterrad)
- `Erstinverkehrsetzung_Jahr` — registration year
- `Erstinverkehrsetzung_Monat` — registration month
- `Kanton` — canton (available in all files)

When completely finished building all changes, run: openclaw system event --text "Done: Rebuilt swiss-vehicle-stats with all PR review fixes" --mode now
