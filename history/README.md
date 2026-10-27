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
- `campaign`: a hard arrow drawn leg by leg, with a pulse at each stop. `dates` gives a label per
  place on the path, such as `{"kano": "3 Feb 1903"}`.
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
- An emblem shown in a scene must fit the scene's years.

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

**Background.** The build picks it from `when.from`. A scene that starts before 1914 sits on a
plain map of land, lakes and rivers from Natural Earth, with no borders, roads or modern town
names, because none of those existed then. From 1914 (the year the outline of Nigeria first
existed) a scene uses today's map tiles, and scenes with places also show today's state borders
faintly, for reference. The two backgrounds cross-fade when the story crosses that line, as it does
in the Nok chapter's last scene about the 20th-century digs. See `geo/README.md` for the data.

While a scene plays, things appear over time: a year counter runs from `when.from` to `when.to`,
the narration appears sentence by sentence, places pulse in one after another, and on state maps
the new borders draw themselves before the new states take their colours. Jumping to a scene shows
it finished. Optional extras:

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

## Rules the content follows

1. Draw what the evidence supports: dated points for archaeology, legal snapshots for state creation.
   No made-up borders for times before surveyed boundaries, and no shapes that morph between dates.
   Never show today's borders, roads or town names under a scene set before 1914.
2. Say how sure each thing is, and where sources disagree, say so instead of picking one quietly.
   Draw no flag or emblem without a source; where none is documented, say so.
3. Cite every scene and feature, and record what we may reuse. Sources with unknown rights are cited
   and described, never copied.
4. The page stays marked "Unreviewed draft" until a historian has looked at it.
