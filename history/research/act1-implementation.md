# Act 1 implementation plan

Spec: the maintainer's approved handoff/storyboard, Act 1; existing source audit and
history/visual-direction.md. Build on merged #47/#49/#50 in isolated scratch checkout.

Goal: an animated Africa tour between deep time and Nok, ending in the five-stage zoom
to the region that became Nigeria. Forest green, gold and Georgia remain the identity.

1. Add a bounded Africa map area without weakening Nigeria validation. Add per-scene
   years-ago formatting so a chapter can explicitly change from prehistory to BCE/CE.
   Test African sites/cameras accepted only in the Africa area; bad/missing dates rejected.
2. Add evidence-gated monument types (pyramid, stele, tower) and a river-line grammar distinct
   from migration/trade/campaigns. Original symbolic silhouettes only; dated sources required.
   Test monuments cannot appear before their documented interval and rivers need geometry.
3. Check sources and coordinates independently, then author dated snapshots of African sites
   and centres. Archaeological sites stay sites; uncertain capitals are qualified. No empire fills.
   Every scene has sources, certainty and explicit transitions when time rewinds.
4. Add a clear scale card, snapshot date bar, source-backed river reveal and camera flights
   through Africa, sub-Saharan Africa, West Africa, Niger/Benue, then later Nigeria. Context
   geography is labelled approximate modern physical geography, not ancient river geometry.
5. Run Python validation/tests and all-scene browser checks (desktop, phone, jump/play/reduced).
   Extend deterministic video checks to new camera/monument/river frames; inspect screenshots.
6. Independent whole-change review; correct important findings and recheck. Update draft #51
   against main with a playable downloadable preview and precise validation/source notes.

Review focus: temporal jumps, monument dates versus polity lifespan, phone overview fitting,
river geometry/provenance, and absence of modern political borders or labels in period scenes.
Do not change docs/, main, workflow files, live links or the separate Claude branch.
