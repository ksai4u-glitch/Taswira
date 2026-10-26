# History page

`python build_history.py` checks the files here and writes `docs/history.html`. It is separate from
`publish.py`, so the weekly UCDP update never changes the history page. `--check` only checks.

- `chapters/<id>.json`: one chapter each. The order is the `CHAPTERS` list in `build_history.py`.
- `sources.json`: every source a chapter cites, with what was checked and what we may do with it.
- `template.html`: the page (map, scene panel, timeline, text version).
- `geo/`: today's state borders, see `geo/README.md`.

## A chapter

A chapter has an `intro`, optional `features` (places on the map), optional `snapshots` (which
state each of today's states belonged to on a date), and `scenes`.

Every **feature** records separately:

| Field | Meaning |
| --- | --- |
| `evidence` | what kind of evidence it rests on (excavated, primary legal text, secondary sources...) |
| `location` | how precise the position is, in words |
| `uncertainty_km` | optional: draws a dashed ring of that radius |
| `disputed` | `null`, or what sources disagree about |
| `sources` | ids from `sources.json` |

Every **scene** has an `id` (used in links like `#chapter=nok&scene=iron`), a `title`, `text`,
`when` (`from` and `to` as whole years, BCE as negative numbers, plus a `label` written for people),
a `camera`, `sources`, and either `show` (feature ids, with `dim` for ones shown faintly) or a
`snapshot`. An optional `disputed` adds a note to the scene.

While a scene plays, things appear over time: a year counter runs from `when.from` to `when.to`,
the narration appears sentence by sentence, places pulse in one after another, and on state maps
the new borders draw themselves before the new states take their colours. Jumping to a scene shows
it finished. Optional extras:

- `furnace`: feature ids that glow, for iron working.
- `mood`: the decoration while a scene with places plays. One of `survey` (a radar-like sweep over
  the sites), `farming` (stalks growing), `sculpture` (clay-coloured specks gathering), `iron`
  (embers and sparks at the `furnace` sites), `decline` (the map greys, ash drifts, the sites smoulder)
  or `excavation` (a searchlight, dust and a camera flash as each site appears).
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
2. Say how sure each thing is, and where sources disagree, say so instead of picking one quietly.
3. Cite every scene and feature, and record what we may reuse. Sources with unknown rights are cited
   and described, never copied.
4. The page stays marked "Unreviewed draft" until a historian has looked at it.
