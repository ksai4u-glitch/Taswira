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
