# Raw results by state

Each file is a "results by state" table copied as text, one state per line, with no changes.
`elections/story.json` says which column holds which candidate; `elections/results.py` reads them.

| File | Copied from | Columns |
|---|---|---|
| `pres-2015-wikipedia.psv` | Wikipedia, "2015 Nigerian presidential election", Results by state (source given: INEC), 27 Nov 2026 | state, then the votes of all 14 candidates (Buhari, Jonathan, then the others) |
| `pres-2019-wikipedia.psv` | Wikipedia, "2019 Nigerian presidential election", Results by state, 27 Nov 2026 | state, Buhari votes/%/25%, Atiku votes/%/25%, four other columns of votes/%, margin, valid votes |
| `pres-2023-wikipedia.tsv` | Wikipedia, "2023 Nigerian presidential election", Results by state, 27 Nov 2026 | state, Tinubu, Atiku, Obi, Kwankwaso, others, valid votes, turnout |

How they were checked:

- 2015 and 2019: the 37 rows add up exactly to the national totals INEC declared (2015: Buhari
  15,424,921, Jonathan 12,853,162, 28,587,564 valid votes; 2019: Buhari 15,191,847, Atiku
  11,262,978, 27,324,583 valid votes), and every row adds up to its own total.
- 2023: the rows do not add up exactly to INEC's declared totals (Tinubu 8,794,726, Atiku 6,984,520,
  Obi 6,101,533, Kwankwaso 1,496,687, 24,025,940 valid votes). After the Yobe correction in
  `story.json` the gap is Tinubu +10,694, Atiku -2,230, Obi -10,516, Kwankwaso -16. Tekedia's list
  of the declarations gives the same figures (apart from its own typing slips), so the gap is in the
  announced state figures, not in the copy. Kwara's row is 40 votes over its total. The page says
  all of this; the next step is to check each state against INEC's result sheets (Form EC8D).
- The per-state Wikipedia articles were not used: several disagree with the main table (Kano gives
  Tinubu 506,412 against 517,341 declared).
