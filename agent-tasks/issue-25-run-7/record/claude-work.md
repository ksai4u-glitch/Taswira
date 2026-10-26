### Claude: first draft

Checked the five leads. I opened the 1967 gazette (Decree No. 14, 12 states) and the 1976 gazette (Decree No. 12, 19 states) as page images and read them in full. The 1996 archivi.ng speech was seen only through a fetch-tool extract. policyvault (connection refused) and the UT map (bot wall) could not be opened. The nigeriareposit home page showed no 1967 decree item. Counts 21, 30 and 36, Kogi's 1991 creation, Ebonyi's decree and the FCT have no primary text read. The 1967 and 1976 schedules list provinces, divisions and districts, and both decrees set up boundary commissions, so the lines were not final. I did not compare the schedules with modern ADM1 units, so that question stays open. Reuse rights are unknown for every source, and the speech page says all rights reserved.

**Files changed**

- `agent-tasks/issue-25-run-7/work/state-creation-source-check.md`

**Checks Claude says it ran** (claims, not verified by the workflow)

- WebFetch of the 1976 gazette PDF, then Read of all 4 pages as images: Opened. Decree No. 12 of 1976, 19 states, schedule by division and district, s.4 boundaries adjustment commission, Kogi division in Kwara, Abuja in Niger.
- WebFetch of the 1967 gazette PDF, then Read of all 7 pages as images: Opened. Decrees 13, 14 and 15 of 27 May 1967. Decree 14 creates 12 states, schedule by province, s.6 delimitation commission.
- WebFetch of the archivi.ng 1996 speech: Extract only: 30-state structure with an FCT, Ebonyi from Abia and Enugu, boundary adjustments deferred, all-rights-reserved footer.
- WebFetch of policyvault.africa 1987 page: ECONNREFUSED. Not opened.
- WebFetch of maps.lib.utexas.edu/maps/nigeria.html (twice): Anubis Access Denied page. Not opened.
- WebFetch of nigeriareposit.nln.gov.ng home page: Opened as an extract. No 1967 decree item found. End User Agreement not read.
- Web searches (nigeriareposit 1967, policyvault 1987, UT 1993 map): Snippets only. Used as secondary leads and labelled as such.
- Bash (listing, local checks): Failed: sandbox could not start (bwrap uid map). Not retried. No scripts run.

**Unverified**

- Gazette transcriptions are from reading page images and need a copy check against the PDFs.
- Why the 1976 decree has commencement 3 Feb, made 10 Mar and gazetted 17 Mar is not explained in the text.
- 1987 decree or Act number, date (23 Sept 1987 from snippets only) and parents (Kaduna, Cross River) from snippets only.
- Nothing opened for the 1991 states or Kogi's creation date and parents.
- The 1996 speech was seen only as a tool extract; the full list of six states is not confirmed.
- Ebonyi's parents beyond Abia and Enugu.
- FCT decree and the capital transfer date: no source opened.
- Contents, date and licence of the UT 1993 map (snippet only).
- Whether any 1967 or 1976 schedule area cuts through a modern ADM1 unit: not compared.
- Whether the 27 May 1967 supplement No. 21 Part A is relevant (not opened).
- Reuse rights for all five sources and for the gazette archive.

_Claude usage: 22 turns, 20 input / 11490 output tokens, estimated $0.45 (1.9 min)._
