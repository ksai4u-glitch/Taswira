# SDD ledger — plan: history/research/act1-implementation.md

Baseline: merged green source tree plus existing Act 1 audit; 69 tests.
Spec: maintainer-supplied handoff dated 27 October 2026, Act 1 storyboard.
Pre-flight: feature geometry/source records feed the renderer and validator; shared field names
must pass through page_data unchanged. Tests will verify source-to-page preservation.
Ruling: use the existing approved storyboard and green direction as the design; no new
design-selection round is needed. Scope remains the previously authorised next chapter.
Ruling: plans live under history/research because repository instructions prohibit docs/ edits.
Ruling: preserve self-governing archaeological sites rather than giving every tour stop a royal
marker. Qualified regional anchors are preferable to fabricated capital coordinates.

Task 1: complete — bounded Africa area, scene clocks, dated monument and river validation; 74 Python tests pass.
Task 2: complete — 17 sourced scenes / 14 features, 28 new used source records; three evidence inventories.
Task 3: complete — glyph rise, dated cards, mapped Niger reveal and five-stage camera sequence.
Ruling: trade context is narrated without new caravan paths because route geometry is not verified.
Ruling: the progress rail shows scene order, explicitly not proportional years; date/scale changes are narrated.
Final: fixed phone HUD/strip collision with compact tour header and duplicate HUD suppression.
Final: fixed authored-path camera discontinuity by using its last camera as the next capture entrance.
Final: fixed browser-clock zoom triggered by raising minZoom; the cross-scene repeated-frame test failed before and passes after.
Final: authoring imperatives removed from viewer-facing locality notes.
Final: held Africa snapshot years at their authored dates; a live monument no longer inherits
the preceding stop's rolling year. Explicit transition cards carry the time jump instead.
Validation: 74 Python tests; 270 scene/viewport/mode combinations; existing video/playback and
new Africa clock/monument/river/camera/mobile regressions. Standalone preview decoded offline.
Ruling: publish the implemented chapter on a fresh branch from merged main, superseding the
older research-only draft #51. This avoids a feature-branch merge or history rewrite and keeps
the reviewed green baseline intact; the source audit travels with the implementation.
