# Design handover: home page and history experience (27 Nov 2026)

This folder is a design handover, not part of the site. Nothing here is built into `docs/`, and no
research, historical qualification, chapter file or production asset was changed.

- **Base:** `main` at `87c4058` (merge of PR #86). Branch: `claude/project-thread-wybc5s`.
- **For:** Saifu (review and approval), Codex and Claude (implementation).
- **Earlier assessment:** the launch-readiness review of 27 Nov (findings B1 to B6, R1 to R5) is the
  reason for this pass. Its two first-pass wireframes are in `wireframes-2026-11-27/`.

## What is in this folder

| Path | What it is | How to change it |
|---|---|---|
| `kano-journey/kano-journey.html` | Editable mock-ups: five steps of one Kano visit, desktop 1440×900 and phone 390×844, real content | Edit the HTML, then re-export |
| `kano-journey/screens/d1…d5.png`, `p1…p5.png` | Exports of the ten frames (d = desktop, p = phone) | `node design/kano-journey/capture.cjs` with `python -m http.server 8765` running in the repo root |
| `kano-journey/img/map-kano-*.png` | Frames of the live Kano scene (`#chapter=hausa&scene=kano` at 34 s) used as map backgrounds | `node design/kano-journey/capture-map.cjs` (same server) |
| `wireframes-2026-11-27/` | The general home and history wireframes from the assessment (`home.html`, `hist.html`, `wire.css`, PNGs) | Edit and screenshot |

Orange dashed outlines in the mock-ups mark what is new. Everything else exists on the site today.

## Work already in flight (do not duplicate)

Checked 27 Nov 10:30 UTC against every remote branch with commits not on `main`:

- **No branch** changes the home page, the shared header or the history frame.
- PR #39 (draft, agent trial of 26 Oct) is stale and unrelated.
- `codex/documentary-series-epic-pass` holds the merge of PR #77 (documentary production
  coordination, docs only) that is not on `main`. `codex/production-coordination-2026-11-05` has one docs commit.
  Neither touches templates.
- `agent/history-act1` (26 Oct) is an old Act 1 source audit, superseded by later chapters.
- Planned elsewhere, not started: Elections piece 2 (1999 to 2011) in its own thread, which touches
  only `elections/` and `build_elections.py`.

## The Kano journey

All facts in the mock-ups are copied from the repository at `87c4058`. Nothing new is claimed.

| Step | Screen | What the visitor does | New | Content comes from |
|---|---|---|---|---|
| 1 Discovery | `d1`, `p1` | Lands on the home page, types "Kano" in the header search | Search box and grouped results; "Skip to the maps"; question cards | Scene titles and `when.label` from `history/chapters/*.json`; map names |
| 2 Story | `d2`, `p2` | Opens "The earth becomes a city" and plays it | One header row (chapter, scene n of m, draft state); date once on the map; title once in the panel; "How sure" line; scene strip with names | `hausa.json` scene `kano` (`text`, `when`, `disputed`) |
| 3 Explore | `d3`, `p3` | Pauses, taps Rumfa's palace | A card for any drawn part, with its date basis and status | `hausa.json` feature `kano-city` (`what`, `status`, `monument.note`, part labels, `sources`) |
| 4 Evidence | `d4`, `p4` | Presses "Why?" | One evidence drawer: how we know, where sources disagree, what is not drawn, sources with their kind, cite | Scene `disputed`, `monument.note`, `history/sources.json` (`author`, `kind`) |
| 5 Related | `d5`, `p5` | Follows "Kano across time" | Generated place page: dated scenes as deep links, today's conflict and election figures, film slot | `hausa.json`, `sokoto.json` (jihad 1807, conquest 3 Feb 1903), `colonial.json` (Baro–Kano 1907–1911), `states.json` (1967 snapshot), `docs/conflict.html` data, `elections/raw/pres-2023-wikipedia.tsv` |

Figures on the place page, checked on 27 Nov: Kano State in the conflict data has 15 events and 33
deaths (best estimates), Jan 2020 to Oct 2026, 11 of them 2026 Candidate (preliminary) events.
2023 presidential election in Kano State: Kwankwaso (NNPP) 997,279 of 1,702,005 valid votes, 58.6%,
as announced (not yet checked against Form EC8D). The film card stays hidden until Saifu approves a film.

## Interaction changes

| # | Change | Benefit | Files |
|---|---|---|---|
| I1 | One shared header on every page: brand, search (later), History, Maps menu (Borders, Conflict, later Elections), About (later) | One way to move around; adding a map changes one menu | new `site/header.html` + a small `site_header.py` used by `build_home.py`, `build_history.py`, `build_borders.py`, `build_elections.py`, `build_map.py`/`map_template.html` |
| I2 | Home: door cards one column below 720px, two between 720 and 1000px | Fixes the 507px-wide phone page | `home_template.html` (rule at line 111 vs media query at line 140) |
| I3 | Home: "Skip to the maps" beside the hero buttons, jumping to `#doors` | A quick route past the cinematic scroll | `home_template.html` lines 166–178 |
| I4 | History: replace the 3-row chapter button bar (`#chapters`) with one row "Chapters › title · scene n of m · draft state"; chapters open in the existing `#chapter-drawer` on every screen size | Map gets ~110px more height on desktop; one place to change chapter | `history/template.html` lines 565–572 and the drawer code near 3485 |
| I5 | History: show the scene date once (`#hud`), the title once (`#card`); hide `#lower` in normal view, keep it in cinema and video modes | Removes the triple date and double title | `history/template.html` `titles()` near 1723 and CSS for `#lower` |
| I6 | History: scene strip (`#ruler`) labels show the scene title, with the date as a second line | Buttons say what the scene is | `drawRuler()` near 3108 |
| I7 | History: a short "How sure" line under the panel title with a "Why?" link to the existing Disputed / Not yet checked text | Uncertainty is visible before the story, not after it | `$("card").innerHTML` near 1883; see decision D2 |
| I8 | (Package 2) Card for any drawn part when paused, from the part's own label, status and sources | Explore the map without new claims | `history/template.html` map layer code; tests |
| I9 | (Package 2) Evidence drawer per scene, replacing the long sources tail of the panel | Calm panel, full detail one click away | `history/template.html`, `build_history.py` transcript |
| I10 | (Package 3) `atlas/index.json` built from chapter, borders and elections files; header search; generated place pages starting with Kano | Discovery across pages; pages that search engines can index | new `build_index.py`, `build_place.py`, `site/` |

## Behaviour that must not change

- Deep links `#chapter=<id>&scene=<id>` (`writeLink`/`readLink`, `history/template.html` ~3491) and
  the home page forwarding old `#country=…` links to `conflict.html`.
- Keyboard: Space plays/pauses, ← and → step scenes, Esc leaves cinema or pauses (~3233);
  the skip link to the text version; focus return when the drawer and dialogs close.
- Cinema mode, the phone default of cinema and its memory (`VIEW_KEY`), Details memory
  (`taswira-history-details`), Zomo memory (`taswira-history-guide`), Effects memory (`FX_KEY`).
- Zomo stays optional and labelled "Taswira's fictional hare guide"; Lore (`#culture-notes`) stays.
- Effects stay decoration only; `prefers-reduced-motion` rules on every page.
- The draft banner wording and the "Suggest a correction" link; Disputed and Not yet checked blocks;
  per-scene sources; the text version (`#text`, `{{TRANSCRIPT}}`).
- Video preview mode and `window.taswira.seek/info` (used by `capture_history.cjs` and the
  scene videos), and every id the capture code and tests use: `#hud`, `#lower`, `#tour-strip`,
  `#story-caption`, `#card`, `#chapters`, `#chapters-open`, `#ov-top`, `#ov-bottom`, `#video-*`.
- OpenGraph tags and preview images on every page; home doors hidden or "coming soon" by
  `data-history` / `data-borders`; UCDP credit, dataset version and Candidate labels.

Tests that pin these ids: `history_layout_browser.cjs` (`#hud`, `#lower`, `#tour-strip`, `#story-caption`),
`history_africa_browser.cjs`, `history_browser.cjs`, `history_storycraft_browser.cjs`,
`history_video_browser.cjs`, `site_theme_browser.cjs` (`#card`), `history_playback_browser.cjs` (`#chapters`),
`history_phone_cinema_browser.cjs` (`#chapters-open`). Keep the ids; hide rather than delete.

## Recommended first package: "One frame"

I1 + I2 + I3 + I4 + I5 + I6, no new content and no new data. I7 waits for decision D2.

Acceptance:

1. The same header markup on `index.html`, `history.html`, `borders.html`, `conflict.html` and
   `previews/elections.html`; current page marked with `aria-current="page"`.
2. At 390px every page has `document.documentElement.scrollWidth === 390`.
3. History at 1440×900: the scene date appears once and the title once in normal view; cinema and
   video modes unchanged (compare a `capture_history.cjs` frame before and after).
4. Every deep link in the transcript still opens its scene; keyboard keys unchanged.
5. `python -m unittest discover -s tests`, the three `--check` builds, and the history browser tests listed above pass.
6. `docs/` rebuilt only in the PR that Saifu merges to publish.

How Claude and Codex divide it, to avoid touching the same file:

| Who | Part | Files |
|---|---|---|
| Codex | Shared header partial and its adoption by home, borders, elections and the conflict map; I2, I3; a 5-check browser smoke test (home width, history first scene and keyboard, conflict loads, borders play, elections year switch) added to `tests.yml` | `site/`, `site_header.py`, `home_template.html`, `build_home.py`, `borders/template.html`, `elections/template.html`, `map_template.html`, `tests/smoke_browser.cjs`, `.github/workflows/tests.yml` |
| Claude | History frame: header adoption on the history page, I4, I5, I6, updates to the history browser tests | `history/template.html`, `build_history.py`, `tests/history_*_browser.cjs` |
| Both | Each reviews the other's PR against this README; Codex lands the header partial first so Claude's PR uses it | |

Saifu judges the look on the before/after screenshots and merges; neither agent merges or publishes.

## Later packages

- **Package 2, "Explore and evidence":** I7 (after D2), I8, I9. Needs a decision on the part-card wording.
- **Package 3, "Find Kano":** I10 with Kano as the first place page, then the launch-core places.
  The film card appears only after an approved film exists.

## Unresolved design decisions (Saifu)

- **D1 Search scope:** history scenes only first, or also borders moments and elections states.
- **D2 "How sure" text:** generate it from existing fields (the scene's `when.label` basis plus
  "disputed" or "not yet checked" when present), or add an authored one-line field per scene. An
  authored line is new historical text and needs review. The mock-up line for Kano is a draft.
- **D3 Zomo default:** stays on (today) or off on first visit; the mock-ups show the toggle only.
- **D4 Place-page sentence:** the one-line description of Kano in `d5` is new text and needs review.
- **D5 Film link rule:** which films may be linked, and whether a film opens in a dialog or on YouTube.
- **D6 Navigation labels:** "Explore" and "About" appear only when their pages exist, or as soon as the header ships.

## Technical limitations

- Pages are single generated HTML files with inline data; a shared header means a shared Python
  partial, not a runtime include (GitHub Pages serves static files only).
- History is 2.45 MB (947 KB gzip) with heavy script work on a slowed phone (5.2 s of long tasks in a lab check);
  layout changes should not add work during playback. Measure on a real phone before optimising.
- Search runs in the browser over a small JSON index; fine for hundreds of entries, not for full text.
- The browser tests take 15 to 40 minutes and hardcode `/usr/bin/chromium`; CI runs none of them today.
- Map-part cards (I8) depend on the hit areas of canvas-drawn monuments; parts drawn only on canvas
  need an invisible hit layer.
- The conflict map's base tiles load from ArcGIS at run time; a blocked network leaves a blank base layer.

## Kept intact

Chapter files, `history/sources.json`, research notes under `history/research/`, the documentary
series docs, `docs/`, all previews and proof videos, and the Ancient Kano masters (which are not in the repository).
