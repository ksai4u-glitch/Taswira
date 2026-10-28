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

### What sits on top of the map

Outside video export, everything drawn over the map lives in one of two zones, so nothing can
cover anything else however long a caption is or however small the screen:

- **Top zone:** the view buttons with any notes under them (draft and uncertainty, architecture
  caveat) on the left, the year on the right. On a phone the buttons take the whole first row.
- **Bottom zone:** one lower third on the left and Zomo on the right (above it on a phone). It
  sits above the credit line, however many lines that wraps onto.

Which lower third shows is one rule per layout. Normal: the Africa tour strip, or in other
chapters the title strip that slides in; the narration is in the side panel. Details hidden or
Cinema: only the narration caption, whose first line carries the date and place. While playing,
the caption shows one beat at a time; paused, it holds the whole narration and scrolls inside a
box of at most about a third of the map. Zomo takes at most a quarter of the map's height and
steps out on a map too short to share (under 300 px, or 420 px on a phone). Video export keeps
its own fixed 1080p layout.

Place names never pile up: in the scene's order, each name takes the first free spot beside its
point, a line above or below, or on the other side, with a short sideways step if something only
clips one end. A name with no room is hidden until there is room again; it is still in the panel.
A walled town's name only takes the spots level with its town (see "Hausa cities side by side").

Architectural settings follow the map. At the scene's camera they are a close-up (never larger
than the map); each zoom step out halves them with the land, and once they would be smaller than
about a third of the close-up they become the site's small glyph, so they never cover the
continent. Outside video export a setting is lifted, with its name, until it clears the lower
third; it may rise a little past the map's top, where its ground is open. A setting that names its
own parts (Kano) keeps its name plate below it or hides it, and each of those names shows only
where it is whole: one that a button, note, the year, the caption, Zomo or the map's edge would
cut waits until the camera brings it back into the clear. City names are about 10 px on screen at
any setting size; on a small setting only the main places are named, not the gates.

```
node tests/history_layout_browser.cjs /tmp/history.html /tmp/history-deps
```

checks every scene in the normal, details-hidden and Cinema layouts at 1440×900, 1024×700 and
390×844, jumped to and at five moments while playing, for overlays that overlap or leave the map,
and that the three settings shrink and turn into glyphs as the map zooms out (about 4 minutes).

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
clock, the globe retains its smoothly following camera on a fixed integration step, and the map camera samples the original flying geometry from
cues rather than Leaflet's real-time flight. CSS keyframes are paused and explicitly sampled at scene time rather than removed. Layout transitions remain disabled for capture; shot dissolves preserve visual continuity. At a fixed browser, viewport, device scale and fonts, repeated seeks reproduce pixels.

Build a local preview without touching the default `docs/history.html` output:

```
python build_history.py --output work/history-preview.html
node tests/history_video_browser.cjs work/history-preview.html work/history-deps
node tests/history_capture_cli.cjs work/history-preview.html work/history-deps
node capture_history.cjs work/history-preview.html work/history-deps work/pilot.mp4 30 6
```

The capture script requires Playwright, Chromium, ffmpeg and the local dependency files listed
above. `CHROMIUM_PATH` and `FFMPEG_PATH` select binaries. It intercepts dependency requests locally
and blocks other network requests. It captures four short, existing scenes at 1920×1080 and 30fps
(or the explicitly requested rate), then adds a credits card. The last argument is seconds per shot.
It writes an MP4, a WebVTT caption file and a source/uncertainty manifest. Existing outputs are never
overwritten, and failed captures remove their own temporary files. No voice-over or music is added.

The pilot excludes Esri reference scenes; their video rights remain unresolved. Model outlines are
modern shapes moved by plate rotations, not ancient coastlines, and physical geography is approximate.
The pilot and map remain **Unreviewed draft**. Historical review and source-specific reuse checks
are still required before publishing a finished video. This is a capture and layout pilot, not a
completed narrated film. The separate director experiment in PR #48 supplied the green-and-gold visual direction now used across both page templates.


## Maintainer requirement: preserve the spectacle

Saifu explicitly reaffirmed on 27 October 2026 that the experience must be flashy, catchy and
fluid. The original moving camera, globe easing, title cards, rising markers, furnace flicker,
pulses, particles and scene transitions are product requirements, not disposable decoration.
Do not obtain repeatable video by stripping those animations out. Sample their original motion
on the export clock and visually compare the result with the live player. Preserve factual
geometry, chronology, reduced-motion accessibility and the existing restraint for human suffering.
The first static-looking pilot is superseded by the restored-motion viewing copy.

Saifu also chose the green-and-gold palette and Georgia serif intro as the visual direction
for the **whole website**, including the live conflict map and interactive history player.
Keep that identity consistent across new chapters and previews. See [visual-direction.md](visual-direction.md).


### Review the complete green theme

`previews/site-theme.html` packages the interactive history and the published conflict-data
snapshot in one downloadable file. Switch pages with the History and Conflict map tabs.
The conflict data keeps its existing build date, version, preliminary labels and attribution;
this is a design preview, not a fresh data release. Basemap tiles still need internet.
Libraries are bundled for this preview only, with their notices in the file and
`previews/dependency-licenses.txt`. The source templates continue using their existing CDN URLs.

To rebuild it after building history to a scratch file:

```
python previews/build_site_theme.py <existing-map-snapshot> <built-history> <local-dependency-directory>
node tests/site_theme_browser.cjs previews/site-theme.html
```

The dependency directory also needs `leaflet-heat.js` (0.2.0). The revised standalone video
viewing copy is 23 seconds, 1920×1080 at 60 fps, with a green serif opening, camera flights,
sampled CSS animation, moving particles and short dissolves. Its source manifest and captions
are alongside `previews/history-video-pilot.html`. It supersedes the earlier 21-second 30 fps copy.


## Act 1: Africa overview

The `africa` chapter plays between `deep` and `nok`: eleven dated snapshots, five geographic
zoom stages, then an explicit rewind into Nok. Three original architectural schematics rise
only in their documented periods; they are neither actor emblems nor scale reconstructions.
The Africa area has its own bounded validator; existing Nigerian chapters keep their narrower
validation. `clock: "ago"` and `clock: "label"` are optional scene overrides. A label clock
marks the geographic interlude, avoiding a false shared date for sites from different periods.
`when.approx: false` preserves sourced exact years such as 1324 and 1495.

A point may set `monument: {type, from, to, note, sources}`: type is pyramid, stele or tower;
its documented interval must cover every scene showing that schematic. Overview scenes set
`monuments: false` and retain ordinary site markers. `kind: "line", type: "river"` uses
mapped coordinate geometry with no arrows or migration/trade particles. The Niger locator
uses Natural Earth 1:50m vertices and small joins between its generalised segments. It is
explicitly a modern physical locator, not reconstructed ancient channels or reservoir outlines.

Optional `camera_path` cues have ordered scene-content times (`at`), `center`, `zoom` and
positive `dur`, finishing before the scene ends. Both live playback and video sampling use them.
The previous path's terminal camera is retained when the following video scene begins.

Source checks and unresolved claims are preserved in `history/research/act1-*-evidence.json`.
Tié's exact coordinate is unverified: Kanem is a regional view without a fabricated capital pin.
No new trans-Saharan caravan route is drawn without source geometry.

Build an offline preview (starts directly in Act 1):

```
python build_history.py --output <scratch-history.html>
python previews/build_act1_preview.py <scratch-history.html> <local-dependency-directory>
```

Open `previews/act1.html`. It bundles the actual player and checked dependencies with their
notices; only explicit modern reference scenes request external Esri tiles.

## Zomo, architectural settings and Cinema

Saifu selected an original hare guide, working name Zomo. The history build embeds the
transparent illustration atlas in `art/`; motion follows the same scene clock as the map.
The guide can be hidden independently. Sensitive passages use a still solemn pose.
The atlas is a prototype: its walking pose is omitted pending repair. No voice is recorded.

**Details** hides/restores the information panel. **Cinema** also hides chapter navigation,
while retaining narration, date, uncertainty, timeline and transport controls. **Full screen**
requests browser fullscreen; Cinema works if it is unavailable. Escape leaves Cinema.
The conflict map has its own panel toggle and keeps the active filter context visible.

An optional monument `setting` selects `royal-cemetery`, `stelae-field` or `stone-enclosure`.
These assemble multiple local SVG components. They are architectural illustrations with
schematic arrangements/counts, not measured plans or complete reconstructed city skylines.
Their settings inherit the monument's dated evidence gate; effects add no historical sites.

Review the actual motion in `previews/storycraft.html` (opens Great Zimbabwe in Cinema).
`previews/site-theme.html` includes both updated players with the existing conflict-data
snapshot, its original build date, dataset version and preliminary labels. It is not a data update.
`previews/motif-catalogue.html` introduces eight researched cultural directions, with their
distinct permitted uses. The supplied Hausa knot is not silently promoted to a medieval flag.

```
python previews/build_act1_preview.py <built-history> <local-dependencies> --output storycraft.html --scene zimbabwe --cinema
python previews/build_motif_catalogue.py
node capture_history.cjs <built-history> <local-dependencies> <new-output.mp4> 60 8 history/cuts/storycraft-pilot.json
python previews/build_storycraft_video.py <new-output.mp4>
```

The reviewed three-shot manifest produces a silent 35-second, 1080p60 proof, including credits.
The viewing HTML embeds that actual MP4; its source manifest and captions are alongside it.
The previous four-shot pilot remains the export default when no shot manifest is supplied.
See [the creative handoff](research/creative/CLAUDE-HANDOFF-2026-10-27.md) for the character
bible, source inventories, whole-project review and the next Hausa city sequence.

## Directed story pass

`previews/directed-story.html` opens the revised 32-second Great Zimbabwe scene in Cinema.
Its authored `beats` contain ordered scene seconds (`at`), caption text (`text`), a supported
Zomo pose (`pose`) and schematic local focus `[x,y,scale]` (`focus`). They begin at zero;
focus stays inside the 440×300 illustration, with scale 0.6–2. Caption, guide and local
architectural camera use the same clock in playback and export. Other scenes retain their
existing behavior. Assembly is an illustrative reveal, never a claim of known construction order.

The **Lore** button opens Zomo’s cultural notebook with eight checked traditions/objects,
source links and the original Hausa interlace study. It pauses playback; closing restores
playback and focus. It is a modern editorial reference, not an automatic historical emblem layer.

`history/cuts/directed-zimbabwe.json` selects the 32-second sequence. The revised exporter
adds ten seconds of concise credits, or sixteen when a plate model needs its attribution.
`previews/build_storycraft_video.py <video.mp4> directed-video.html` packages a separate
viewing copy so the earlier three-setting proof remains available.

## Hausa cities: Kano

`chapters/hausa.json` follows Nok. Its first scene, "The earth becomes a city" (44 seconds), grows
Kano from Dala hill into a walled city, about 1000 to 1499: the hill and its ironworking, the
first wall and three of its gates, Rumfa's palace, his walls through named gates, Kurmi market and
the road north. It ends by pulling back to Katsina. The `walled-city` setting is an original
schematic stage set: the Chronicle names gates but does not place them, so wall lines, gate
positions, the palace footprint and the market are schematic, and nothing later is drawn (no
present-day palace decoration, no 1951 mosque, no 16th-century wall line, no emblem).

**Dated parts.** A setting can list its own `monument.parts`. Each has an `id` (a drawing in the
template), `at` (scene seconds), optional `until` (it fades out again), a `label`, `sources`, and
exactly one of `natural: true` (the land), `year` (the date it rests on) or `oral: true`.

**Dated beats.** A beat can carry `when`: `from` and `to` (whole years inside the scene's), a
`label` and a `basis`, one of `archaeology`, `chronicle` (a Kano Chronicle reckoning: the label
must say "Chronicle"), `differ` (the sources disagree: the label must say "differ") or `oral` (no
`from` or `to`, and no digits in the label). If one beat is dated, every beat is. While the scene
plays, the year and the caption's first line show the beat's label; the scene panel and the text
version start each beat with it.

`build_history.py --check` refuses a part that appears before its date (the beat on screen must
start at or after the part's year), an oral part outside an oral beat or still on screen at the
next dated beat, dated beats that go back in time, and `appear` times for places the scene does
not show. The text version lists what appears when.

```
python build_history.py --output <scratch-history.html>
node tests/history_kano_browser.cjs <scratch-history.html> <local-dependencies>
python previews/build_act1_preview.py <scratch-history.html> <local-dependencies> --output kano.html --chapter hausa --scene kano --cinema
node capture_history.cjs <scratch-history.html> <local-dependencies> <kano.mp4> 60 8 history/cuts/kano-city.json
python previews/build_storycraft_video.py <kano.mp4> kano-video.html
```

The browser test plays the scene in quarter seconds and checks that the year shows each beat's
label, that no part is visible under an earlier date, that oral tradition shows only under its
undated label, that the jumped-to scene is the finished city, that the city becomes its glyph only
in the pull-back, that repeat video seeks give identical pixels, and that the city's names stay
whole in three layouts.

### Kano 2: who lived inside the walls

The second scene, "Who lived inside the walls" (58 seconds, 1438 to 1526), answers the first
scene's closing question. It goes back to the city as it stood under Abdullahi Burja (1438–1452 by
the Chronicle's reckoning) and fills it: homes and townspeople, the roads Burja opened towards
Bornu and Gwanja, the first camels in Hausaland, the captives taken in raids to the south, books
and salt in Yakubu's reign (1452–1463), then Rumfa's palace, walls and market rising again, with
traders, the council of nine and the kakaki trumpets. It pulls back to Katsina (the eleven-year
war) and Bornu, and ends with Leo Africanus's description, written in 1526, whose visit is doubted.

- **Sensitive beats.** The captives, the eunuch officials and the war are told plainly, with Zomo
  in the still, solemn pose and nothing but fades. The twenty-one towns of captives are shown as a
  count in a framed inset while the Chronicle's record is told, because their places are not known;
  the Chronicle's numbers of people are not repeated.
- **People.** People, camels and goods are small schematic figures with no faces, dress or
  likenesses, and their numbers are illustrative.
- **Kola.** Kola is in the narration only (Lovejoy 1978: probably brought by Wangara merchants in
  the late 1400s and 1500s). A drawing would appear only after the pull-back, where nobody sees it.
- **Gwanja.** It is the Chronicle's name for the lands to the south-west; the Gonja state itself was
  founded later.

**City bases.** A setting can carry on from another city in the same chapter: `monument.base`
names it, and both must use the same `setting`. The build expands it (`expand_bases`) before the
checks, the page data and the text version:

- The base's passing parts (oral tradition, anything with `until`) are left out and cannot return.
- A base part listed again in the city's own `parts` (by `id`, with a new `at` and optional
  `dur`) rises at that time, keeping the base's label and sources.
- Every other base part is `standing`: whole from the scene's first frame, names included.
- New parts follow.

Because a standing part keeps its year, `--check` refuses a base part dated after the scene's first
beat that is not re-timed (Rumfa's palace cannot stand in 1438). The text version's "What appears
when" lists only what is new.

**Accounts.** A beat can also rest on `account`, a dated written description by a named writer;
its label must say "account", for example "1526 · Leo Africanus's account; his visit is doubted".

```
node capture_history.cjs <scratch-history.html> <local-dependencies> <kano-life.mp4> 60 8 history/cuts/kano-life.json
python previews/build_storycraft_video.py <kano-life.mp4> kano-life-video.html
python previews/build_act1_preview.py <scratch-history.html> <local-dependencies> --output kano-life.html --chapter hausa --scene kano-people --cinema
```

The browser test runs every check above on both scenes. It also checks that the second scene opens
on the standing city, whole and without Rumfa's parts, once the camera has come in from the first
scene's pull-back. In the video, a city's names also hide under the caption, the caution, the credit
and the cinema bars.

Still to check before this is published:

- The Chronicle's exact wording on Rumfa's gates and their order. The positions here are schematic;
  the ABU survey of the walls could place them.
- Leo Africanus's own text. Only Fisher's summary, via the Kano article, was used.
- The Wangarawa traders' arrival, which different sources date differently.
- A review by a historian of Kano, and by a Hausa speaker for names and spellings.

### Hausa cities side by side

The third scene, "Hausa cities side by side" (62 seconds, 1349 to 1516), pulls back from Kano to
its neighbours: Daura, Katsina, Zazzau, Gobir, Rano and Biram, each its own walled town with its own
king, and never one kingdom, so no shared border or area is drawn. It opens with the Bayajidda story
and the seven tasks as tradition, with no date. Then come the dated beats: Yaji takes Rano (Rano goes
faint), Amina of Zazzau (the Chronicle's date, with others that differ), Burja's tribute to Bornu,
Korau in Katsina, the eleven-year war, Songhai, and Kanta of Kebbi breaking with Songhai in 1516.

- **Places.** Each town is drawn at today's town of the same name, or, where the old capital is not
  known, inside a dashed ring: Zazzau at Zaria (founded about 1536), Biram at Hadejia, and Gobir at
  Birni Lalle with a wide ring and a `disputed` note. Bornu stands at Ngazargamu and Kebbi at Surame.
  Nupe, Kwararafa and Gao are told in the narration, not placed.
- **Sensitive beats.** Fighting, conquest and the tradition that Zazzau supplied slaves are told with
  Zomo in the still, solemn pose and nothing but fades.
- **Sources.** `research/hausa-cities-sources.md` lists where each place is drawn and what each
  beat rests on. Every date was checked against a source first; Amina's date, Korau's date and
  Songhai's hold are labelled as differing.

New vocabulary, all checked by `build_history.py --check`:

- **`icon: "walled-town"`** on a city-state draws it as a small walled town: an earth wall with a
  gate around a few round and flat-roofed houses. It is the same symbol for every town, not a plan.
  It is larger in Cinema and the video, and grows a little as the camera comes in. Only a
  `city-state` may carry it.
- **`notes`** on a scene: `[{place, text, at, until, oral?, art?, side?}]`. A note is up to 40
  characters at a place the scene shows, under its drawing (or `side: "above"`), from `at` to
  `until`. A note marked `oral` shows only during an oral-tradition beat and leaves before the next
  dated beat. Any other note shows only under a dated beat. `art: "well"` adds the Kusugu well of
  the story.
- **`fade`** on a scene: `{place: seconds}`. From that moment the place goes faint over 0.8 s. It
  cannot also be in `dim`.
- **Ties.** `appear` can now time a tie as well as a place. A tie must come after both of its
  places. A link's `bend` (from -0.4 to 0.4, not 0) curves it, so that Kano's tribute does not run
  through Biram. A tie whose `status` is `disputed` is drawn, then left dashed, and the map key
  explains the dashes.
- **`camera_frame: "video"`** means the scene's zooms are composed for the 1920×1080 video. A
  smaller map shows the same area, zoomed out to fit, so the towns keep their spacing.

A walled town's name stays level with its town, on either side, with no other town between them.
If there is no room, the name hides until there is; it is still in the panel. On a phone some names
hide in the busiest moments, because a name moved up or down would read as a neighbour's.

```
node tests/history_hausa_cities_browser.cjs <scratch-history.html> <local-dependencies>
python previews/build_act1_preview.py <scratch-history.html> <local-dependencies> --output hausa-cities.html --chapter hausa --scene hausa-cities --cinema
node capture_history.cjs <scratch-history.html> <local-dependencies> <hausa-cities.mp4> 60 8 history/cuts/hausa-cities.json
python previews/build_storycraft_video.py <hausa-cities.mp4> hausa-cities-video.html
```

The browser test plays the scene in quarter seconds on a desktop (Cinema and normal) and a phone.
It checks that the year shows each beat's label, with no date under the tradition, and that each
town, tie and note waits for its moment, with oral notes only under the tradition. It also checks
that Rano fades, that the disputed tie stays dashed and the other solid, and that every name shown
sits beside its own town. In the 1920×1080 video, once the camera has settled, it checks that names
and notes are never under the caption, caution, credit or bars, and that repeat seeks give
identical pixels.

Still to check before this is published:

- The Kano Chronicle's wording on Yaji and Rano: Palmer's text and the Wikipedia summary give
  different reign lengths.
- Where Gobir's capital stood in these centuries, and where Zazzau's and Biram's early capitals were.
- How far Songhai ruled the Hausa cities. The Hausa Kingdoms article marks this "citation needed",
  and Leo Africanus's account is doubted.
- A review by a historian of the Hausa states, and by a Hausa speaker for names and spellings.
