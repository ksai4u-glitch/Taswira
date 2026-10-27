# Taswira visual direction — 27 October 2026

Saifu asked to carry the director intro's green feel and typography across the whole
website. This extends the existing approved cinematic direction to the conflict map,
interactive history, transcript and video preview.

Use forest green surfaces (#08120e, #12271e), warm ivory text (#f0eee2), muted sage
secondary text (#b5c4b8), and antique gold (#d4b57a) for navigation and focus.
Use Georgia for the brand, scene/chapter titles and large dates. Keep controls,
sources, table cells and map labels in the existing readable system sans serif.
Light mode uses parchment and dark green, with dark bronze links for contrast.
Conflict categories, severity colours and heat intensity retain their data meaning.

Build on the existing two self-contained templates: no fonts, frameworks or extra
network dependency. Preserve animation, evidence, draft status, attribution and
reduced-motion views. Source-template changes require the maintainer's normal build
and merge to reach the live site; never edit generated docs here.

Implementation and verification:

1. Apply palette and heading typography to map_template.html and history/template.html,
   including canvas geography, overlays, tooltips, popups, controls and transcript.
2. Preserve the restored camera, sampled CSS motion and green serif video opening;
   render a new 1080p60 viewing copy and replace the old preview.
3. Check desktop and phone layouts, dark/light conflict-map controls, history playback,
   reduced motion, exact repeated video seeks, and keyboard navigation.
4. Record the design and motion requirements in the handoff so future changes retain them.
