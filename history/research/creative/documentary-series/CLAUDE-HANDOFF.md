# Claude handoff: series, map evidence and the final website

3 November 2026. Direct maintainer brief; documentation stage only. Main inspected at `7b737d55b521da2aec60a0278aa2c9783af0713c` (merged PR #71). No application or live-site edits are part of this handoff.

## Product direction to carry forward

Everything built for the Taswira map can become a candidate for a Codex/Higgsfield documentary or social film, provided its evidence survives a film-level audit. The map and films should share entity identities, chronology and source references. Films must not silently turn schematic map layouts or disputed dates into photoreal certainty.

The final website should bring the **history map and conflict map into one product**, with:

- A **Home** landing page explaining the project and offering clear entrances to History, Conflict and Visualize.
- A **Visualize** page containing the series teaser, episode highlights, historical “Did you know?” cards and title cards leading to the relevant map view and source note.
- Contextual links from a film/episode to its historical places, date range, relationships and sources; links back from a map feature to related films when available.
- A visible distinction between published episodes, working reconstructions, disputed historical claims and forthcoming material.

These are recommendations for subsequent implementation. The current `docs/` tree contains the conflict page and preview image, not a verified deployed combined product. Route names and episode IDs below are proposals. Preserve existing users' map links when routing is introduced.

## Integration proposal

An episode record could carry `episode_id`, title, period, editorial status, map chapter/feature/scene references, claim IDs, source IDs, reconstruction disclosure, media master/derivative references, rights/attribution, captions, and publication status. A claim record should keep source passage, evidence type, date basis, geographical precision, confidence/dispute and whether the image is interpretive. Avoid creating a second competing source registry: reconcile documentary source IDs with `history/sources.json` before runtime integration.

Suggested editorial IDs are `kano-foundations`, `taswira-series-teaser` and `sokoto-1804-1817`. They do not yet exist as runtime routes or database rows. Keep production artifacts outside the live `docs/` folder. Native exports should record pinned repository commit, scene/cut IDs, camera/time settings, source references, output dimensions and frame rate so that later films can repeat a verified view.

## Map evidence proposals

References R/S/C/W belong to the linked research memos; K references are in [SOURCES.md](SOURCES.md). This table proposes review work. It does not authorize an automatic change to a dated runtime claim or geometry.

| Existing target | Already represented / new finding | Proposed action and evidence limit |
|---|---|---|
| `hausa/kano-city`, scene `kano` | Already labels early reign dates as Chronicle reckoning and geometry as schematic; already distinguishes Yusa from Zamnagawa. | Upgrade passage links to the original Palmer scan K1 pp.66–67 and retain disagreement. K2 is a Nigerian tentative-list submission, not an independent UNESCO historical certification. |
| `hausa/kano-city` monument parts for gates, palace, Kurmi | Existing map explicitly calls positions/footprints schematic and excludes later decoration. The film enlarges and varies gates for cinema. | Preserve that discipline in exported references. Neither the generated city nor later gate photographs should become a medieval survey. Gate A/B/C heights are production units, not historical measurements or identities. |
| `hausa/kano-life`, scene `kano-people` | Already includes Burja's raids/captives, learning, market and royal institutions. | Bring that human and coercive dimension into the longer film. K1 pp.75–78 was checked directly; its counts and royal praise remain attributed, not audited. No coordinates for the reported captive settlements. |
| `hausa` introduction | Already distinguishes nineteenth-century copy from Last's earlier-compilation argument. | Add K4 as evidence that authorship/dating is debated; do not describe Last's hypothesis as consensus. No need to erase the existing qualification. |
| `sokoto/degel`, scene `jihad` | Existing place is approximate. R1 pp.23–24 describes staged migration and alternative dates. | Retain approximate geography; use February 1804 for uncomplicated narration. Check any exact “declaration of war” date separately from the departure. Gudu would be a new node only after gazetteer verification. |
| `sokoto/alkalawa` | Existing 3 October 1808 date agrees with R1's main text; its note offers 26 September. | Add the alternative and source passage. Do not replace the main date as though it were simply wrong. Show displacement and continuing town life rather than total erasure. |
| `sokoto/zaria` | Existing claim: captured in 1805. R1 p.39 n.101 describes its fall about three months after Alkalawa in 1808. | **Reconcile:** distinguish first emir/appointment chronology from conquest/occupation and compare additional scholarship. Do not silently substitute a new exact date based on one note. |
| `sokoto/gwandu`, scene `emirates` | Existing claim: Abdullahi's seat from 1812. R1 pp.41–42 distinguishes division of authority, Bodinga residence and Gwandu headquarters after Usman's death. | **Clarify:** authority and residence are separate. Sifawa/Bodinga are candidate additions; no new coordinates verified. Keep links schematic and time-aware. |
| `sokoto/conquest-1903`, scene `conquest` | Existing Kano/Sokoto capture context. C1 dispatch supports Kano fighting on 3 February and Sokoto occupation on 15 March 1903. | Preserve event/date distinctions. Do not falsely “correct” Kano to 6 February. Obtain the full dispatch header before assigning its first-person voice; seek local perspectives. No exact marching route verified. |
| `kanem/kanem` and scenes `kanem-east`, `sayfawa` | Existing map already says Njimi is not securely located, records proposed Tié identification and uses Mao only as a regional anchor. | Retain that qualified wording; S1/S2 strengthen its source basis. A new precise capital pin is not justified by this pass. |
| `kanem/idris-alooma` scene | Local chapter uses a reign chronology that differs from the 1987 edition's metadata/abstract, S6. | **Reconcile editions**, not just numbers. Use a sixteenth-century label until the edition and chronology are read. Early Kanem, later Bornu and Alooma are different periods. |
| `kanem/move-west` | Existing late-fourteenth-century relocation relationship. | Prefer “royal court moved” over a claim that a whole people crossed simultaneously. No exact route or medieval shoreline established. S2. |
| Proposed Kanem–southern Nigeria material connection | New archaeological provenance lead, S1. | At most a qualified direct-or-indirect regional relationship. No definite caravan itinerary, conquest edge or transfer of political sovereignty. |
| Colonial slavery/court-case layer, not an existing feature | C3 has a published erratum changing one case location from Kano to Katagum. | Corrected passage and case context must be checked before plotting an event. The erratum does not relocate all examples in the paper. |
| `colonial/satiru`, scene `resistance` | Existing 1906 point is already approximate at Sokoto with a 30km uncertainty ring. | Keep uncertainty. This research did not independently fix Satiru's location or verify Burmi's exact site/day; create neither a new precise pin nor pursuit path. |
| `civil-war` scenes `crisis`, `war`, `blockade`, `end` | Existing dated events, estimate ranges and no-front-lines method are already present. | Enrich source provenance with W1/W2/W3. Compare each local date and each population/cause/period in death estimates. A total-war-death estimate is not interchangeable with a famine-death estimate. |
| `civil-war/uli` | Existing point is at the town, explicitly not the airstrip. W2 p.141 supplies a relief connection lead. | Keep approximate. Verify airfield location, organisations, operating dates and flight records before mapping routes; do not turn a town coordinate into an exact runway. |
| Proposed 1966 displacement connection | W2 selected passages support northern violence and refugee return. | A schematic origin–destination relation may be researchable; exact trains, routes, passenger counts and local incident dates need case-level evidence. Attribute perpetrators specifically, never collectively to an ethnicity. |

## Representation rules remain in force

Points for dated sites; lines for documented relationships; polygons only for documented legal/administrative extents at stated dates. Do not interpolate civil-war fronts, project modern ethnic boundaries backward, infer control of all countryside from a captured city or draw precise slave/caravan routes from a general narrative. A schematic connection is a relationship, not a travelled GPS path.

Maintain separate `status`, `disputed`, evidence, source and location-precision fields in any future chapter additions. Keep unknowns explicit. The user's adult documentary brief calls for honest treatment of difficult history; it does not require changing the map's calm handling of atrocity, famine, displacement and enslavement.

## Production findings useful to the map project

The city-first direction works: broad views, gates with differing forms/heights, market streets, distant riders and palace geography. The failed ascent and palace morph show why the native scene should control formation and topology. Export a stable start/end view and a camera path; use generated atmosphere selectively. A new kingdom needs new researched reference forms rather than a reskin of Kano.

Please carry the series direction into later website and map proposals, and reconcile the evidence items above in a separate scoped stage. This documentation PR neither merges changes nor launches the site.
