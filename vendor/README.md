# Map libraries carried by the site

`vendor.py` writes these files into the built pages in place of their unpkg.com tags, so the
live site does not depend on another website. They are the unchanged published files.

| File | Version | From | Licence | SHA-256 |
| --- | --- | --- | --- | --- |
| leaflet.js | 1.9.4 | npm `leaflet` dist/ | BSD-2-Clause (LICENSE-leaflet) | db49d009c841f5ca34a888c96511ae936fd9f5533e90d8b2c4d57596f4e5641a |
| leaflet.css | 1.9.4 | npm `leaflet` dist/ | BSD-2-Clause (LICENSE-leaflet) | a7837102824184820dfa198d1ebcd109ff6d0ff9a2672a074b9a1b4d147d04c6 |
| leaflet-heat.js | 0.2.0 | npm `leaflet.heat` dist/ | BSD-2-Clause (LICENSE-leaflet.heat) | eb952aae5806a1102729f291bab887dde783ace859819a354827a776e73e486a |
| d3-array.min.js | 3.2.4 | npm `d3-array` dist/ | ISC (LICENSE-d3-array) | 80aa70d0cd17dabddf6d056494ea17926a45a69da8b7850220aace331bad671d |
| d3-geo.min.js | 3.1.1 | npm `d3-geo` dist/ | ISC (LICENSE-d3-geo) | 23e574f1e8d4716d622bce45356a379b66a277162b145f5f147e4c8daefb73d2 |

leaflet.js and leaflet.css match the integrity hashes Leaflet publishes for 1.9.4
(sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo= and sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=).
