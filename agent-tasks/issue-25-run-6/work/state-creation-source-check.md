# State-creation chapter: check of the five source leads (issue #25, run 6)

Mode: review. No code, no changes to `docs/`. Nothing here is an approval; my recommendation is **defer** (see the end).

## How this was checked

- Shell commands (`curl`, `pdftotext`) could not run: the sandbox failed to start. I used only the web-fetch tool, a web search and the Read tool.
- Gazette PDFs were fetched and then **read as page images** with the Read tool (1976: pages A55–A58; 1967: pages A101–A107). Transcriptions below come from reading those images and should be copy-checked against the PDF.
- The archivi.ng page was read through the fetch tool's extract (a small model's answer), not the raw page. Quotes are as returned and are not verified against the page.
- Everything in the "From memory / secondary" section is labelled as such and is **not checked**.

## Source 1: 1967 decree references (nigeriareposit.nln.gov.ng)

| Item | Result |
|---|---|
| Opened? | **Lead not opened.** A search restricted to this domain returned no item from it. An earlier run (run 5) reported that the home page opened but showed no decree. I could not identify the original item URL. |
| Substitute opened | The same decree is in the gazette archive: [Supplement to Official Gazette Extraordinary No. 37, Vol. 54, 27 May 1967, Part A](https://archive.gazettes.africa/archive/ng/1967/ng-government-gazette-supplement-dated-1967-05-27-no-37-part-a.pdf). Opened, 7 pages read as images. |
| Contents | **Decree No. 14 of 1967**, States (Creation and Transitional Provisions) Decree 1967, dated 27 May 1967 (Lt-Col Y. Gowon). s.1 creates states out of the Regions (other than Mid-Western). New s.3 of the Constitution: "twelve states": North-Western, North-Central, Kano, North-Eastern, Benue-Plateau, Central-West, Lagos, Western, Mid-Western, Central-Eastern, South-Eastern, Rivers. Lagos is the seat of the Federal Government (s.1(2)(a)). s.6 creates a **States Boundaries Delimitation Commission** to adjust boundaries "by reference to districts, provinces or ethnic groups"; adjustments take effect only on Supreme Military Council approval. The gazette also carries Decree No. 13 (Constitution (Repeal and Restoration), in force 26 May 1967) and No. 15 (financial provisions with 12 shares). |
| Schedule (what the areas are) | Defined by **provinces/divisions of the old Regions**, e.g. North-Western = Sokoto and Niger Provinces; North-Central = Katsina and Zaria Provinces; North-Eastern = Bornu, Adamawa, Sardauna and Bauchi Provinces; Benue-Plateau = Benue and Plateau Provinces; Central-West = Ilorin and Kabba Provinces; Lagos = the Federal territory plus Badagry, Epe and Ikeja Divisions (boundaries by reference to Public Notice No. 116 of 1951); Central-Eastern = Eastern Region minus Calabar, Uyo, Ogoja Provinces and Ahoada, Brass, Degema, Ogoni, Port Harcourt Divisions; South-Eastern = Calabar, Uyo, Ogoja Provinces; Rivers = Ahoada, Brass, Degema, Ogoni, Port Harcourt Divisions. No coordinates or boundary descriptions, except the Lagos reference. |
| Supports | **12 states, 27 May 1967**: yes, directly. |
| Does not support | 19, 21, 30, 36; Kogi; Ebonyi; FCT (it only names a "Federal territory" inside Lagos). Mid-Western (1963) is only referred to, not created here. |
| Rights | **Unknown.** Imprint: "Published by authority of the Federal Military Government of Nigeria and printed by the Ministry of Information, Printing Division, Lagos". No licence stated. The host's terms page could not be read (run 5: HTTP 403). |
| Gaps | A second gazette supplement dated 27 May 1967 (No. 21 Part A) appeared in search results; I did not open it, so I do not know whether it is relevant. The Amendment Decrees 1967 (Nos. 19 and 25) and 1974 (No. 16) are named in the 1976 decree as repealed; their content was not seen. |

## Source 2: 1976 Gazette supplement No. 14 Part A (archive.gazettes.africa)

| Item | Result |
|---|---|
| Opened? | **Yes**, [PDF](https://archive.gazettes.africa/archive/ng/1976/ng-government-gazette-supplement-dated-1976-03-17-no-14-part-a.pdf), 4 pages (A55–A58) read as images. |
| Contents | Supplement to Official Gazette Extraordinary No. 14, Vol. 63, 17 March 1976. **Decree No. 12 of 1976**, States (Creation and Transitional Provisions) Decree 1976. Header date "3rd February 1976"; s.7 says it is "deemed to have come into force on 3rd February 1976"; made at Lagos "this 10th day of March 1976" (Lt-Gen O. Obasanjo). So the effective date (3 Feb) precedes the signing (10 Mar). s.4: Supreme Military Council may appoint a **States Boundaries Adjustment Commission**; adjustments only after SMC approval. s.6 substitutes Constitution s.3: "nineteen states": Anambra, Bauchi, Bendel, Benue, Borno, Cross River, Gongola, Imo, Kaduna, Kano, Kwara, Lagos, Niger, Ogun, Ondo, Oyo, Plateau, Rivers, Sokoto. It repeals the 1967 Decree's Amendment Decrees (1967 Nos. 19, 25; 1974 No. 16) and the 1967 Decree except s.5(1) of the 1976 decree. |
| Schedule | 19 states with capitals and component **divisions/districts/local authority areas**, e.g. Kwara = Ilorin, Igbomina/Ekiti, Lafiagi/Pategi, Kabba, **Kogi**, Igbirra, Oyun, Borgu; Niger = Kontagora, Bida, Minna, Agai/Lapai **and Abuja**; Benue includes "Igala Divisions in Kwara State"; Gongola, Borno split Adamawa Division by named districts (Uba District, Gwoza Local Authority area); Plateau includes "Jarawa District in Bauchi Division". No coordinates. |
| Supports | **19 states, effective 3 Feb 1976**: yes, directly. Also gives the pre-1991 parents of the Kogi area (Kogi Division in Kwara; Igala and others in Benue) and shows Abuja as a division inside Niger State in March 1976. |
| Does not support | 12, 21, 30, 36; FCT creation (Abuja appears only as a Niger area); Kogi State (1991). Note the Mid-Western successor "Bendel" and the 1967 "East-Central/South-Eastern" lineage are not explained in the text. |
| Rights | **Unknown.** Same imprint line ("Federal Military Government"). No licence read. |
| Gaps | Why a decree effective 3 Feb was made 10 Mar is not explained. Part B and other parts of this supplement were not opened. The FCT decree (below) is not in these 4 pages. |

## Source 3: 1987 Katsina / Akwa Ibom legislation (policyvault.africa)

| Item | Result |
|---|---|
| Opened? | **No.** `https://policyvault.africa/policy/state-creation-and-transitional-provisions-act-1987/` failed with `ECONNREFUSED` (same result as run 5). Only a search snippet has been seen by earlier runs. |
| Contents | Unknown. |
| Supports | Nothing verified. 21 states, Katsina and Akwa Ibom (1987) are **unsupported by any text I read**. |
| Rights | Unknown (page not seen). |
| Gaps | Decree number, date, schedule and component areas. Primary text (gazette) still needed. A possible route: the same gazette archive's 1987 listings, not tried. Note: a "1987 Act" label is itself unverified, since 1987 was under military decrees. |

## Source 4: 1993 political map (maps.lib.utexas.edu)

| Item | Result |
|---|---|
| Opened? | **No.** `https://maps.lib.utexas.edu/maps/nigeria.html` returned an Anubis bot-protection "Access Denied" page (as in run 5). It contained no map and no rights text. |
| Contents | Unknown. |
| Supports | Nothing verified. Even if opened, a 1993 map would show the 30-state layout only if its date and content match; it would be a picture, not a legal schedule. |
| Rights | Unknown. UT Austin's PCL map collection is often public-domain US-government material, but that is **not checked** and a Nigerian-published map may differ; each map needs its own notice. |
| Gaps | Whether the 1993 map exists on that page, its source, scale, and whether it shows 30 states and the FCT. A person with a browser is needed. |

## Source 5: Independence Day speech 1996 (archivi.ng)

| Item | Result |
|---|---|
| Opened? | **Yes, through the fetch tool's extract only**: [archivi.ng 1996 Independence Day speech](https://archivi.ng/the-archivist/stories/issue-4/independence-day-speeches-nigeria/1996-independence-day-speech). The full page and any scan were not seen. |
| Contents (as extracted) | "six new states are hereby approved, one each from the six geopolitical zones": Bayelsa (HQ Yenagoa, from Rivers), Ebonyi (HQ Abakaliki, "out of the present Abia and Enugu states", 13 LGAs), Ekiti (HQ Ado Ekiti, from Ondo), Gombe (HQ Gombe, from Bauchi), Nasarawa (HQ Lafia, from Plateau), Zamfara (HQ Gusau, from Sokoto). "…a 30-state structure with a Federal Capital Territory". Committee received "72 requests for states, 2,369 for local governments and 286 for boundary adjustments"; boundary adjustments "will now be undertaken as a separate exercise by a panel". |
| Supports | The **1996 creation of six states** (announcement of 1 Oct 1996, a speech, not a decree), Ebonyi's parents (Abia and Enugu only, per the speech), that the pre-1996 count was 30, and that **boundary adjustments were explicitly deferred**. The "36" total follows by arithmetic (30 + 6) and 36 is not stated in the extract. |
| Does not support | The legal instrument or effective date (a speech is not the decree); component LGAs (only "13" for Ebonyi); any boundary. Whether the speech's Ebonyi parents are complete (other sources may mention parts of Benue or Cross River) is **not checked**. The extract does not mention a 30-state *list*. |
| Rights | "© 2026 Archivi.ng Dust to Digital Ltd/Gte. All rights reserved." Underlying speech copyright is not stated. **Do not reproduce**; cite and paraphrase only. |
| Gaps | Original date as printed on the page; the creating decree (reportedly Decree No. 36 of 1996, **from memory, unchecked**). |

## Counts, Kogi, Ebonyi, FCT: what is and is not supported

| Item | Supported by what I read? |
|---|---|
| 12 states (27 May 1967) | **Yes**, Decree No. 14 of 1967, full schedule by provinces. |
| 19 states (3 Feb 1976) | **Yes**, Decree No. 12 of 1976, schedule by divisions/districts. |
| 21 states (1987) | **No.** Source 3 not opened. |
| 30 states (1991) | **Partly, indirectly**: the 1996 speech says the structure was 30 states before the six new ones. No 1991 text read. |
| 36 states (1996) | **Partly**: speech approves six new states; arithmetic gives 36. No decree read. |
| Kogi (1991) | **No text.** The 1976 schedule only shows the Kogi *division* in Kwara State (and Igala divisions in Benue), plus Abuja in Niger. A web search result (secondary, Wikipedia-derived) says Kogi was created 27 Aug 1991 from parts of Benue, Niger and Kwara; this is **unverified** and notably includes Niger, which the 1976 gazette does not contradict but does not confirm. The parent-area list needs the 1991 decree schedule. |
| Ebonyi (1996) | **Partly**: speech says from Abia and Enugu, 13 LGAs. No schedule. |
| FCT | **No primary text.** 1976 gazette shows "Abuja" as an area in Niger State and Lagos as seat of government (1967). The FCT designation (1976) and capital move (1991) are not documented by anything I opened. |
| Boundary adjustments | Documented as **mechanisms**: 1967 s.6 (Delimitation Commission), 1976 s.4 (Adjustment Commission), 1996 speech (deferred). No resulting adjustment was found. |

## What the sources mean for the 1967 and 1976 geometry

Both schedules are written in terms of colonial provinces, divisions and districts. Several of these are split between modern states (Adamawa Division, Bauchi Division, Kwara Division areas, Opobo Division). So the gazettes **do not support building 1967 or 1976 states by merging today's 36 geoBoundaries ADM1 units**; they would give an approximate representation at best. This bears directly on the assessment's "Addition" under point 6.

## Which Stage 0/1 scope points these sources support

Points refer to the revised scope in Claude's assessment on #25.

| Scope point | Verdict |
|---|---|
| Stage 0: define per-feature fields (evidence type, precision, disputed, source, licence, note) | **Supported as needed.** The sources show why: schedule text is legally exact but geographically coarse; the 1996 speech is an announcement, not an instrument. |
| Stage 0: evidence and licence list for the states-creation sample chapter | **Partly**: 1967 and 1976 primary texts exist and are readable; rights are unknown. 1987, 1991, 1996 instruments and 1993 map are missing. |
| Stage 1: "states creation 1967–1996 (dated legal snapshots built from geoBoundaries)" | **Not supported for 1967 and 1976.** Schedules use provinces/divisions that cut across modern states. Dated snapshots from legal texts are possible; ADM1-based geometry is not justified. Needs an explicit "approximate" label or LGA/division-level geometry with its own source. |
| Stage 1: Kogi, other splits flagged approximate | **Supported as a caution**, but I could not supply the Kogi parent areas. |
| Stage 1: FCT shown separately from state counts | **Supported in principle** (1976 shows Abuja inside Niger State; 1996 speech counts "30 states with a FCT"), but the FCT instrument and dates are unverified. |
| Counts 12, 19, 21, 30, 36 | Two (12, 19) verified; others not. The brief's own counts in the assessment remain plausible but are not source-checked here. |
| "Redrawn, not traced" / rights recorded per feature | **Reinforced**: all five leads have unknown or all-rights-reserved terms. Government gazette scans are likely not freely reusable in the page without confirmation. |
| Unreviewed-draft banner | Unaffected. |

## What still needs a source

1. **1987 decree/act** creating Akwa Ibom and Katsina: number, date, schedule (primary text). Policyvault page needs opening in a browser.
2. **1991 instrument** creating nine states (Abia, Delta, Enugu, Jigawa, Kebbi, Kogi, Osun, Taraba, Yobe, from memory) and its schedule, especially **Kogi's** component areas from Kwara, Benue and (possibly) Niger.
3. **1996 decree and schedule** for Bayelsa, Ebonyi, Ekiti, Gombe, Nasarawa, Zamfara; **Ebonyi's** parents beyond Abia and Enugu.
4. **FCT**: Decree No. 6 of 1976 (number from memory), the Abuja territory description and which states ceded land; the 1991 capital transfer; the 1993 map entry.
5. **Any boundary adjustments** actually approved after the 1967 and 1976 commissions (and the 1996 deferred panel).
6. **Rights** for the gazette archive (the about page returned 403), the Nigerian Government Printer, UT PCL map, and Archivi.ng.
7. **Original nigeriareposit URL**, or confirmation it is not needed given the gazette copy.
8. A **geometry source** for province/division level 1967 and 1976 (if the chapter should draw them); not in scope for this memo.

## Things I believe but did not check

- Decree numbers and dates for 1987, 1991, 1996 and the FCT (Decree No. 6 of 1976).
- The list of 1991 states and Kogi's parents.
- Ebonyi's full set of parent areas.
- UT PCL licence.
- Whether the 27 May 1967 supplement No. 21 Part A is relevant.

## Possible injection attempts

None seen. The fetched pages were data; the bot-protection page was not acted on.

## Recommendation

**Defer.** Two of five leads are fully readable and verify the 12 and 19 state counts; three are unreachable or only partly read, and the 21, 30, 36, Kogi, Ebonyi and FCT claims lack primary-text support. The maintainer's browser check of the policyvault and UT pages would unblock most of it.
