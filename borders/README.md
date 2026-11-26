# Borders map (draft)

"Who drew Africa's borders?": the Scramble for Africa on a globe. This first piece is a proof
scene, 1886 to 1914. It is a draft and is **not published**: `python build_borders.py` writes
`previews/borders.html` and refuses to write `docs/`.

- `story.json`: the words on the page. `powers` (colours), `names` (the name each unit had at the
  time, from a date; an optional third item is a shorter map label), `corrections` (where the page
  differs from CShapes, with a note and sources), `notes` (shown when you tap a unit), `moments`
  (the stops while it plays, each with a date, a camera `focus` [lon, lat], text and sources) and
  `sources`.
- `geo/`: the borders, from CShapes 2.0. See `geo/README.md`.
- `template.html`: the page (globe, panel, timeline, sources, text version).

`python build_borders.py --check` checks that every unit has a period name, every moment and
correction cites a known source, moments are in date order inside the borders' dates, and the
last moment is the last date. The tests are in `tests/test_build_borders.py`.

The share of Africa "claimed by European powers" is land area: the units of Britain, France,
Germany, Belgium (King Leopold's Congo before 1908), Portugal, Italy and Spain, out of all the land
CShapes maps in Africa on 1 January 1914.
