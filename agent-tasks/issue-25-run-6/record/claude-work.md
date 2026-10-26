### Claude: first draft

Checked the five leads. Two gazette scans (1976 Decree No. 12; 27 May 1967 Decree No. 14) were fetched and read page by page as images. They verify the 12 and 19 state counts, with schedules by province, division and district. The 1996 archivi.ng speech was read only through the fetch tool's extract. It gives six new states, Ebonyi from Abia and Enugu, and a deferral of boundary adjustments. policyvault (connection refused) and the UT map page (bot wall) could not be opened. The nigeriareposit lead was not found. The 21, 30 and 36 counts, Kogi, Ebonyi's full parents and the FCT have no primary-text support. The 1967 and 1976 schedules do not follow modern state lines, so building them from geoBoundaries ADM1 is not supported. This agrees with the finding of the earlier run (issue-25-run-5).

**Files changed**

- `agent-tasks/issue-25-run-6/work/state-creation-source-check.md`

**Checks Claude says it ran** (claims, not verified by the workflow)

- Fetched the 1976 gazette PDF and read pages A55-A58 as images: Decree No. 12 of 1976 read in full: 19 states, Schedule, s.4 Adjustment Commission, Kogi division in Kwara, Abuja in Niger. In force 3 Feb 1976; made 10 Mar 1976.
- Fetched the 27 May 1967 gazette PDF and read pages A101-A107 as images: Decree No. 14 of 1967 read in full: 12 states, province-level schedule, s.6 Delimitation Commission. Decrees 13 and 15 also read.
- WebFetch of the archivi.ng 1996 speech: Opened; only the tool extract was seen. Six new states, Ebonyi from Abia and Enugu, 30-state structure with an FCT, boundary adjustments deferred. Footer: all rights reserved.
- WebFetch of the policyvault.africa 1987 page: Failed with ECONNREFUSED. Not opened.
- WebFetch of maps.lib.utexas.edu/maps/nigeria.html: Anubis Access Denied page. No map content seen.
- Web searches for the nigeriareposit 1967 item and for Kogi 1991: No nigeriareposit item found. Secondary snippets only for Kogi (27 Aug 1991), unverified.
- Bash commands (pdftotext, curl): Not run: the sandbox could not start (socat missing).

**Unverified**

- Decree numbers and dates for the 1987, 1991 and 1996 creations and for the FCT (Decree No. 6 of 1976).
- The list of nine 1991 states and Kogi's parent areas (Kwara, Benue, and possibly Niger).
- Ebonyi's full parent areas beyond Abia and Enugu.
- The 1996 speech quotes, which were seen only in a fetch-tool extract.
- Gazette transcriptions are from reading page images and need a copy check.
- Contents and licence of the UT 1993 map.
- Whether the 27 May 1967 supplement No. 21 Part A is relevant.
- Reuse rights of the gazette archive and the Government Printer.

_Claude usage: 19 turns, 20 input / 11257 output tokens, estimated $0.41 (1.8 min)._
