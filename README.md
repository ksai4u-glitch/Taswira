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

The area, dates, dataset version and request limits are all in `settings.py`
(currently `AREA = "africa"`, all 54 African countries, 2020 to 2025 from the stable GED 26.1,
plus 2026 so far from the preliminary GED Candidate releases in `CANDIDATE_VERSIONS`).
Set `AREA = "nigeria"` to go back to Nigeria only. Change them there and every script follows.

Candidate events are marked `preliminary` in the clean table and shown hatched or dashed
on the map, because UCDP may still revise them. When UCDP publishes a new monthly
Candidate release, add its version to `CANDIDATE_VERSIONS` and run `save_events.py`
again: only the new version is downloaded.

1. Copy `.env.example` to `.env` and paste your UCDP token after `UCDP_TOKEN=`.
   `.env` is listed in `.gitignore` and must never be committed.
2. Run the Stage 1 script (Python 3, no extra packages needed):

   ```
   python3 fetch_nigeria.py
   ```
3. Run the Stage 2 script to fetch every page (`PAGE_SIZE` events per request, one country at a time; it stops
   early if the download would need more than `MAX_REQUESTS`):

   ```
   python3 fetch_all.py
   ```
4. Run the Stage 3 script to save every event (stable and Candidate) to `data/taswira.db` (SQLite).
   It only calls the API for versions it hasn't saved yet; add `--refresh` to download everything again:

   ```
   python3 save_events.py
   ```
5. Run the Stage 4 script to build a clean, map-ready table (`clean_events`) and
   `data/<area>_<years>_clean.csv`. It reads the database only, with no API requests:

   ```
   python3 clean_events.py
   ```
6. Run the Stage 5 script to build the interactive map `data/<area>_<years>_map.html`
   (heatmap, individual events, a per-year chart, a per-month chart, a month-by-month animation (Play, with a draggable timeline, trail mode, a moving heatmap, and blast or gunfire bursts as events appear), deaths by state for the picked country, a filter by armed group, hotspot zones worked out from the last 12 months, and a dark "ops" look with a Light button). It opens in your browser automatically:

   ```
   python3 build_map.py
   ```

7. Run the Stage 7 script to build the public page `docs/index.html`. It checks that
   your token is not in the page, that UCDP and the dataset version are credited, and that
   preliminary data is labelled, before writing anything:

   ```
   python3 publish.py
   ```

   Then commit and push `docs/index.html`. With GitHub Pages set to serve the `docs/`
   folder of `main` (repo Settings → Pages → Deploy from a branch → `main` / `/docs`),
   the map appears at `https://ksai4u-glitch.github.io/Taswira/`.
   Re-run `publish.py` and push again whenever you add a new Candidate release.

## Automatic updates

A GitHub Actions workflow (`.github/workflows/update.yml`) runs every Monday. It costs
1 API request to check whether UCDP has published the next monthly Candidate release
(`update_candidates.py`). If it has, the workflow adds it to `settings.py`, downloads it,
rebuilds `docs/index.html` and opens a pull request ("Add GED Candidate …") with both.
Nothing goes live until you merge it; merging republishes the map. While one data pull
request is open, later runs wait for it instead of opening another.

It needs your token as a repository secret: Settings → Secrets and variables → Actions →
New repository secret, name `UCDP_TOKEN`, and Settings → Actions → General → "Allow GitHub
Actions to create and approve pull requests". You can also start it any time from the
Actions tab → "Update map with new UCDP releases" → Run workflow.

The yearly stable release (for example 27.1) still needs a manual change of
`API_VERSION` and the dates in `settings.py`.

## History page (draft)

`python build_history.py` builds `docs/history.html`, an animated map of chapters of African and
Nigerian history. The chapters so far, in order:

- Deep time: how the land was made
- Africa: peoples, cities and kingdoms (including Great Zimbabwe)
- Nok: farmers, sculptors and early iron
- Hausa cities: walls, markets and kings (Kano, about 1000 to 1526)
- From four regions to 36 states (1967 to 1996)
- Map key: how power and movement are drawn

It reads only the files in `history/`, makes no API requests and is separate from `publish.py`.
See [`history/README.md`](history/README.md) for how chapters and sources are written.

Tests: `python -m unittest discover -s tests` (Python), and the browser tests in `tests/*.cjs`
(Node with Playwright), for example `node tests/history_browser.cjs`.

## Agent tasks (Claude + Codex)

A comment such as `/agent review` plus a brief on an issue starts a task that
Claude drafts and Codex reviews, for up to three rounds, ending in a final
report on the issue. Agents work only on `agent/…` branches and never merge,
push to `main` or deploy. Setup, limits and the stop command (`/agent stop`) are
in [`.github/agents/SETUP.md`](.github/agents/SETUP.md); the rules both agents
follow are in [`.github/agents/INSTRUCTIONS.md`](.github/agents/INSTRUCTIONS.md).

## Build stages

1. **Fetch:** one authenticated request for Nigeria events, inspect the JSON fields
2. **Paginate:** loop through all pages safely, respecting the daily limit
3. **Store:** save events locally (CSV/SQLite) so the API is not hit repeatedly
4. **Clean:** select key fields (date, location, deaths estimate, violence type, actors)
5. **Map:** plot events and build a heatmap for Nigeria
6. **Expand:** extend to wider Africa, add time filtering and Candidate data (done)
7. **Publish:** public version with full UCDP attribution, updated weekly (done)
8. **History:** animated chapters of African and Nigerian history (`docs/history.html`) ← *current*
