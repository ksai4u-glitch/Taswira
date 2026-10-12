# Taswira: Africa Conflict Tracker

*Taswira* is the Hausa word for "map".

A personal, non-commercial, educational project that maps organised violence across Africa, with a particular focus on Nigeria. The goal is a clear visual overview of where conflict events happen and how patterns change over time.

## Data source

- **UCDP Georeferenced Event Dataset (GED)**, Uppsala Conflict Data Program, Uppsala University.
- API: `https://ucdpapi.pcr.uu.se/api/gedevents/<version>`
- Docs: https://ucdp.uu.se/apidocs/
- Access token sent as the HTTP header `x-ucdp-access-token`.
- Limit: 5,000 requests per day. Every paginated request counts, including errors. Resets at midnight UTC.
- Versions: `26.1` = stable yearly GED release; `26.0.x` = monthly GED Candidate releases (preliminary data).
- Nigeria filter: `Country=475` (Gleditsch-Ward code). Date filters: `StartDate`, `EndDate` (YYYY-MM-DD).

Any public version of this project will credit UCDP as the data source, cite the dataset version used, and clearly label Candidate events as preliminary.

## Setup

1. Copy `.env.example` to `.env` and paste your UCDP token after `UCDP_TOKEN=`.
   `.env` is listed in `.gitignore` and must never be committed.
2. Run the Stage 1 script (Python 3, no extra packages needed):

   ```
   python3 fetch_nigeria.py
   ```
3. Run the Stage 2 script to fetch every page (about 6 requests for Nigeria 2024):

   ```
   python3 fetch_all_nigeria.py
   ```

## Planned build stages

1. **Fetch:** one authenticated request for Nigeria events, inspect the JSON fields
2. **Paginate:** loop through all pages safely, respecting the daily limit ← *current*
3. **Store:** save events locally (CSV/SQLite) so the API is not hit repeatedly
4. **Clean:** select key fields (date, location, deaths estimate, violence type, actors)
5. **Map:** plot events and build a heatmap for Nigeria
6. **Expand:** extend to wider Africa, add time filtering and Candidate data
7. **Publish:** public version with full UCDP attribution
