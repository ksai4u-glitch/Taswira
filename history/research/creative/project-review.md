# Taswira: creative and technical review of the Act 1 snapshot

27 October 2026. Read-only review of `/workspace/work/taswira-act1`, including its current source changes over HEAD `30bb11a5c514a7551a5536d2d46afbc6e035e537`. This assesses the broader experience Saifu describes; it is not a claim that the narrower Act 1 implementation failed its original storyboard. No repository or GitHub changes were made.

**Recommendation:** keep the evidence engine and green visual identity, but make the next increment a directed city-building sequence with a named guide and a hideable interface. Adding more isolated monument pins will not deliver the requested transformation.

## What I checked

Read the two page templates, `build_history.py`, `capture_history.cjs`, every chapter, the emblem inventory, visual direction, implementation/progress/audit records, and the three regional research inventories. Read the original repository's AGENTS and shared instructions. Loaded the bundled `previews/act1.html` offline in Chromium through Playwright; inspected desktop, phone, and the 1920×1080 Zimbabwe video frame at seven seconds. No browser page errors occurred. Screenshots were inspected locally; the dimensions and observations below are retained as the pre-upgrade baseline.

The browser review used the bundled preview, while code findings below cite the source tree. I did not rerun the full regression suite, render a new MP4, profile a real phone, or independently reopen institutional research sources. Source claims below distinguish the repository's recorded checks from fresh external verification.

## Prioritized findings

### F1 — major product gap: architecture remains an icon reveal, not a city coming to life

**Evidence:** `history/template.html:703–709` defines only `pyramid`, `stele`, and `tower`, each as a small inline SVG. `:747–750` anchors one 76×96 pixel icon at a geographic point. The common rise is a 0.7-second effect (`:157`, `:1561`). The Africa data contains exactly three monument-bearing features. At Zimbabwe seven seconds, the browser reports one monument and two scene layers; the screenshot shows an isolated enclosure/tower badge on a broad southern-Africa map.

**Implication:** the camera travels, but the subject has little internal motion or visual discovery. Enlarging this same badge will preserve the feeling Saifu is rejecting.

**Next concrete change:** create one layered architectural vignette: ground plan traced first, walls growing in staggered sections, buildings lifting from the plan, a distinct craft or civic action, and a camera close-up followed by a geographic pullback. Label it an original schematic whenever it exceeds measured geometry. Use the Game of Thrones opening's *sequence grammar*—map, mechanism, construction, reveal—while making the forms, rhythms and cultural detail Taswira's own.

**Architecture/performance:** extend the existing validated scene data with bounded named layers and timed actions; keep the current Leaflet/SVG/canvas stack. Do not turn every house or stone into a separate Leaflet marker. Use a single local SVG/canvas group per vignette, limit detail by viewport, and derive its pose from scene time so repeatable seeks remain possible. The current live renderer changes layers only on scene changes (`:1216–1226`); retain that property. I have not measured a frame-rate problem in the existing simpler scenes.

### F2 — major story gap: Hausa history is a reference example outside the continuous story

**Evidence:** `build_history.py:50` orders `deep → africa → nok → states → key`; `history/chapters/key.json:3` marks the last chapter as a reference. `history/template.html:2133–2135` and `:2154–2156` deliberately skip reference chapters in continuous playback. The Hausa scene (`key.json:395`) largely explains marker semantics, not the experience of living in a Hausa city. Nok's later archaeology scene reaches 2021, followed by state creation beginning in 1963; there is no authored historical bridge through Hausa, Bornu, Benin, Oyo or the nineteenth century.

**Implication:** adding Hausa decoration to the current Africa tour cannot supply the missing narrative. A viewer who presses Play never reaches the existing Hausa or Sokoto material.

**Next concrete change:** develop an actual regional story chapter after Nok, beginning with one carefully researched Hausa city. Separate dated archaeology, chronicles, and oral traditions on screen. A Daura/Bayajidda story can be compelling as **oral tradition**, with its storyteller and variants identified; do not give the legend an invented archaeological year or make it an explanation of every Hausa community's origins. Keep the map key available as reference.

### F3 — major usability gap: there is no normal viewing mode with hideable history information/navigation

**Evidence:** `history/template.html:85` fixes the side panel at 380px; the phone rules at `:275–300` stack map, panel and controls. The only full-screen treatment is `body.video-mode` (`:327–348`), which removes normal navigation and switches to capture tools. In the actual 1440×900 preview, map = 1060×590.5px; side panel = 380px. On 390×844, map = 390×240px, the header/draft takes 257px and controls take 168.5px; the 178px-tall information panel contains 1031px of scrollable material. The conflict map already has a phone drawer (`map_template.html:214–241`, `:680–688`), but its desktop panel remains fixed at 340px (`:111–114`).

**Next concrete change:** add a persistent accessible “Info / Chapters” toggle, with a map-first viewing mode and a separately openable evidence drawer. Preserve a visible current scene/date, pause and next/previous controls; move the long chapter list, feature detail and source lists behind that toggle. On phones, offer a usable scene list rather than seventeen tiny simultaneously squeezed timeline cells (`history/template.html:2094–2101`). Call `map.invalidateSize` after layout changes; preserve the current scene/time, restore focus to the toggle on close, use `aria-expanded`/`aria-controls`, and make Escape close an overlay. Apply the same user intent to the conflict-map desktop panel without removing attribution or data meaning.

### F4 — major product gap: the narrator currently exists only as text

**Evidence:** `history/template.html:1264–1275` splits scene text into highlighted spans. There is no narrator component, speaker/voice data, or audio track in the inspected templates and chapter schema. The loaded preview has zero audio/video elements. `capture_history.cjs:1–4` explicitly says no audio is added; its encoder uses `-an` (`:60`).

**Next concrete change:** create an explicitly fictional contemporary guide with a small original illustrated character sheet: attentive, explaining, pointing, and neutral/resting. Give the guide an optional entrance at chapter boundaries and a few purposeful cues, rather than continuous bouncing or lip movement. A guide can connect the Sahara, inland waterways and cities without pretending to be an ancient eyewitness or to speak for all African cultures. Commission or review Hausa wording/pronunciation where used. Keep mute, captions, transcript and a “Hide guide” control independent of animation effects. In scenes about enslavement, conquest or loss, the guide should become still or leave the frame; retain the current sensitive-scene restraint.

### F5 — major direction gap: scene timing is reading-driven instead of action-driven

**Evidence:** Africa has 17 scenes and 291 seconds before any chapter lead. The five geographic narrowing scenes take 76 seconds; the Nok rewind adds 15 more. Kanem is a 20-second regional scene with `show: []` (`africa.json:1699–1724`), intentionally avoiding an unverified capital pin. Sub-Saharan Africa is another empty-feature interlude (`:1927–1953`). Live narration highlights and export captions are derived by splitting sentences; export uses equal sentence slots across the first 55% of the duration (`history/template.html:2344–2347`). The fallback scene length is word count ×0.33 +4 (`build_history.py:680–682`). In the inspected Zimbabwe video frame, the large year/title HUD and lower-left tour card repeat information while the central architecture remains tiny.

**Next concrete change:** author beats such as “orient → draw foundations → assemble → reveal human use → hold → depart,” then place narration and camera cues around those actions. Preserve all five geographic scales but let them read as one continuous directed descent rather than five separately introduced text cards. A narrator or qualified regional vignette can make Kanem meaningful without manufacturing a capital coordinate. In video mode, use one title/date hierarchy and reserve most screen area for the subject. Add explicit caption cue times or recorded-voice timing instead of equal sentence slots; this matters particularly when sentence lengths differ.

### F6 — major video-readiness gap: the capture pipeline does not yet represent Act 1 or a narrated film

**Evidence:** `capture_history.cjs:7` hard-codes four shots: Gondwana, South Atlantic, Nok terracottas, Nok iron. None is an Africa scene. The exporter samples a configurable fixed number of seconds from each shot (`:43–56`, `:80–86`), appends a short credit card, and writes a VTT and sources manifest. This is a useful deterministic pilot, but not a complete Act 1 render. `taswira.seek` deliberately clears and rebuilds scene rendering on every sample (`history/template.html:2331–2334`); increasing architectural complexity will increase export work even if live playback is efficient.

**Next concrete change:** use a reviewed shot manifest with scene IDs, in/out points, transition duration and narration/caption assets. Export a complete single-city sequence before extending to the whole continental tour. Keep the existing repeatable seek API, rights/source sidecar and modern-basemap exclusion. Make architecture, guide and camera all seek to the same authored clock; do not use free-running random particles, wall-clock animation or browser speech synthesis as the final export voice. Cache static scene structure during sequential export where practical, then verify repeated nonsequential seeks still match. No claim is made here that the current encoder is broken or that a new framework is needed.

### F7 — minor consistency issue and a prerequisite for cultural detail: source/emblem debt differs sharply between chapters

**Evidence:** the new Africa research correctly qualifies Tié as a probable identification of Njimi and refuses an exact site point without verified coordinates (`history/research/act1-central-south-evidence.json:29–41`; rendered narration `africa.json:1715`). The reference chapter still says Njimi “has never been located” and substitutes Mao (`key.json:29`). Both statements are presented within the same experience. More broadly, `history/emblems.json:77–87` explicitly leaves Dagin Arewa undrawn because its historical age is unverified. Only the Benin leopard currently names a drawing; many emblem records are descriptions or `tier: none`, often based on secondary reference pages. The file already distinguishes symbols from flags and rejects invented Kanem/Sokoto flags.

**Next concrete change:** align the older Kanem entry with the newer qualified evidence, and audit new Hausa architecture, dress, music, motifs and legends at the same feature/scene level as Act 1. Do not interpret an empty emblem slot as a design deficiency to fill with a guessed flag. A clearly branded modern narrator costume/motif has a different role from a historical political symbol, but still needs thoughtful cultural review. Source each building *phase* and location separately; reuse rights for source photographs/maps are not implied by access to their historical facts.

## Three compelling sequences to develop

These are proposals, not claims that their missing research is already complete. Use the existing forest green/ivory/gold identity and Georgia headings. Preserve the dated-source validator, reduced-motion static complete states, transcript, visible uncertainty, source records and sensitive-scene suppression (`history/template.html:255–263`, `:1925–1929`).

### 1. “The earth becomes a city” — a Hausa city as the first hero sequence

Begin above the Sahel with the Niger/Chad geography as orientation. The guide sets the question: what makes a city a city? Descend to one verified site and an explicitly selected period. A hand-drawn ground line becomes a schematic earth wall; gates rise one after another; courtyards, a market and an evidenced civic/religious landmark unfold as separate layers. Cloth/craft detail gives the scene purpose and human scale. The camera makes a restrained orbit within this schematic inset, then pulls back to show separate Hausa cities as separate places.

A brief optional Daura oral-tradition inset can change visual material—illustrated storytelling against a flat background—then explicitly return to dated evidence. Research Kano's wall phases and any mosque, market or dye-pit depiction individually before selecting a date; the existing Chronicle-based approximate wall date does not validate every modern landmark in that scene. Do not use modern Kano's footprint as a fifteenth-century plan, a common Hausa state border, or an undated Arewa emblem as a medieval flag. This is the best sequence for testing whether the requested transformation has actually arrived.

### 2. “Stone remembers the builders” — Great Zimbabwe built in layers

Keep the already selected c.1400 later-phase snapshot. The map descends from southern Africa into a clearly labelled schematic architectural stage. Trace the Great Enclosure's broad form, raise several wall courses in a wave, reveal the narrow passage, then reveal the tower as part of the completed composition. End on the builders' material skill and a quiet pullback to the geographic anchor.

The current repository records construction c.1100–1450 and the enclosure's fourteenth-century attribution, but no separately verified exact tower construction date (`act1-central-south-evidence.json:7–23`). Accordingly the assembly is an explanatory reveal at c.1400, **not a time-lapse claiming a known order of construction**. Do not show the entire later ensemble already standing in 1100, add a royal palace from imagination, invent an abandonment catastrophe, or draw an empire footprint. This is the fastest source-grounded proof of the new architectural grammar because the current art and research already supply a starting point.

### 3. “Water, craft and exchange” — Nok and the Niger as connective tissue

Use the mapped Niger/Benue descent to carry the viewer into the regional narrative, with an explicit rewind to the Nok dates. At the locality inset, millet grows first for the early farming phase; a dated transition brings clay forms and sculpture into view around the later archaeological phase; another transition introduces ironworking in its documented and disputed range. Clay turns, a kiln/forge glow develops, and the guide draws attention to how researchers know these things. Conclude by opening a small evidence view of pottery, plant remains and radiocarbon dates, not a fabricated movement arrow connecting Nok to later peoples.

The present Nok text already separates farming (~1500 BCE), terracottas (~900 BCE), and later ironworking (`history/chapters/nok.json`, scenes `farmers`, `terracottas`, `iron`). Preserve those distinctions. Use original non-sacred schematic objects and label hypothetical workshop layouts; do not copy uncleared museum objects, map ritual placements without evidence, claim a settled reason for Nok's disappearance, or turn looting into an exciting explosion effect. A quiet archaeology ending connects naturally to the source drawer and makes the guide useful.

## Suggested next reviewable increment

Produce one 30–45 second city vignette in the existing player, with a normal-view panel toggle, the guide's three or four purposeful states, timed captions, a reduced-motion complete view, and a deterministic exported clip. Great Zimbabwe is the quickest evidence-supported motion test; a researched Hausa city is the stronger flagship for Saifu's stated cultural goal. Judge that increment on whether the viewer can see construction, distinct local character and a coherent action sequence without reading the sidebar. Extend to more cities only after this single sequence demonstrates the intended quality.

Unverified claims: real-device performance, completed Hausa cultural/linguistic review, clearance of any new art/audio assets, and external historical claims beyond the repository's checked-source records remain unverified by this review.
