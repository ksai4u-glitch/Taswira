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

`natural-earth-background.json` is the map background for scenes that start before 1914: land,
lakes and rivers only, with no borders, roads or towns. Made by `make_background.py` in this folder.

- **Source:** [Natural Earth](https://www.naturalearthdata.com/), version 5.2.0-pre, from
  https://github.com/nvkelso/natural-earth-vector at commit `ca96624`, downloaded 27 Oct 2026. Files
  (`geojson/` folder, SHA-256):
  - `ne_50m_land.geojson` `e874b27a51d146452be360cafb3cc50c86001074a67d534113e6534682f9826b`
  - `ne_10m_land.geojson` `1ac90796408bc6ad6911d69448485d3c4dbf2190370080368a09976e1c9f7416`
  - `ne_10m_lakes.geojson` `2d036f53dedec578001c5c30c2959ee7d4eebc1306900fa4367c49929ec8f2d9`
  - `ne_10m_rivers_lake_centerlines.geojson` `bb854a900ecbd3b408df46d5e16e3e0f974ba55993f9d8b5c26e855273c0905a`
- **Licence:** public domain ("Crediting the authors is unnecessary"). The page credits it anyway.
- **What the script does:** keeps detailed (1:10m) land and rivers between 6° W and 20° E, 0° and
  18° N, and coarser (1:50m) land and only the biggest rivers out to the edge of what the map can
  show (40° W to 65° E, 40° S to 45° N). It simplifies the lines and stores them as whole numbers.
  Reservoirs are left out because they are 20th-century (Kainji 1968, Lake Volta 1965); the river
  lines through them are kept. To remake the file, download the four files into a folder and run:

  ```
  python history/geo/make_background.py <that folder>
  ```

**Limits.** The coast, rivers and Lake Chad are drawn as they are today. Lake Chad was larger in
most earlier periods (about 28,000 km² in 1870, against about 1,900 km² recently), and river courses
and the delta coast have shifted over the centuries. Showing those changes needs sources for each
period and is left for later chapters.
