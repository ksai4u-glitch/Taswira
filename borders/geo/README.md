# Borders 1886 to 1914

`scramble.json` holds every country, colony and protectorate that touched Africa between
1 January 1886 and 1 January 1914, with the dates each set of borders starts and ends.
Made by `make_scramble.py` in this folder (standard library only).

- **Source:** CShapes 2.0, Gleditsch-Ward version: `inst/extdata/cshapes_2_gw.topojson.xz` from the
  CShapes 2.0 R package (CRAN version 2.0, published 5 June 2021), via the read-only CRAN mirror
  https://github.com/cran/cshapes at commit `54840534d9a82cfd01caf1021f85933e701e8318`, downloaded
  26 Nov 2026. SHA-256 `196c6d9d881cf944e176e4ce5bfc61074d21792de7152cb0a9e035e56b0297c8`
  (the script refuses any other file). ETH Zurich's own data page (icr.ethz.ch) was blocked from
  the build machine, so the copy in the R package was used.
- **Cite:** Schvitz, Guy, Luc Girardin, Seraina Rüegger, Nils B. Weidmann, Lars-Erik Cederman and
  Kristian Skrede Gleditsch (2022). Mapping the International System, 1886-2019: The CShapes 2.0
  Dataset. *Journal of Conflict Resolution* 66(1): 144-161.
- **Licence:** the R package that carries the data is GPL (>= 2). Taswira is non-commercial and
  credits the authors on the page. To check before publishing: the licence on ETH's data page.
- **What the script does:**
  - keeps units whose dates overlap 1886-01-01 to 1914-01-01, and of each one only the polygons
    whose middle lies in Africa or its islands (so the Ottoman Empire keeps Tripolitania but not
    Arabia; Spain's and Portugal's own islands, which are not colonies, are left out);
  - simplifies each border line on its own (Douglas-Peucker, 0.04 degrees, about 4 km), so a
    border shared by two colonies stays one line, and keeps coordinates to 0.01 degrees;
  - writes the borders as a small TopoJSON-style topology (arcs as steps from the last point).

## What CShapes does and does not show

CShapes maps borders as the colonial powers **claimed** them, with exact start and end dates. It
does not map African states (the Sokoto Caliphate, Asante, the Mahdist state and others), so land
no European power claimed is left blank, and the page says these lands were African-ruled. Known
differences from other sources are written in `borders/story.json` and shown on the page:

- the two Boer republics stay independent in CShapes until 1910; the page shows them as British
  from the Treaty of Vereeniging, 31 May 1902 (a `correction`);
- CShapes starts Northern and Southern Nigeria on 1 January 1899; British government rule began
  on 1 January 1900 (a note);
- Egypt is coded as a British dependency from 1886, although it was formally Ottoman until 1914
  (a note).

To make the file again:

```
python borders/geo/make_scramble.py path/to/cshapes_2_gw.topojson.xz
```
