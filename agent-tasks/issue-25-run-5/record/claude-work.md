### Claude: first draft

Checked the five leads. Two were opened and read: the 1976 gazette (Decree No. 12, 19 states) and, in the same archive, the 27 May 1967 gazette (Decree No. 14, 12 states). The 1996 speech was opened through a fetch extract only. The policyvault (connection refused) and UT map (bot wall) leads could not be opened, and the nigeriareposit item was not found. 21, 30, 36, Kogi, Ebonyi and the FCT lack primary-text support. The 1967 and 1976 schedules use provinces, divisions and districts that cut across present-day states, so building them from geoBoundaries ADM1 is not supported.

**Files changed**

- `agent-tasks/issue-25-run-5/work/state-creation-source-check.md`

**Checks Claude says it ran** (claims, not verified by the workflow)

- Read pages A55-A58 of the 1976 gazette PDF (page images) via the Read tool: Decree No. 12 of 1976; 19 states counted; Kogi division in Kwara; Abuja in Niger; boundary commission in s.4.
- Read pages A101-A107 of the 27 May 1967 gazette PDF (page images): Decree No. 14 of 1967; 12 states and province-level schedule; s.6 boundary commission.
- WebFetch of archivi.ng 1996 speech: Opened; only the tool's extract was seen. Six new states, Ebonyi from Abia and Enugu, '30-state structure with a Federal Capital Territory', boundary adjustments deferred. Footer: all rights reserved.
- WebFetch of policyvault.africa (two URLs): Failed: ECONNREFUSED. Not opened.
- WebFetch of maps.lib.utexas.edu/maps/nigeria.html: Returned an Anubis 'Access Denied' page. Not opened.
- WebFetch of nigeriareposit.nln.gov.ng home page and a site search: Home page opened; no decree item found; one unrelated 1967 trade review.
- WebFetch of gazettes.africa/about for licence terms: HTTP 403. Rights unknown.
- Bash commands (curl, pdftotext): Failed: sandbox could not start. No scripts run.

**Unverified**

- Decree numbers, dates and component areas for 1987, 1991 and 1996 (no primary text read).
- The 1996 speech quotes were seen only in a fetch-tool extract, not the full page.
- Ebonyi's parent areas beyond Abia and Enugu (possible Benue/Cross River parts) are from memory.
- FCT: Decree No. 6 of 4 Feb 1976 and the parent states are from search snippets of secondary sources only.
- The 1991 states list in the memo is from memory.
- Contents of the UT 1993 map and its legend.
- Transcription of the gazette scans is from image reading and needs a copy check.
- The 1976 decree's commencement (3 Feb) versus signing (10 Mar) was read from the scan; reason for the gap not established.

_Claude usage: 29 turns, 26 input / 16046 output tokens, estimated $0.57 (2.4 min)._
