# Ancient Kano Cinematic Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the rejected mounted scenes with coherent native motion and deliver a checked cinematic revision while preserving the owner's accepted narration, city-first direction and credits.

**Architecture:** Reuse the owner-accepted two-rider rigged-motion basis. Extend camera/occlusion coverage, clean the existing plate, build a disciplined varied formation, and finish within the existing 59-second edit. Treat the source plate's geometry as illustrative; reconcile historical/readability issues explicitly rather than silently changing series identity or speech.

**Tech Stack:** Blender 4.3.2/Cycles, OpenCV, NumPy/SciPy, FFmpeg/Pillow; optional local Apache-licensed segmentation for rotoscoping only. No paid generation submission is authorized.

**Spec:** Owner request history, PROCESSION-REJECTION-2026-11-04.md, the delivered four-second motion study, owner's reply “Movement works; refine the cinematic finish”, and CLAUDE-CRITIQUE-RESPONSE-2026-11-04.md.

## Global Constraints

- Native work only; no new image/video/voice/music generation, trial, refill or paid retry.
- Keep Arthur's exact hook and accepted audio timing; no speed/pitch change. A 45-second cut and title rename remain proposals.
- Preserve original supplied Arewa and R logos, sai_fu / Rahzatech Media Production, qualified dates and attribution.
- City-wide emphasis, no talking characters or face close-ups; preserve the requested grand procession and gate hierarchy.
- Original 59-second delivery remains rejected and retained until a checked replacement is uploaded and confirmed.
- Never restore rejected closing source3.75–6.75 or claim one physical uninterrupted take.
- No main merge, live-site change, deployment or social publication. Use the existing documentation PR if still open.

## Review Focus

- Bodies/hooves must retain coherent identity and readable weight-bearing movement at normal speed, not merely pass frame hashes.
- Gate face, roof, parapets and street need true foreground holdouts; no riders standing on roofs or clipped into floating torsos.
- Original incidental gate riders and palace orbiters must not remain as obvious failed animation behind the new formation.
- Landmarks/period cards must remain readable and aligned with actual words after any edit.
- Historical picture correction must distinguish sourced geography, schematic reconstruction and art direction; no unapproved rebrand or voice rewrite.

---

**Checkpoint, 4 November:** camera/formation components and typography exports exist. Native plate cleanup/in-place replacement tests are rejected. A three-image clean-plate proposal is prepared at a live cost-only total of three credits, awaiting separate owner approval. No revised full-film delivery is claimed. See NATIVE-REBUILD-PROGRESS-2026-11-04.md.

### Task1: Full shot camera, masks and clean plate

**Files:** `full_camera.py`, `source_masks.py`, `clean_plate.py`, `full-camera.json`, `plate-clean/` in the isolated native work folder.

**Interfaces:** Consumes the original gate source and owner-accepted rig study. Produces168 camera records at24fps, foreground/cleanup masks at source resolution, and a clean seven-second plate with the original endpoint.

- [x] Extend the existing reconstruction across source0–7s, using static-background keyframes and measured reprojection evidence.
- [ ] Produce gate/roof/street holdouts and separate original-rider masks; inspect dense gate-passage frames.
- [ ] Reconstruct removed riders' ground/shadows using temporally aligned plate content; protect architecture.
- [ ] Verify no new texture boil, mask pop, camera wobble, wrong-depth rider or endpoint change.

### Task2: Formation, styling and native render

**Files:** `full_procession.py`, `formation-manifest.json`, `procession-layers/`.

**Interfaces:** Consumes Task1 camera/holdouts and the accepted fixed horse rig. Produces a native1080 formation pass and seven-second integrated shot.

- [x] Build approximately24 riders as three disciplined columns/eight ranks; movement outward under the inward-flying camera, with coherent spacing and phase variation.
- [ ] Refine woven cloth, tack, coat variation, rider silhouette and warm-light/shadow match; no unverified period-uniform claim.
- [ ] Ensure the gate has formed before the front rank enters; each rider persists to a real occlusion or exit.
- [ ] Inspect normal-speed movement, silhouettes, hoof contact, reins, shadows and architecture across the whole shot; reject failed frames before integration.

### Task3: Palace and cinematic finishing

**Files:** `palace_cleanup.py`, `finish_revision.py`, finishing manifest and actual export contacts.

**Interfaces:** Consumes Task2 shot and existing clean palace/pullback sources; produces a new review candidate with unchanged accepted audio.

- [ ] Repair/clean the palace orbiting riders and preserve the compound/kingdom overview.
- [ ] Replace the flat beige transition with a coherent authored transition or justified match cut; keep the rejected source interval excluded.
- [ ] Improve fog/image hook, phone-size period cards, fully readable integrated landmark names and Taswira CTA.
- [ ] Resolve Dala/compound picture framing against the map; record any remaining historical release blocker. Keep existing series branding and59-second duration unless the owner directs otherwise.

### Task4: Independent review, export and handoff

**Files:** export/QC JSON, current-delivery-state.json, updated GitHub production/source/lessons records.

- [ ] Inspect the actual exported movie and dense critical sequences; obtain one fresh independent whole-result review.
- [ ] Decode every frame, play the complete file in a browser, verify audio identity/sync/loudness/tail, labels/logos/dates and all joins.
- [ ] Fix material findings and verify again. Treat frame counts as playback evidence only.
- [ ] Upload only a checked result with media_upload before delivery copy+PUT, correct Content-Type, HTTP200, confirmation, then show_result.
- [ ] Record actual calls/balance observations without attributing unexplained account movement. Update the existing PR, retain private URLs outside public docs, preserve the separately planned Taswira teaser.
