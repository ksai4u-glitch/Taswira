# Claude + Codex task workflow: setup and use

This lets you authorize a task once on GitHub and come back to one final report.
Claude drafts, Codex reviews independently, Claude answers each finding, Codex
checks again, for at most three review rounds. Everything they produce is kept
on GitHub: a task branch, a draft pull request, comments, and JSON/Markdown
records under `agent-tasks/<task>/record/`.

> **Status: working for one-round review tasks** (26 Oct 2026, trial runs 6-8 on
> issue #25; see "What has been verified" below). Three-round runs, implement
> mode and `/agent stop` have not been tried live yet.

## How it works

```
you: /agent review   (comment on an issue, with a brief)
 └─ Agent task run (one run, stages chained with `needs:`, nothing relies on bot comments)
     authorize ─ checks you are a listed maintainer with admin/maintain rights,
     │            saves your brief as the task record, creates branch agent/issue-N-run-M
     Claude draft ─ read-only GitHub token; output leaves as a patch artifact
     publish ─ no AI: checks the patch's paths, commits to the task branch, opens a draft PR
     Codex review 1 ─ reads the exact commit, read-only files with web access, returns numbered findings (JSON)
     publish ─ records the review, marks that commit with status agent/codex-review
     Claude answers 1 ─ agree / partly agree / disagree per finding, with evidence; may correct
     publish ─ checks and commits
     Codex review 2 ─ checks the answers and the revised commit … (round 3 the same)
     checks ─ the workflow's own checks (compile, tests, protected paths, preview build)
     final report ─ posted on the issue and the PR, committed as FINAL-REPORT.md
```

- **Review-only vs implementation.** `/agent review` lets Claude write only
  under `agent-tasks/<task>/work/`. `/agent implement` lets it change code on the
  task branch, but never `.github/`, `docs/` (the live site), `AGENTS.md`,
  `CLAUDE.md`, `.env` or `.gitignore`. The publish job enforces this with
  `git apply --numstat` and rejects the whole patch if any path is outside.
- **Only you can start it.** The command must come from a login listed in the
  repository variable `AGENT_MAINTAINERS` (default: the repository owner) who
  also has admin or maintain permission. Anyone else's `/agent` comment is
  ignored silently. Tasks start from issues, not pull requests.
- **Agents never merge, push to `main` or deploy.** Agent jobs get read-only
  GitHub tokens. Only the publish jobs (no AI, no AI keys) can write, and they
  refuse any branch not starting with `agent/`. No job approves pull requests.
- **Disagreements stop, they are not forced.** If Claude disagrees with a
  finding and Codex still keeps it open in the next round, it is marked
  "unresolved disagreement" and goes into the final report with both positions.
  The loop stops when nothing actionable is left or the round limit is reached.
  In the last round Claude may only answer in writing.
- **Exact commits.** Each Codex review records the commit it checked and puts a
  commit status on it; after Claude changes anything, the next round reviews the
  new commit.
- **Untrusted content.** The repository is public. The issue thread is saved
  as a snapshot that the agents are told to treat as data; only your brief is an
  instruction. Untrusted text is never pasted into shell scripts. Claude's shell
  commands run with secrets stripped from their environment
  (`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`); Codex runs under codex-action's
  `drop-sudo` strategy with a permission profile that makes files read-only
  but allows outbound network, so it can re-open the sources it checks.

## Limits

| Stage | Time limit | Usage limit |
|---|---|---|
| Claude draft | 40 min | 60 turns, `--max-budget-usd 5` |
| Claude answer (per round) | 30 min | 40 turns, `--max-budget-usd 3` |
| Codex review (per round) | 25 min | codex-action has no turn or cost limit: use a budget on the OpenAI project |
| Publish, checks, report | 10 / 15 / 10 min | none (no AI) |
| Rounds | 3 maximum (`rounds=1` or `2` to lower) | |

Worst case for a full three-round task is about five hours of wall-clock time,
but most tasks should stop earlier. The turn and budget numbers can be changed
with repository variables (below). With a Claude subscription token,
`--max-budget-usd` caps Claude Code's own cost estimate; what you actually use
comes out of your plan's limits.

## Starting, stopping, deciding

Start (comment on an issue; the first line is the command, the rest is the brief):

```
/agent review
Scope: …
Out of scope: …
Expected output: …
```

`/agent implement` for code changes, and `rounds=1`, `rounds=2` or `rounds=3`
after the command to limit rounds (for example `/agent review rounds=2`). You can
also use Actions → Agent task → Run workflow.

Stop:

- Comment `/agent stop` on the issue. It adds the `agent:stop` label (every
  stage checks it before starting) and cancels the running task. Remove the
  label before starting a new task on that issue.
- Or press **Cancel workflow** on the run (works in the GitHub mobile app).
- Kill switch for everything: repository variable `AGENT_AUTOMATION` = `off`.
- To remove it entirely: disable the "Agent task" workflow in the Actions tab.

Decide: the final report recommends approve, defer or reject. That is the
workflow's summary, not an approval, and Codex's or Claude's "approve" is only
advice. You approve by merging the pull request yourself, defer by leaving it
open, and reject by closing it.

## One-time setup

All of this is done in the GitHub website or app, or in PowerShell on your
laptop. **Never paste a key into chat, an issue or a comment.** Secrets go only
into Settings → Secrets and variables → Actions.

1. **Claude credential (choose one).**
   - Your Claude Pro plan: in PowerShell run `claude setup-token`, sign in, and
     copy the token it prints. Add it as the repository secret
     `CLAUDE_CODE_OAUTH_TOKEN`. Usage counts against your Pro limits, the
     same pool as your normal Claude use.
   - Or an Anthropic API key from console.anthropic.com as the secret
     `ANTHROPIC_API_KEY`, billed per token. Set a spend limit in the Console.
   - Set only one of the two.
   - The Claude GitHub App is **not needed**: the workflow passes GitHub's own
     short-lived token to the action. If you want the app anyway (for `@claude`
     mentions), `/install-github-app` in the CLI is only a shortcut; you can
     install it from https://github.com/apps/claude instead.
2. **Codex credential.** codex-action needs an OpenAI API key; it does not
   use your ChatGPT plan. Create a project at platform.openai.com, give it a
   monthly budget limit, create a key in that project, and add it as the secret
   `OPENAI_API_KEY`. Billing is pay-as-you-go API usage, separate from any
   ChatGPT subscription. (The Codex GitHub bot that reviews PRs today uses your
   ChatGPT plan, but it cannot be chained into these stages, so this workflow does
   not use it.)
3. **Allow the workflow to open draft PRs.** Settings → Actions → General →
   Workflow permissions → tick "Allow GitHub Actions to create and approve pull
   requests". The workflow only creates drafts; it never approves. If you leave
   this off, tasks still run and post to the issue instead of a PR.
4. **Merge the setup pull request.** Comment-triggered workflows only run from
   the default branch, so nothing works until this is on `main`.
5. **Optional repository variables** (Settings → Secrets and variables →
   Actions → Variables):
   - `AGENT_MAINTAINERS`: comma-separated logins allowed to start tasks
     (default: `ksai4u-glitch`).
   - `AGENT_AUTOMATION`: `off` disables every task.
   - `AGENT_CLAUDE_MODEL`, `AGENT_CODEX_MODEL`, `AGENT_CODEX_EFFORT`: pick models
     (default: each tool's own default).
   - `AGENT_CLAUDE_WORK_TURNS`, `AGENT_CLAUDE_RESPOND_TURNS`,
     `AGENT_CLAUDE_WORK_BUDGET_USD`, `AGENT_CLAUDE_RESPOND_BUDGET_USD`.
6. **Recommended: protect `main`.** Settings → Rules → Rulesets → New branch
   ruleset for `main`: require a pull request before merging and block force
   pushes, with yourself as a bypass actor. This makes "agents never push to
   main" a GitHub rule rather than only a workflow rule. The weekly data update
   now opens a pull request too ([UPDATE-POLICY.md](UPDATE-POLICY.md)), so the
   ruleset does not block it.

GitHub Actions minutes are free for this public repository on GitHub-hosted
runners.

## What has been verified

Checked without credentials, before the setup pull request:

- The helper script `scripts/agent_task.py` has unit tests
  (`python3 -m unittest discover -s .github/agents/tests`): authorization
  refusals, rounds, path rules (including a real `git apply` patch), the
  stop/continue decision, unresolved disagreements, unusable Codex output, the
  final report and usage parsing.
- A local simulation ran the real `run:` blocks from the workflow files
  against a throwaway git repository: authorize and branch creation, a Claude
  patch accepted, a Codex review recorded, a Claude patch outside the allowed
  paths rejected, and the final report.
- Every workflow parses as YAML; job dependencies, step ids, reusable-workflow
  inputs, secrets and permissions were cross-checked by a script, and every
  `run:` block passes `bash -n`. `actionlint` could not be installed here, so it
  has **not** been run.
- The action inputs used were read from the action repositories on 26 Oct 2026:
  `anthropics/claude-code-action` v1.0.262 and `openai/codex-action` v1.13, both
  pinned by commit.

Confirmed by live runs on issue #25 (26 Oct 2026, review mode, `rounds=1`):

- Both credentials authenticate; the actions accept the inputs as written
  (`--json-schema`, `--max-budget-usd`, Codex `-c web_search="live"`, the
  `review-web` permission profile with an output schema).
- Claude's structured output and usage arrive through the action's outputs
  (about $0.45 to $0.65 for a draft, $0.10 to $0.15 for an answer round).
- Claude reads PDFs (as page images) and its shell sandbox runs `curl`; Codex
  re-opens web sources.
- Draft PR creation, comments, commit statuses, and the chain authorize → Claude
  → publish → Codex → publish → Claude → publish → checks → final report.
- Earlier runs found and fixed: string job outputs into number inputs, apt
  mirror failures, bubblewrap/socat and Ubuntu's user-namespace restriction for
  Claude's sandbox, a GitHub 502 being read as "stop", Codex's `--search`
  flag, and Codex having no network under `:read-only`.

Not yet tried live:

- Three rounds (Claude editing in rounds 1-2, then written answers only).
- Implement mode, including the patch path check rejecting a real patch.
- `/agent stop` cancelling a running task, and the `agent:awaiting-decision`
  label.
