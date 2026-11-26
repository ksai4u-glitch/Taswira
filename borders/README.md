# Borders map (draft)

"Who drew Africa's borders?": the Scramble for Africa on a globe. It runs from 1 January 1886 to
1 October 1960, the day Nigeria became independent. It is a draft and is **not published**: `python build_borders.py` writes
`previews/borders.html` and refuses to write `docs/`.

- `story.json`: the words on the page. `powers` (colours), `names` (the name each unit had at the
  time, from a date; an optional third item is a shorter map label), `corrections` (where the page
  differs from CShapes, with a note and sources), `notes` (shown when you tap a unit), `moments`
  (the stops while it plays, each with a date, a camera `focus` [lon, lat], text, sources and an
  optional `highlight`: units labelled first while it shows) and `sources`. A correction can end
  with a `to` date.
- `geo/`: the borders, from CShapes 2.0. See `geo/README.md`.
- `template.html`: the page (globe, panel, timeline, sources, text version).

`python build_borders.py --check` checks that every unit has a period name, every moment and
correction cites a known source, moments are in date order inside the borders' dates, and the
last moment is the last date. The tests are in `tests/test_build_borders.py`.

The share of Africa "claimed by European powers" is land area: the units of Britain, France,
Germany, Belgium (King Leopold's Congo before 1908), Portugal, Italy and Spain, out of all the land
CShapes maps in Africa on the last date. League of Nations mandates count with the power that ran
them; South Africa and its South West Africa mandate count as white minority rule.

The timeline is not to scale: 1886 to 1914 takes 38% of it, 1914 to 1950 22% and the 1950s 40%,
so the years when the map changes fastest get the most room and playing time (about two minutes
with the stops).
