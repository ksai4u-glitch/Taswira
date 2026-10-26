### Claude: answers to Codex round 1

Round limit reached, so no files were edited. I agree with both minor findings and checked each. F1: the memo overstates "FCT unsupported". The 1996 speech does support the FCT's existence by 1996, and the memo itself quotes that passage at lines 105 and 122. What lacks primary support is the creation instrument, designation date, component areas and capital-transfer date. F2: my sandbox fetch of the UT index returned HTTP 200 and the page lists the 1993 map, so the memo's "not opened" is out of date for the index page. The map image itself still has not been inspected.

_Round limit reached: written answers only, no further edits._

| Finding | Position | Evidence | Action |
|---|---|---|---|
| F1 | agree | Memo line 105 and line 122 already quote the speech's '30-state structure with a Federal Capital Territory'. Yet lines 12, 126 and 19 say the FCT is 'not supported' or 'Unsupported by primary text', and line 33 says Source 2 supports nothing for the FCT. The first two are too broad. The accurate claim is that the 1996 speech supports the FCT's existence by 1996. Unsupported by any opened primary … | No edit (round limit). I recommend the maintainer or a later round qualify lines 19 and 126 along those lines. |
| F2 | agree | Memo line 88 says 'Opened? No' and that the 1993 listing could not be confirmed. I ran curl against https://maps.lib.utexas.edu/maps/nigeria.html in this session and got HTTP 200. The HTML contains 'The following maps were produced by the U.S. Central Intelligence Agency, unless otherwise indicated.' It also lists 'Nigeria (Political) 1993' as africa/nigeria_pol93.jpg and africa/nigeria_pol_1993.… | No edit (round limit). I recommend the memo record that the index page is confirmed, with the listing and CIA attribution, while the map image and its rights stay unchecked. |

**Checks Claude says it ran** (claims, not verified by the workflow)

- Read INSTRUCTIONS.md, TASK.md and codex-review-1.json: Done. Two open findings, F1 and F2, both minor. No disputes.
- grep of the memo for FCT wording and reading of the Source 4 section: Confirmed the FCT wording at lines 12, 19, 33, 126 and 134, and the stale 'Opened? No' for the UT source at line 88.
- curl of the UT Nigeria index, with grep for 1993 and CIA: HTTP 200. The page lists the 1993 political map (JPG and PDF) and carries the CIA attribution line.

**Unverified**

- The contents of the UT 1993 political map (state count, FCT depiction) and its item-specific reuse rights.
- I did not re-check the gazette transcriptions, the Archivi.ng speech or the National Repository in this round.
- FCT creation by Decree No. 6 of 1976 and the capital move on 12 Dec 1991 remain secondary-snippet claims.

_Claude usage: 5 turns, 8 input / 2146 output tokens, estimated $0.09 (0.3 min)._
