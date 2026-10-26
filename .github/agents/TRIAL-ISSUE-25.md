# Trial plan: issue #25 in review-only mode

The first live run tests the workflow on real work without any code or site
changes: an independent check of the source leads Codex found for the Nigeria
history page.

## Before the trial

1. The setup pull request is merged and the one-time setup in
   [SETUP.md](SETUP.md) is done (both secrets added; PR creation allowed).
2. Optional, to keep the first run short and cheap: start with `rounds=1`, then
   repeat with the full three rounds once it works.

## The comment to post on issue #25

```
/agent review rounds=1
Scope: independently check the five source leads Codex found for the state-creation
chapter (1967 decree references at nigeriareposit.nln.gov.ng, the 1976 Gazette
supplement no. 14 part A at archive.gazettes.africa, the 1987 Katsina/Akwa Ibom
legislation at policyvault.africa, the 1993 political map at maps.lib.utexas.edu,
and the archived 1996 Independence Day speech at archivi.ng). For each: whether it
can be opened, what it actually contains (decree numbers, dates, schedules of
states and their boundaries or component areas), whether it supports the 12, 19,
21, 30 and 36 state counts and the FCT, and its reuse rights. Pay particular
attention to Kogi, Ebonyi, the FCT and any boundary adjustment. Also say which
of the revised Stage 0/1 scope points in Claude's assessment on this issue
these sources do or do not support.
Out of scope: building the history page, any code, any change to docs/ or the
live site, drawing or tracing boundaries.
Expected output: one Markdown memo in the task's work/ folder with a table per
source (opened? contents, dates, what it supports, rights, gaps) and a list of
what still needs a source.
```

## What to look for

| Check | Where |
|---|---|
| The run started only from your comment, and an acknowledgement appeared on #25 | Issue #25, Actions tab |
| A branch `agent/issue-25-run-N` and a draft PR exist; only `agent-tasks/…/work/` and `…/record/` changed | The draft PR's Files tab |
| Codex's findings are numbered and name the commit they reviewed; that commit shows the `agent/codex-review` status | PR comments, commit page |
| Claude answered every open finding with agree / partly agree / disagree and evidence | PR comments |
| The final report separates checks the workflow ran from agents' claims, lists unverified claims, source and licensing gaps, and usage | Issue #25 and the PR |
| Sources that could not be retrieved are reported as not opened, not filled in from memory | The memo and the report |
| `/agent stop` on a second short run cancels it and labels the issue | Issue #25 |

## Afterwards

- If it works: run again with three rounds, then decide on the memo itself
  (merge the PR to keep it, or close it).
- If a stage fails: the run log names the step. The likely first-run problems
  are listed under "Needs a live run to confirm" in SETUP.md. Fixes go in a
  follow-up pull request; nothing on `main` or the live site is affected by a
  failed task.
- Remove `agent:stop` and `agent:awaiting-decision` labels from #25 when done.
