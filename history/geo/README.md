# State borders

`nga-states-2022.topojson` holds today's 36 states and the FCT, simplified for the history page.

- **Source:** GRID3 Nigeria state boundaries (boundary year 2022), as published by
  [geoBoundaries](https://www.geoboundaries.org/) (gbOpen, NGA, ADM1). File
  `releaseData/gbOpen/NGA/ADM1/geoBoundaries-NGA-ADM1_simplified.geojson` from
  https://github.com/wmgeolab/geoBoundaries at commit `5c25134`, downloaded 26 Oct 2026
  (SHA-256 `edd28050c7f1ae40471424605f74e4d2df83502e4f301089761ae18f8ae2fbbf`).
- **Licence:** CC BY 4.0 (from the geoBoundaries metadata file). Credit GRID3 and geoBoundaries.
- **How it was made:** with [mapshaper](https://github.com/mbloch/mapshaper) 0.6.102, which keeps the
  border shared by two states as one line, so the page can tell which lines separate which states:

  ```
  npx mapshaper geoBoundaries-NGA-ADM1_simplified.geojson -filter-fields shapeName,shapeISO \
    -rename-layers states -simplify 12% keep-shapes \
    -o format=topojson quantization=20000 nga-states-2022.topojson
  ```

These are today's borders. The history page uses them to approximate older states, and says so on
every state map.

# Period background

`natural-earth-background.json` is the default background for historical map scenes in any era: land,
lakes and rivers only, with no borders, roads or towns. Made by `make_background.py` in this folder.

- **Source:** [Natural Earth](https://www.naturalearthdata.com/), version 5.2.0-pre, from
  https://github.com/nvkelso/natural-earth-vector at commit `ca96624`, downloaded 27 Oct 2026. Files
  (`geojson/` folder, SHA-256):
  - `ne_50m_land.geojson` `e874b27a51d146452be360cafb3cc50c86001074a67d534113e6534682f9826b`
  - `ne_10m_land.geojson` `1ac90796408bc6ad6911d69448485d3c4dbf2190370080368a09976e1c9f7416`
  - `ne_10m_lakes.geojson` `2d036f53dedec578001c5c30c2959ee7d4eebc1306900fa4367c49929ec8f2d9`
  - `ne_10m_rivers_lake_centerlines.geojson` `bb854a900ecbd3b408df46d5e16e3e0f974ba55993f9d8b5c26e855273c0905a`
- **Licence:** public domain ("Crediting the authors is unnecessary"). The page credits it anyway.
- **What the script does:** covers the whole world, so the map never ends in a straight edge
  however far the camera pulls back, with detail rising towards Nigeria in three rings:
  - 6° W to 20° E, 0° to 18° N: detailed (1:10m) land and rivers;
  - out to 40° W to 65° E, 40° S to 45° N (Africa, Europe, Arabia): 1:50m land, rivers down to
    Natural Earth's rank 5;
  - the rest of the world: 1:50m land, simplified more, and only the largest rivers (rank 3).

  Lakes are never cut: a lake that reaches the middle ring is kept whole, and elsewhere only the
  largest lakes are kept. The script simplifies the lines and stores them as whole numbers (about
  250 KB). Reservoirs are left out because they are 20th-century (Kainji 1968, Lake Volta 1965); the
  river lines through them are kept. The page draws the land a second time 360° to each side, so a
  very wide screen at the farthest zoom shows the world wrapping round instead of empty sea. To
  remake the file, download the four files into a folder and run:

  ```
  python history/geo/make_background.py <that folder>
  ```

**Limits.** The coast, rivers and Lake Chad are drawn as they are today. Lake Chad was larger in
most earlier periods (about 28,000 km² in 1870, against about 1,900 km² recently), and river courses
and the delta coast have shifted over the centuries. Showing those changes needs sources for each
period and is left for later chapters.

# Plate model

`plates.json` holds the moving continents for the deep-time chapter's globe. Made by
`make_plates.py` in this folder.

- **Source:** Merdith, A. S., Williams, S. E., Collins, A. S. and others (2021), "Extending
  full-plate tectonic models into deep time: Linking the Neoproterozoic and the Phanerozoic",
  Earth-Science Reviews 214, 103477 (doi:10.1016/j.earscirev.2020.103477). Model files version
  1.2.4 on Zenodo (doi:10.5281/zenodo.13635864): `Merdith_etal_2021_ESR_v1.2.4.zip`, received
  27 Oct 2026 (MD5 `181ab32d1d235a923ee343568731e64a`, which matches the Zenodo record; SHA-256
  `c08cd59f9fc26a99315a9a28c7a8da33ef7dc16e60c14eaec24e673cb6b78e6e`). Two files in it are used:
  `Rotations/1000_0_rotfile_Merdith_etal.rot` and `Continents/shapes_continents.gpml`.
- **Licence:** CC BY 4.0. The globe credits the model and links to it.
- **What the script does:** works out where each plate was every 10 million years from 600 million
  years ago to today. The rotation file says how each plate turned against another one at given
  times; the script blends between those times and chains each plate back to the fixed frame
  (plate 0), as GPlates does. It keeps the continent outlines larger than 15,000 km² that existed
  in those 600 million years, simplified to within 0.25° (about 28 km). Positions are stored in
  hundredths of a degree and rotations as whole numbers (times 10,000), and a block that moves
  exactly with another names that plate instead of repeating its rotations. To remake the file:

  ```
  python history/geo/make_plates.py <Merdith_etal_2021_ESR_v1.2.4.zip, or the folder it unzips to>
  ```

  It warns if the zip's MD5 differs from the one above.

**Limits.**

- The outlines are today's continents with their shelves, so they are not the coastlines of the
  time: seas covered parts of them for long stretches.
- The model's frame is palaeomagnetic. Rocks record how far from the poles they formed, not how far
  east or west, so the longitudes of deep time are the model's choice.
- The page blends between the 10-million-year steps, so a plate can be slightly off from the
  model between them.
- Each outline is shown for the years the model gives it, with one exception: the model shows the
  Benue Trough's two outlines only today, which would leave a hole in Africa in every past scene.
  Their rock was there before the rift, only narrower, so `make_plates.py` draws them at all times.
- The outer Niger Delta is in none of the model's outlines, so it is sea on the globe. That is
  right for most of the past: the delta has grown out over the last 56 million years or so.
- Pieces under 15,000 km² (small islands and slivers) are left out, and each outline is simplified
  on its own, so the page widens the land's edges a little to close the cracks between neighbours.

