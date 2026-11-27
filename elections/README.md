# Elections map (draft)

"How Nigeria voted": who won each of the 36 states and the FCT in Nigeria's presidential elections.
This first piece covers 2015, 2019 and 2023. `python build_elections.py` writes a draft preview,
`previews/elections.html` (with a Draft badge and `noindex`). `python build_elections.py --publish`
would write the live page, `docs/elections.html`; it is not linked from the site yet.

- `story.json`: party colours, each election (dates, candidates and the column of the raw table
  that holds their votes, INEC's declared national totals, a headline and a short text), the
  `corrections` made to the raw figures, the `known_gaps` the page admits, the 25% rule and the
  `sources`.
- `raw/`: the state tables as copied, and how they were checked (`raw/README.md`).
- `results.py`: reads the raw tables into votes per state.
- `template.html`: the page (globe that flies down to Nigeria, panel, state card, text version, sources).
- State borders: today's 36 states and the FCT from `history/geo/nga-states-2022.topojson`
  (GRID3 2022 via geoBoundaries, CC BY 4.0).

`python build_elections.py --check` checks that each election has all 37 states, the winner has the
most votes, every source is known, and that the states add up to INEC's national totals (and each
state to its own total) unless `known_gaps` says they do not. Tests: `tests/test_build_elections.py`.

Next pieces (one at a time): 1999, 2003, 2007 and 2011; then 1979, 1983 and the annulled 1993
election (on the 19 states of the time); then the 2027 election when INEC declares it.
