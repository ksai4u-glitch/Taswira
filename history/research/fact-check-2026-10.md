# History fact-check, October 2026

Scope: every feature, scene and emblem in `history/chapters/{deep,africa,nok,hausa,states,key}.json`
and `history/emblems.json`, checked against the sources cited in `history/sources.json`.

How it was checked (31 Oct 2026). The `checked` note on each source in `sources.json` records what
an earlier pass read. Each claim was compared with that note. Claims that looked doubtful were
searched for on the web. **Limitation:** from this build machine, Wikipedia, ThisDay and PressReader
could not be opened directly (DNS blocked), so new checks rely on web-search summaries and Wikipedia
mirrors. Each item below says whether that applies.

Status key: **Fixed** = changed in this pull request; **For Saifu** = a judgement call, left as it
is; **OK** = checked, no change.

## Fixed in this pull request

| Chapter | Id | What it said | What the sources say | Fix |
| --- | --- | --- | --- | --- |
| states | scene `1991` | "nine more states were created: Abia, Delta, **Edo**, Jigawa, Kebbi, Kogi, Osun, Taraba and Yobe" | The nine states usually listed for 27 Aug 1991 are Abia, **Enugu**, Delta, Jigawa, Kebbi, Kogi, Osun, Taraba and Yobe (ThisDay 2019, Jigawa at 28; Nigerian Flight Deck). The chapter's own 1991 snapshot already shows Enugu split from Anambra, so the text and the map disagreed. The ThisDay 2023 article cited lists Edo instead, because Bendel's remainder was renamed Edo. | Enugu put in the list instead of Edo. The text now notes that some lists count Edo as new. Added source `thisday-2019-jigawa`, labelled as seen only in a search summary. |
| key | `kano-tribute` | "Bornu was recognised as Kano's overlord **and paid tribute**." | Kano paid tribute to Bornu (`wiki-bornu`, `wiki-hausa`, the Kano Chronicle on Burja). The link's arrow also points to Bornu as overlord. The sentence read as if Bornu paid. | "Kano recognised Bornu as its overlord and paid it tribute." |

## For Saifu (judgement calls, not changed)

| Chapter | Id | What it says | What the sources say | Proposal |
| --- | --- | --- | --- | --- |
| key, hausa | `ngazargamu`, `bornu` | Ngazargamu ruins at 13.083 N, 12.367 E, "near Geidam", "in the fork of two rivers" | Matches Wikipedia's coordinate (13°05′N 12°22′E, confirmed on mirrors). But Geidam is at about 12.89 N, 11.93 E, so that point is about 50 km east of Geidam, and one mirror gives 13.047 N, 12.228 E. Wikipedia's "near Geidam, in the fork of the Komadugu Gana and Yobe" may not agree with its own coordinate. | Keep `approx`, but compare it with an archaeological source (for example Gronenborn's or Hambolu's work on Gambaru and Birni Ngazargamu) before treating it as the ruin's location. You could add `uncertainty_km` (about 25) until then. |
| key | `zazzau-emirate`, scene `sokoto` | "Zaria … was captured by the Fulani in 1805" (status `firm`) | Search results give 1804 (the ruler's submission and the first capture), 1805 (Wikipedia, Zaria) and December 1808 (Wikipedia, Kingdom of Zazzau; Britannica, a Fulani ruler from 1808). `wiki-sokoto`'s check note does not mention Zaria. | `firm` describes the place, which is right. The date could take a `disputed` note in the scene ("1804 to 1808 in different sources"), or the text could say "by 1808". |
| key | `conquest-1903` | "British forces took Zaria in 1901" | Zaria was not stormed. After the Kontagora campaign (1901) a British garrison stayed outside Zaria and a Resident was posted. The emir was deposed in autumn 1902 (1911 Britannica). The stop is already marked `approximate`. | You could say "British troops were garrisoned at Zaria from 1901" instead of "took". |
| key | scene `sokoto` | Kano captured 1807 | `wiki-sokoto` says 1807. Other accounts give 1805 or 1806 for the first fall of Kano. | No change. A `disputed` note would be optional. |
| nok | scene `rediscovery` | "When German researchers began looking for Nok sites from 1989, most of the ones they found had already been looted." | Wikipedia (via mirrors) says that in 1989 Frankfurt researchers were working in the **Chad Basin** (with Maiduguri), and only later found Nok sites, most of them looted. Systematic Nok fieldwork began in 2005 and the DFG project in 2009. "Began looking for Nok sites from 1989" may overstate it. | Reword to "German researchers working in Nigeria from 1989 later found that most Nok sites had already been looted", after re-reading the Nok article. |
| nok | `nok-village` | First terracotta found 1928, about 7 m deep in a tin mine | Confirmed (24 ft / 7 m, found near Nok village by the mine's co-owner, Col. Dent Young). Accounts of the 1943 find differ: in one, a clerk used a head as a scarecrow; in another, the Geological Survey reported a head from the Jema'a area. | OK as written ("a second head, found nearby"). Note: "nearby" is not certain in every account. |
| deep | `intro` | "everything since the first Nok farmers would fit into its last half-second" | 1500 BCE to 2026 is about 3,526 years. 3,526 ÷ 600 million × 86,400 s ≈ 0.51 s, just over half a second. | You could say "into about its last half-second". Minor. |
| deep | `enugu-coal`, scene `coal` | Coal "first shipped to Britain by 1914" | Coal was found in 1909 and the first mine (Udi) opened in 1915. A first shipment to Britain "by 1914" appears only in local news and travel sources (and Wikipedia, Enugu State, per `wiki-places-deep`). | The status is about the geology, which is fine. The 1914 shipment claim needs a historical study (for example Brown, *We Were All Slaves*, 2003) before it is relied on. You could drop the date or say "mined from 1915". |
| deep | `mega-chad` | `disputed`: 330,000 vs 400,000 km² | Peer-reviewed estimates cluster at 340,000 to 361,000 km² (Schuster et al.; Leblanc et al., SRTM shoreline at about 325 to 329 m). The figures of 400,000 km² and more are in less formal sources. | Keep `disputed`. The disc of 330,000 km² is a fair conservative choice. |
| states | scene `1991` | "Gongola was renamed Adamawa" | Gongola was split into Adamawa and Taraba. Some lists count Adamawa, as well as Edo, among the 1991 "new" states (hence "11 states" in some accounts). | Wording is defensible: Taraba is listed as new. Left as is. |
| hausa | `gobir` | Birni Lalle 14.433 N, 6.767 E, `disputed`, ring of 80 km | Matches the source. The dispute over the capital's dates is recorded. | OK. |
| key | `aro` scene | Arochukwu taken 28 Dec 1901 | Confirmed (Wikipedia, Anglo-Aro War and Aro Confederacy, via mirrors). Fighting from about 24 Dec; capture on the 28th. | OK. |
| key | `aro` scene | Period "about 1640 to 1901" | The infobox gives 1640. Other accounts say 1690. The source note already says "mid-17th century". | OK. You could write "mid-17th century" in the label. |

## Checked, no issue found

- **deep**: Gondwana assembly (600 to 530 Ma), the start of Pangaea's break-up (CAMP, about 200 Ma),
  Africa and Antarctica parting (180 to 160 Ma), the timing of the South Atlantic rift, the Benue
  Trough (145 to 84 Ma, about 1,000 × 150 km), the line through Abakaliki, Makurdi, Numan and Lake
  Chad, the Niger Delta (Eocene, about 56 Ma; 250 km; 300,000 km²; more than 10 km of sediment),
  the African humid period (14,500 to 5,000 years ago), Lake Chad agro-pastoralism from about
  1800 BCE. All match the source notes.
- **africa**: the coordinates of Jebel Irhoud, Memphis, Meroe, Aksum, Kilwa, Djenné-Djenno,
  Koumbi Saleh, Timbuktu, the Askia tomb and Great Zimbabwe all match the UNESCO and gazetteer
  values recorded. Their dates match too (about 300 ka; about 3100 BCE; 3rd century BCE; stelae
  of the 3rd and 4th centuries CE; from about 250 BCE; 1324; 1495; the Great Enclosure in the
  14th century). The Koumbi Saleh and Tié/Njimi identifications are correctly marked as
  uncertain.
- **nok**: phases (1500, 900 and 400 BCE), site counts (almost 500 sites, 84 excavated, 270
  dates), Kagarko sites, the disputed date of Taruga's iron and the size of its ring,
  Katsina-Ala `disputed`. These match the sources.
- **hausa**: the reign years by Kano Chronicle reckoning (Gijimasu, Yusa, Yaji, Dauda, Burja,
  Yakubu, Rumfa), Rumfa's palace, walls, Kurmi market, kulle, eunuchs, Tara-ta-Kano and kakaki,
  Burja's tribute, camels and 21 towns, Yakubu's Fulani with books and the salt, the eleven-year
  war with Katsina, Leo Africanus (1526, his visit doubted), Kanta (1516), Zaria founded about
  1536, the "seven tasks" of the Hausa states, Murray Last's mid-17th-century first edition.
  All match the sources. The `disputed` fields for Amina, Korau, Songhai and Gobir are well
  supported.
- **key**: Bilma, Kanem (at Mao, ring of 120 km, disputed founding), the salt road
  (Tripoli–Murzuk–Bilma), Ewuare (1440), Benin's reach, Onitsha `disputed`, Bonny, the Igbo
  umunna and Ozo, Sokoto 1809, Gwandu, Kano 3 Feb 1903, Sokoto 15 Mar 1903 (13 Mar dispute
  recorded), Attahiru I (Burmi, 27 Jul 1903, dispute recorded), RNC transfer on 1 Jan 1900 for
  £865,000.
- **states**: the dates of 27 May 1967, 3 Feb 1976, 23 Sep 1987, 27 Aug 1991 and 1 Oct 1996.
  The capital moved in Dec 1991. The Mid-West dispute (1963 or 1964) is recorded. The split
  notes for Kogi, the FCT and Ebonyi are suitably cautious.
- **emblems**: the RNC badge, the 1914 colonial flag, Nana Olomu's flags, the unidentified 1897
  flag, the Benin leopard (from 1550, `approx`), the Yoruba knot, Dagin Arewa (`to-check`), Kanem
  and Bornu (none; Organa noted), Biafra (eleven rays, 30 May 1967) and the 1960 flag
  (Akinkunmi, chosen in 1959). These match the cited sources. The entries marked `to-check`
  (colonial badges, Sokoto, Aro, Dagin Arewa) correctly draw nothing.

## Claims with no source

None found. Every feature, scene and emblem with `tier` flag or symbol cites at least one
source id. Emblems marked `none` or `to-check` (colonial badges, Sokoto) have no sources by
design.

## Could not verify this time

- Anything that needs Wikipedia or ThisDay opened directly. Those hosts are blocked from this
  session, so they were checked only through search summaries and mirrors. Re-open
  `thisday-2019-jigawa` and confirm its list.
- The exact location of Taruga (still given only as "about 60 km south-east of Abuja").
- Whether any of today's Kogi State came from Niger (already marked `disputed`).
