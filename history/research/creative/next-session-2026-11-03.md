# Next session (3 Nov 2026, 5pm): plan and Saifu's feedback

## New project-direction handoff (2 Nov)
Read [PROJECT-DIRECTION-2026-11-02.md](PROJECT-DIRECTION-2026-11-02.md) before continuing. Saifu wants one finished website with both maps, a visual landing/highlights experience, and cinematic social animation adapted from the map through Codex + Higgsfield. The handoff records the maintainer's direction, Codex's recommendations, reusable scene/export needs and the proposed Kano flagship. The earlier session snapshot below is retained as originally recorded; PR #69 has since merged.


## Saifu's feedback (2 Nov)
1. **Conflict visuals.** In the conflict map (UCDP) there are bomb and gunfire bursts. Add the same for
   wars on the history page, Oversimplified-style: flashes, clashes, explosions. Not conservative.
2. **Weapons by era** for Hausa, Sokoto and Kanem conflicts (and around migrations): show the weapons
   of the time as clash icons/flashes.
3. **Deeper dive on animation quality** for the whole project; animation matters as much as the
   education.
4. Keep going on the track: next stage after the Civil War.
5. An Instagram trailer: done, `previews/taswira-trailer-instagram.mp4` (1080x1920, 34.5 s, silent).

## Proposed approach to conflict visuals (needs a README rule change, Saifu's call)
- New `battle` effect on dated beats about fighting between armed forces: muzzle flashes, crossed-weapon
  clash icon, smoke, shockwave, and for 20th-century wars shell bursts and tracer lines (reuse the
  conflict map's burst/gunfire look). Oversimplified-style: stylised, not gory.
- **Keep calm only where the victims are civilians**: massacres (Asaba, the 1966 killings), famine,
  enslavement, flight. Battles between forces get the effects; atrocities and hunger stay still.
  Rewrite "Rules for war and violence" in history/README.md to say this, and split `sensitive` into
  `battle` (effects on) and `atrocity` (effects off).
- **Weapons by era** (each needs a source saying that force used it):
  - Kanem-Bornu: cavalry, spears, and Idris Alooma's musketeers and Turkish advisers (16th c.).
  - Hausa cities: cavalry with lances, quilted armour, bows; walls and gates in sieges.
  - Sokoto jihad: cavalry and archers; muskets later; Burmi 1903 vs British Maxim guns.
  - Colonial conquest: Maxim guns, rifles, naval guns (Benin 1897, Lagos 1861 bombardment if sourced).
  - Civil War: artillery, air raids, armoured columns; front-line pushes as dated arrows.
- Clash icons: crossed spears, crossed sabres, musket smoke, cannon flash, Maxim gun burst, shell.

## Animation deep dive: ideas to work through
- **Camera**: more authored camera paths (push-in on each beat's place, pull-back at the end), easing,
  slight parallax of labels; avoid long holds on one framing.
- **Army tokens**: Oversimplified-style coloured blobs/arrows for forces that move along dated stops,
  colour per side, size never implying strength (rule 2), with a clash burst where they meet.
- **Territory pulses**: soft colour wash for a polity's core area at its peak (labelled as schematic),
  fading as it shrinks; never a hard border unless sourced.
- **Day/night and seasons**: a dusk/night grade for night events (the Uli airlift), harmattan haze,
  rainy-season flood shimmer on the Niger.
- **Typography in motion**: animated date cards between beats (big year slam, counter roll), place
  names that write themselves in.
- **Sound**: no audio yet; a music bed and narration would lift the videos most (proof videos are silent).
- **Characters**: Zomo reacts more (points at the place being named, flinches at explosions, sad pose
  for loss) using the existing poses.
- **Transitions**: map wipes/zoom-throughs between chapters instead of cuts; globe-to-map dissolve.
- **Performance**: keep canvas effects batched; test 60 fps on a phone.
- **Videos**: vertical 9:16 export mode in capture_history.cjs (crop the map, bigger captions) so
  Instagram/TikTok clips come straight from the player.

## Next stage on the track
After the Civil War: the states chapter exists (1967 to 1996). Candidates:
- **Stage D: Nigeria since 1970**: the oil boom, military rule and coups (1975, 1983, 1985, 1993),
  FESTAC 77, the capital moving to Abuja (1991), the return to civilian rule (1999), then the
  conflicts the conflict map already covers (Boko Haram from 2009, linking to the UCDP map).
- Or widen Africa: other states' independence wave (Ghana 1957, the 1960 wave).

## State at end of 2 Nov
- `main`: volcanoes/Sahara, Colonial Nigeria (railways, ports), source re-checks, iron-roads video.
- Open: ksai4u-glitch/Taswira#69 (ships arriving, British warship at Lagos 1861, the Civil War chapter).
