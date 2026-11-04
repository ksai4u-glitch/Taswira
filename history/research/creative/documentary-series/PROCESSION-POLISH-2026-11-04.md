# Ancient Kano — native procession polish

This follows the [definitive master polish](MASTER-POLISH-2026-11-03.md) and addresses the owner’s observation that the mounted entourage looked jittery and pasted into the flyover at film 11–14 seconds. No new shot, soundtrack or speech was generated.

## Diagnosis and repair

The existing composite used an independently thresholded difference matte on each frame. Small changes in the mask and the edited plate’s alignment made the party’s edges unstable. The original gate plate is 1080×1920 at 30 fps, conformed to the 24 fps film; the additive horse edit is 704×1248 at 24 fps. Export frame counts alone did not test that integration.

The native repair measures the edited background against the original gate plate, smooths the measured registration trend, and integrates neighboring cutout masks after compensating for their motion. A restrained virtual shutter samples premultiplied colour and alpha along the local motion direction. A small edge-only contribution from the scene softens the pasted boundary. This is local compositing, not a new full-frame city generation or a change to the camera route.

The repaired patch covers exactly 72 frames at 11–14 seconds, easing in and out over six frames. The native RGB patch changes only the union of the old and repaired party masks, with feathering. The full film is then re-encoded for delivery, so compressed video outside that window is not claimed to be bit-identical. The secondary patch is explicitly conformed to 24 fps before overlay to avoid Matroska timebase rounding changing the rider cadence.

Measured motion-compensated mask change fell from 0.22230 to 0.10329, about 53.5%. This measures edge stability, not gait correctness or artistic approval. Raw RGB pixels outside the defined patch support were preserved exactly before the final encode. Low-opacity matte area grows slightly through feathering; no extra riders or architecture are generated. Native processing makes no paid model call and uses zero generation credits.

## Locked material

Arthur’s accepted AAC track is copied without encoding. Its complete decoded waveform must also match, preserving continuous Majestic Hills, the entry at about 4.005 seconds, full Kurmi Market cue at 25.005–25.685, the palace anchor around 31.399, the exact hook at 43.525–50.005, and the final whole-mix fade. There is no new narration edit or speech acceleration.

Sand-drift intro typography, qualified period cards, both supplied logos, crisp Arewa-style credits, integrated road/tower labels, kingdom overview and thunder/lightning remain in the existing timeline. The cleaned closing’s dust-concealed edit at 37.75 seconds remains; rejected closing source 3.75–6.75 is not restored. Narration subtitles remain absent.

## Verification and delivery

`taswira-ancient-kano-procession-polish.mp4` is **59 seconds, 1080×1920, 24 fps**, 37,943,081 bytes. SHA-256: `0e4ba04997cd7a8fdbc28c3a28e54ac7de792d1463bd4a3f7830380d05a38bd8`. Upload returned HTTP 200; the delivery-copy hash matched, confirmation succeeded and the owner result preview was shown.

All 1,416 frames decoded uniquely; complete browser playback presented all 1,416 with a maximum media-time gap of 0.041667 seconds. Exact compressed AAC and decoded float-sample hashes match the accepted master. This preserves its −16.01 LUFS / −1.06 dBTP mix and the measured speech placements. The intro around Arthur’s entrance, patch boundaries, gate occlusion, landmark labels, overview and credits were inspected in actual exported contacts; a separate dense sequence compares eight consecutive procession frames before/after. These are technical/visual checks, not an artistic listening certification.

Outside the local repair, mean half-resolution export SSIM against the accepted master was 0.996812, minimum 0.990032. The intro mean was 0.996876. These record delivery-encode similarity; the original unencoded patch support check is a separate exact RGB test. See [review-artifact.json](review-artifact.json) for the machine-readable record.

## Limits and lesson

Temporal integration can improve boundary flicker, alignment and shutter consistency; it cannot recover native 1080 horse detail or invent anatomically correct gait where the generated source lacks it. The entourage remains illustrative ceremony, not a sourced historical event or evidence of medieval uniform. Proper-name listening and the existing historical/editorial release review remain owner tasks.

For the next episode, inspect additive elements in a dense temporal sequence at the final camera speed before locking the composite. Review cutout edges, hoof contact, silhouettes, shadows and occlusion separately from browser playback. A technically complete encode is not proof of coherent generated motion.

Retained private processing records are `procession_refine.py`, `qc_procession_polish.py`, `diagnostics.json`, `repair-report.json`, a lossless three-second patch, the exported comparison contacts and browser/export reports. No private media URL or binary is stored in this public documentation. No map runtime data or historical claim changes. The separate Taswira map teaser remains next.
