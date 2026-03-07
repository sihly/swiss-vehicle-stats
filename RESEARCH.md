# Swiss Vehicle Stats — Gemini Deep Research Validation

**URL:** https://gemini.google.com/app/794a00b7c5d598e9
**Date:** March 7, 2026

## 1. Licensing — CONFIRMED: Freely republishable

- ASTRA data falls under Swiss OGD "Open Data by Default" (since 2020)
- Aligned with CC-BY 3.0/4.0 and ODC-By 1.0
- **Commercial use: permitted.** Derivative works: allowed. Redistribution: allowed.
- **Attribution required:** Source must be cited (ASTRA/IVZ)
- **Key distinction:** Free datasets (NEUZU, BEST) are fine. Fee-based datasets (NEUZU_R with PLZ/holder data) require framework agreement — we don't need those
- **Repo license:** MIT for code is appropriate. Data outputs carry OGD attribution requirement.
- Must not link data across periods to build individual vehicle histories (privacy rule)

## 2. Similar Projects — Few exist

- No major GitHub repo doing Swiss vehicle registration analytics found
- Some comparable international projects exist (German KBA analysis, UK DVLA)
- Kaggle has "Car Brand Classification Dataset" useful for brand-origin mapping
- Tom MacWright's Observable notebook "Car companies" has brand-to-group mapping
- Gap in the market = opportunity for LinkedIn positioning

## 3. GitHub Actions Limits — Feasible with optimization

- Free tier: 2 vCPU, **7GB RAM**, 14GB disk
- 100MB+ TSV files will OOM if loaded fully into pandas
- **Must use chunked processing:** `pd.read_csv(chunksize=100000)` with `usecols` and dtype optimization
- Use `category` dtype for string columns (Marke, Treibstoff, Kanton) — massive memory savings
- Files >100MB cannot be committed to git — use .gitignore for raw data (already planned)
- GitHub Actions free tier: 2,000 minutes/month for private repos, unlimited for public

## 4. Brand-to-Country Mapping

- Kaggle "Car Brand Classification Dataset" provides brand → origin mapping
- Tom MacWright Observable notebook has brand → parent group mapping
- Teoalida.com has comprehensive European car database
- **Stellantis problem:** Industry standard is to map by brand heritage, not corporate HQ
  - Peugeot → French, Fiat → Italian, Jeep → American, even though all owned by Stellantis (Dutch-registered)
  - VW Group: VW → German, SEAT → Spanish, Skoda → Czech
- Our `mappings.yaml` approach is correct — map by brand heritage

## 5. Data Quality Issues

- **Registration lag:** End-of-month/quarter surge not fully reflected until next reporting cycle
- Weekly reports (NEUZU_W) differ from monthly (NEUZU) — monthly is authoritative
- Pre-2019 datasets have fewer columns (no CO2-WLTP, no Hybridcode, no El-Verbrauch)
- 2022+ introduced eCOC system: vehicles get "IVI" instead of type approval number
- Master numbers contain check digits — can validate data integrity

## 6. Repo Size Management — Validated approaches

- **Orphan branch for artifacts:** Store charts in `gh-pages` or `data-artifacts` branch, keeps main branch clean
- **GitHub Releases:** Bundle charts as release assets instead of committing to tree
- **Our approach (overwrite PNGs in place) is acceptable** for first 2-3 years (~24MB/year)
- `git gc` helps compress history
- SVG is git-diffable but renders poorly on LinkedIn (PNG preferred for social media screenshots)

## 7. Maintenance Minimization

- Use header-based column matching (not positional) — already planned
- CSV Blueprint or csv-detective tools can lint data before processing
- Fuzzy string matching for column name drift (e.g., if ASTRA renames "Marke" to "Brand")
- **Key insight from report:** Implement a "metadata contract" — expected columns with aliases, validated at pipeline start. Fail loudly with GitHub Issue creation on mismatch.

## 8. MVP Charts — What Swiss automotive pros want to see

- **Drive type market share** is #1 priority (ICE→BEV transition is THE industry topic)
- **4x4 prevalence** is uniquely Swiss (high demand due to Alps/weather)
- **Direct import share** tracks vehicles entering outside general importers (pricing indicator)
- **Weight class for LCVs** relevant for logistics stakeholders
- YoY percentage deviation call-outs are "signature elements" of professional market reports
- Bar charts for monthly comparisons, line charts for long-term trends
- auto-schweiz annual report is the benchmark for style/content

## 9. Future Data Enrichment

- **ACEA:** EU-wide registration data for cross-border comparison
- **BFS (Federal Statistical Office):** Fuel price indices, economic indicators
- **SFOE (Federal Office of Energy):** Charging infrastructure locations
- **2025+ regulatory change:** Automated Driving Systems (ADS) will get new registration categories — new data attributes coming
- CO2 levy correlation with registration trends
- Fleet replacement cycle modeling from BEST stock data

## 10. Delta Report Format

- Must include: MoM, YoY, and **YTD** deltas (we missed YTD — add it)
- "Plug-in Share" (BEV + PHEV combined) is a key tracked metric
- Use templated narrative generation ("surpassed", "stabilized", "contracted")
- auto-schweiz format is the gold standard for Swiss audience

## Additional Insights from Research

- **BEST dataset** (vehicle stock/fleet) would complement NEUZU (new registrations) — shows total fleet composition over time, not just new sales
- **AHOI dataset** (status changes) could show used car market trends
- **STNR dataset** (master numbers, daily) has detailed CO2/technical specs
- For 2025+: new vehicle types (ADS vehicles) will appear in data

## Validated Architecture Decisions

1. mappings.yaml for classification — correct approach
2. Chunked pandas processing — mandatory for 7GB RAM limit  
3. PNG over SVG — right for LinkedIn audience
4. Raw data gitignored — correct, required by GitHub 100MB file limit
5. Monthly cron schedule — aligns with ASTRA release cycle
6. MIT license for code — appropriate
7. Add "Data: ASTRA/IVZ Open Data" attribution — legally required
