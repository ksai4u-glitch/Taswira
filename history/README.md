# History page

`python build_history.py` checks the files here and writes `docs/history.html`. It is separate from
`publish.py`, so the weekly UCDP update never changes the history page. `--check` only checks.

- `chapters/<id>.json`: one chapter each. The order is the `CHAPTERS` list in `build_history.py`.
- `sources.json`: every source a chapter cites, with what was checked and what we may do with it.
- `emblems.json`: flags, emblems and symbols, each with how sure it is (see "Emblems" below).
- `drawings/`: the few emblems that are drawn, as small SVG files of plain shapes.
- `template.html`: the page (map, scene panel, timeline, text version).
- `geo/`: today's state borders, the period background and the plate model, see `geo/README.md`.

## A chapter

A chapter has an `intro`, optional `features` (places on the map), optional `snapshots` (which
state each of today's states belonged to on a date), and `scenes`.

A feature is a `point` (a place, with `coordinates` inside the map area: latitude 2 to 20, longitude
0 to 18), a `link` (a tie between two places, `from` and `to`), a `move` (a `path` through two or
more places) or a `line` (on the globe only, see "Deep time" below). Links and moves join places of the same chapter, and a scene that shows one also
shows its places. Every feature records separately:

| Field | Meaning |
| --- | --- |
| `name` | the name in the panel and on the map; `short` is an optional shorter map label for phones |
| `evidence` | what kind of evidence it rests on (excavated, primary legal text, secondary sources...) |
| `location` | how precise the position or route is, in words (points and moves) |
| `uncertainty_km` | optional: draws a dashed ring of that radius |
| `status` | `firm`, `approx` (approximate), `disputed` or `to-check`, shown as a badge in the panel |
| `disputed` | `null`, or what sources disagree about. Set exactly when `status` is `disputed` |
| `sources` | ids from `sources.json` |
| `label` | optional: `"left"` puts the map label on the left, when two labels would overlap |

### The map vocabulary

How power and movement are drawn. The "Map key" chapter shows each one with a real example.

A point's `form` says what kind of power sat there:

| `form` | Drawn as |
| --- | --- |
| `kingdom` | a diamond, with an optional soft halo of influence: `reach_km` plus a `reach_note` saying what the size rests on. Never a hard border |
| `city-state` | a walled-town ring |
| `network` | a hub, with its ties drawn as `trade` links |
| `caliphate` | a double ring, the caliph's seat |
| `emirate` | a ring, tied to the caliphate by `allegiance` links |
| `communities` | a dotted field with a soft edge (`reach_km` and `reach_note`), for self-governing towns and villages with no ruler over them |

Two forms are about the land, not power: `lake`, a lake of the time, drawn as a blue dot with a halo
of `reach_km`, and `landmass`, a continent's name on the globe (see "Deep time" below).

A link's `type` is `allegiance`, `tribute`, `alliance`, `trade` or `ritual`; allegiance and
tribute get an arrow towards the overlord. A move's `type` is one of three motion styles:

- `migration`: a soft, widening band with drifting dots and a `period` label, such as "by the
  15th century". `uncertain: "start"` (or `"end"`) adds a faint dashed lead beyond that end of the
  path, ending in a "?"; `"whole"` draws the whole move faintly.
- `campaign`: a hard arrow drawn leg by leg. `stops` dates every place on the path, for example
  `{"kano": {"date": "1903-02-03", "precision": "day", "label": "3 Feb 1903"}}`.
  CE dates use ISO `YYYY`, `YYYY-MM` or `YYYY-MM-DD`, matching `precision` (`year`, `month`, `day`).
  `approximate: true` adds an approximation marker; year/month-only dates keep their precision
  on screen. The build rejects missing, invalid, out-of-order and out-of-scene stops.
  One compiled clock drives all campaign legs, arrivals, date labels, control changes and the
  year counter. Time is distributed by date gaps with at least 1.8 seconds per leg; scenes too
  short to support readable timing fail validation. Partial dates anchor the beginning of their
  interval for presentation only, never as a claim that the capture happened on 1 January or the
  first of a month. Route segments remain schematic, not a reconstruction of marching speed.
- `trade`: a dotted route with goods moving along it, and a `goods` label.

A scene's `control` marks colonial claims: `{"sokoto": "claimed"}` draws a hatched disc (on paper
only), `"held"` a solid one, and `"taken"` starts hatched and turns solid when a campaign in the same
scene reaches the place. A taken place without such a campaign stops the build.

### Emblems

`emblems.json` lists flags, emblems and royal symbols by `actor`, with a `tier`: `flag`, `symbol`
(a royal symbol, not a flag) or `none` (nothing documented, which is said rather than invented).
Each has a `description`, a `status` and `disputed` like a feature, a `note`, optional `from` and
`to` years, and `sources`. A point's `emblem` names one.

- A flag or symbol needs a source, or the build stops. A `none` entry says in its `note` what was
  looked for, and may not have a drawing.
- A `drawing` names an SVG file in `drawings/`, drawn as a plain silhouette from the description,
  never copied from an object. It may hold shapes only: no scripts or links.
- An emblem shown in a scene must be valid for the whole scene, not just overlap its years.
  Split a scene at an emblem's change of date if necessary.

The panel shows the emblem's description, status and sources under the place, and the text version
lists every entry, including the ones with nothing documented.

### Deep time

A chapter with `"area": "world"` may put places anywhere on Earth, and `"clock": "ago"` counts its
years as years ago ("145 million years ago", then "14,500 years ago", then "today"), counted back
from the year 2000. `when` still holds whole years, so 145 million years ago is `-145000000`.

A scene with `"view": "globe"` shows the whole Earth instead of the map, as far back as 600 million
years ago. The continents are today's outlines, each moved with its plate as the Merdith et al.
(2021) plate model says (see `geo/README.md`). The camera's `center` is a place it follows as that
place's plate moves, and its `zoom` runs from 1 (the whole Earth) to 6. On the globe a scene shows:

- points, which ride on the plate under them;
- `landmass` points: a continent's name. `blocks` lists how the model's plate numbers for that
  continent start. The model numbers plates by region: 1 North America, 2 South America, 3 Europe,
  4 northern and central Asia, 5 India, Arabia and Iran, 6 China and South-East Asia, 7 Africa,
  8 Australia, Antarctica and New Zealand. So Africa is `"7"` plus the Somali and north-east
  African blocks that the model numbers among Arabia's (5032, 5034, 5902 to 5905). Where two
  continents match a plate, the longer start wins. The continents a scene shows are lit, unless
  `dim`; the rest of the land stays dark.
- `line` features: a `path` of two or more points, a `type` (`rift`) and `active`, the years it was
  active as `[from, to]` in million years ago. A rift glows, with sparks, while it is active and
  turns grey after. A line rides on the plate under its first point, so it keeps its shape.

The build stops if a place, line point or camera centre on the globe is not on one of the model's
continents, if the model does not place its plate at the scene's years, if a continent's `blocks`
match no plate, or if a line or continent is shown on the map instead of the globe.

### Not yet checked

Anything with status `to-check`, a feature or a drawn emblem, may only be shown in a scene whose
`unchecked` note says what is unchecked. The panel then shows "Not yet checked." with that note.
Otherwise the build stops: check it first.

Every **scene** has an `id` (used in links like `#chapter=nok&scene=iron`), a `title`, `text`,
`when` (`from` and `to` as whole years, BCE as negative numbers, plus a `label` written for people),
a `camera`, `sources`, and either `show` (feature ids, with `dim` for ones shown faintly) or a
`snapshot`. An optional `disputed` adds a note to the scene. On a phone's small map the camera
is fitted to the scene's places and their labels instead, never closer than the scene's camera.

**Background.** Historical map scenes default to plain land, lakes and rivers from Natural Earth,
including scenes after 1914. Today's roads, towns and administrative borders are not a reconstruction
of any earlier period. The physical geography is also modern and approximate; see `geo/README.md`
for its limits. Dated features and state snapshots are drawn on top separately.

A scene from 1914 onward may explicitly request `"background": "modern-reference"` to locate places
on today's map, as the Nok chapter's archaeological rediscovery scene does. It must include a
non-empty `background_note` explaining that the map is a modern locator, not a historical
reconstruction. The note appears in the scene panel and text version. Modern reference scenes
also show today's state borders faintly. Globe scenes and scenes before 1914 may not use this option.
Leave `background` out (or use `"period"`) for the neutral map.

While a scene plays, things appear over time: a year counter runs from `when.from` to `when.to`,
the narration appears sentence by sentence, places pulse in one after another, and on state maps
the new borders draw themselves before the new states take their colours. Jumping to a scene shows
it finished, with the full date label rather than an animated starting year. Reduced-motion
views also show complete information. Optional extras:

- `furnace`: feature ids that glow, for iron working.
- `mood`: the decoration while a scene with places plays. One of `survey` (a radar-like sweep over
  the sites), `farming` (stalks growing), `sculpture` (clay-coloured specks gathering), `iron`
  (embers and sparks at the `furnace` sites), `decline` (the map greys, ash drifts, the sites smoulder),
  `excavation` (a searchlight, dust and a camera flash as each site appears), `calm` (no sparks
  or flashes, only a soft ring as each place appears, for scenes about trade or everyday life),
  `delta` (sand and mud coming down the river from the north and fanning out into the sea, wider as
  the scene goes on) or `greening` (green spreading over the land and ripples on its lakes, then
  sand blowing back in over the last part of the scene).
- `effects`: a list of moments, where `at` is how far into the scene (0 to 1) each starts:
  `{"type": "pulse", "state": "NG-FC", "at": 0.5}` (a beacon of light over a state),
  `{"type": "arc", "from": [lat, lon], "to": [lat, lon], "from_label": "...", "to_label": "...", "at": 0.6}`
  (a comet from one place to another), or `{"type": "shatter", "features": ["..."], "at": 0.2}`
  (fragments flying from a site; only where the evidence is broken pieces, as at the Kagarko sites).

### Effects

On top of the map, a layer of effects plays at every change: a title card when a chapter starts,
the scene's title sliding in, a band of light sweeping across, the year counter rolling to the new
date (with streaks of light when it jumps far forward or back in time), shockwaves where places
appear or new states take their colours, glowing tips on borders as they draw, and the camera leaning
towards the new states. Play runs on from one chapter into the next.

These are decoration and must stay that way: they never add a place, border or date that is not in
the chapter file, and the panel says so. The Effects button switches them off (remembered in the
browser), and they are off when the device asks for less motion.

A **snapshot** lists `groups` (the states at that date, each with the codes of today's states it
covered, and `from`: the state it came from in the previous snapshot) and `split` for today's states
that were divided between earlier states. The build stops if any of today's states is missing or
placed twice, if the number of states does not match `count`, or if a `from` does not exist.

## Playback and reference chapters

`CHAPTERS` orders the chapter bar. `reference: true` makes a chapter optional reference: it stays
available through its button, scene navigation and deep links, but normal Play skips it. Play in
a reference chapter stops at its end. The Map key is last in the bar and marked "reference";
the current film sequence is Deep time → Nok → States. Replay restarts that sequence, or the
selected reference chapter when exploring the key.

## Rules for war and violence

Humour must not cover killing, enslavement, starvation, displacement or atrocity. No jokes,
comic sounds or celebratory effects accompany those passages. Set `sensitive: true` on scenes
about these subjects: their factual markers and lines remain, but decorative canvas effects
and marker pop/rise animations are suppressed. Campaign scenes receive this treatment automatically,
including arrival rings, bursts, shockwaves and victory glows.

For Acts 4 and 6, follow this sequence:

1. Establish the place, actors and immediate context.
2. Name forces; never imply their strength through icon size.
3. Show advances and retreats through sourced, dated stops.
4. Show a siege only where it is documented; do not invent a perimeter.
5. Change the captured site's marker on its date. A captured town does not fill surrounding territory.
6. Show fronts only as dated, sourced snapshots; never interpolate between them.
7. Give human consequences their own cards, apart from military movement.
8. Include aftermath: governance, livelihoods, displacement, rebuilding and continuing resistance
   where sources support them.

Uncertain casualty and displacement numbers appear as sourced ranges with a period and category,
never as running counters. Explain incompatible estimates separately. A campaign's animated path
is a presentation of documented links, not evidence of a surveyed route or a moving front.

## Rules the content follows

1. Draw what the evidence supports: dated points for archaeology, legal snapshots for state creation.
   No made-up borders for times before surveyed boundaries, and no shapes that morph between dates.
   Never show today's borders, roads or town names under a scene set before 1914.
2. Say how sure each thing is, and where sources disagree, say so instead of picking one quietly.
   Draw no flag or emblem without a source; where none is documented, say so.
3. Cite every scene and feature, and record what we may reuse. Sources with unknown rights are cited
   and described, never copied.
4. The page stays marked "Unreviewed draft" until a historian has looked at it.

## Browser regression check

With Playwright and Chromium installed, build a preview outside `docs/` (for example, call
`build_history.build()` and write its returned HTML to a temporary file). Then run:

```
node tests/history_browser.cjs /tmp/history.html /tmp/history-deps /tmp/history-screenshots
node tests/history_playback_browser.cjs /tmp/history.html /tmp/history-deps
```

The dependency directory holds local copies of `leaflet.js` and `leaflet.css` 1.9.4,
`d3-array.js` 3.2.4 and `d3-geo.js` 3.1.1. Set `CHROMIUM_PATH` if necessary. The script intercepts
CDN requests and uses a placeholder for Esri tiles, so it checks layer selection and requests,
not the availability or appearance of Esri's live service. Screenshots are optional.

It checks all scenes at 1440×900 and 390×844, jumped to, playing and with reduced motion.
Historical scenes must leave the modern layer detached; only labelled modern-reference scenes
may create Esri tiles. The text and all dated scene overlays remain available without tile service.

## Video pilot and exact-time capture

A downloadable, offline viewing copy is in `previews/history-video-pilot.html`, with its caption
file and source manifest alongside. It embeds the compressed 21-second 1080p/30fps pilot.

The main player has a separate video preview mode. Use **Video preview**, scrub its labelled scene
time slider, then use **Exit video preview** or Escape to return. Playback does not start on its own.
The export layout removes the panel and controls from the map, enlarges text, and includes captions,
draft/uncertainty markers and source credits. The full transcript remains in the normal player.

```js
window.taswira.info("deep", "south-atlantic");
window.taswira.seek("deep", "south-atlantic", 7);
window.taswira.exitVideo();
```

Chapter and scene can be IDs or zero-based indices. Time is non-negative seconds, including a
3.6-second title card at the start of a chapter, clamped to the scene's duration. `info()` reports
the content start, duration, source IDs, location precision and dispute/uncertainty metadata.
Seeking stops normal playback. The year counter has a fixed scene origin, effects use the explicit
clock, the globe camera has no time-dependent easing, and the map camera is computed directly from
cues rather than Leaflet's real-time flight. CSS animations and transitions are disabled only in
video mode. At a fixed browser, viewport, device scale and fonts, repeated seeks reproduce pixels.

Build a local preview without touching the default `docs/history.html` output:

```
python build_history.py --output work/history-preview.html
node tests/history_video_browser.cjs work/history-preview.html work/history-deps
node tests/history_capture_cli.cjs work/history-preview.html work/history-deps
node capture_history.cjs work/history-preview.html work/history-deps work/pilot.mp4 30 6
```

The capture script requires Playwright, Chromium, ffmpeg and the local dependency files listed
above. `CHROMIUM_PATH` and `FFMPEG_PATH` select binaries. It intercepts dependency requests locally
and blocks other network requests. It captures three short, existing scenes at 1920×1080 and 30fps
(or the explicitly requested rate), then adds a credits card. The last argument is seconds per shot.
It writes an MP4, a WebVTT caption file and a source/uncertainty manifest. Existing outputs are never
overwritten, and failed captures remove their own temporary files. No voice-over or music is added.

The pilot excludes Esri reference scenes; their video rights remain unresolved. Model outlines are
modern shapes moved by plate rotations, not ancient coastlines, and physical geography is approximate.
The pilot and map remain **Unreviewed draft**. Historical review and source-specific reuse checks
are still required before publishing a finished video. This is a capture and layout pilot, not a
completed narrated film. The separate director experiment in PR #48 is independent.

