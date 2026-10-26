### Claude: first draft

Checked the five leads. I read the 1976 gazette (Decree No. 12, 19 states) and the 1967 gazette (Decree No. 14, 12 states) page by page as images. The 1996 archivi.ng speech was seen only as a fetch-tool text extract: six new states, Ebonyi from Abia and Enugu, a "30-state structure with a Federal Capital Territory", boundary adjustments deferred. The policyvault page (connection refused) and the UT map page (bot wall) could not be opened. The nigeriareposit home page shows no 1967 decree item. The 21, 30 and 36 counts, Kogi's 1991 creation and the FCT have no primary text read. Both gazette schedules use provinces, divisions and districts, and both decrees set up boundary commissions. The ADM1-based Stage 1 plan is therefore not supported as stated, though I did not compare schedule areas with modern ADM1 units. Reuse rights are unknown for all five sources.

**Files changed**

- `agent-tasks/issue-25-run-8/work/state-creation-source-check.md`

**Checks Claude says it ran** (claims, not verified by the workflow)

- WebFetch of 1976 gazette PDF, then Read of all 4 pages as images: Opened. Decree No. 12 of 1976: 19 states, Schedule by division and district, s.4 Boundaries Adjustment Commission, Kogi in Kwara, Abuja in Niger, no FCT. Dated 3 Feb 1976, made 10 Mar 1976, gazetted 17 Mar 1976.
- WebFetch of 1967 gazette PDF, then Read of pages 3-7 (A103-A107) as images: Opened. Decree No. 14 of 1967: 12 states, province-level Schedule, s.6 Delimitation Commission. Decree No. 15 of 1967 also read. Pages 1-2 not read.
- WebFetch of the archivi.ng 1996 speech: Extract only. Six new states with parents, 30-state structure with an FCT, boundary adjustments deferred, all-rights-reserved footer.
- WebFetch of policyvault.africa 1987 page: Failed: ECONNREFUSED. Not opened.
- WebFetch of maps.lib.utexas.edu/maps/nigeria.html: Anubis Access Denied page. No map content.
- WebFetch of nigeriareposit.nln.gov.ng home page: Opened. No 1967 decree item visible. End User Agreement not read.
- Three web searches (1991 states, FCT, 1987 states): Snippets only, labelled secondary in the memo. 1991 instrument number conflicts: Decree No. 37 vs No. 41.
- Bash and code execution: Not used. No code was run.

**Unverified**

- Gazette transcriptions come from reading page images and were not copy-checked against extracted text.
- 1967 gazette pages 1-2 (Decree 13) were not read.
- 1987 instrument number, date (23 Sept 1987), and parents (Kaduna, Cross River) come from search snippets only.
- 1991 instrument number (Decree No. 37 vs No. 41), date 27 Aug 1991, the nine states and Kogi's parents are from search snippets or memory only.
- FCT creation by Decree No. 6 of 1976, its parent states, and the 12 Dec 1991 capital transfer are from search snippets only.
- The 1996 decree number (No. 36) is from a search snippet only.
- The archivi.ng quotes come from a fetch-tool extract, not from reading the full page.
- Contents, date and licence of the UT 1993 map are not seen.
- Whether any 1967 or 1976 schedule area cuts through a modern ADM1 unit was not compared.
- Whether any boundary adjustment was actually enacted is not established.

_Claude usage: 22 turns, 20 input / 13157 output tokens, estimated $0.51 (1.8 min)._
