# Weekly data update and human approval: proposal

**Nothing in `update.yml` has been changed.** This is a proposal for you to decide.

## What `update.yml` does today

- Runs every Monday at 06:00 UTC, and on demand from the Actions tab.
- Spends one UCDP request to see whether the next monthly GED Candidate
  release exists (`update_candidates.py`).
- If it does: appends the version to `CANDIDATE_VERSIONS` in `settings.py`,
  downloads it, runs `clean_events.py` and `publish.py` (which refuses to write
  the page if the token is in it, UCDP credit or version is missing, or
  preliminary data is unlabelled), then **commits `settings.py` and
  `docs/index.html` straight to `main` as github-actions[bot]** and asks GitHub
  Pages to rebuild.
- It did exactly this this morning: commit `d996be0` "Add GED Candidate 26.0.9"
  (26 Oct 2026, 06:39 UTC) went live without anyone looking at it.

## How it relates to the new rule

The agent workflow is built so that nothing reaches `main` or the live site
without your merge. `update.yml` is the one path that does: no AI is involved,
but new data goes public unreviewed. It does not interact with the agent jobs
otherwise (pushes made with `GITHUB_TOKEN` start no other workflows, and the
agents may not touch `docs/` or `.github/`).

It also blocks one safeguard: a ruleset on `main` requiring pull requests would
make "nothing pushes to main" a GitHub rule, but would also make this workflow's
direct push fail. I have not verified whether GitHub's built-in Actions token can
be listed as a ruleset bypass actor, so I would not rely on that.

## Option A: keep it as a defined exception

Keep direct publishing, but write the exception down and narrow it:

- It may only change `settings.py` (the `CANDIDATE_VERSIONS` line) and
  `docs/index.html`, and only after `publish.py`'s checks pass.
- Add a guard step that fails if anything else is staged:

  ```yaml
  - name: Only the expected files may change
    if: steps.check.outputs.new_versions != ''
    run: |
      unexpected=$(git status --porcelain | awk '{print $2}' | grep -vxE 'settings\.py|docs/index\.html' || true)
      if [ -n "$unexpected" ]; then echo "Unexpected changes: $unexpected"; exit 1; fi
  ```
- No ruleset requiring PRs on `main` (or one with a bypass that you confirm works).

Data stays fresh within a week of UCDP's release; the cost is that each month's
preliminary data is published before you have seen it.

## Option B (my recommendation): route updates through a pull request

The same workflow, but it ends by opening a pull request instead of pushing:

- Branch `data/ged-<version>`, a PR titled "Add GED Candidate <version>" with a
  short summary (events added, preliminary count, the `publish.py` check result).
- You merge it from the GitHub app; your merge is a normal push, so Pages
  rebuilds on its own and the `pages/builds` call is no longer needed.
- If a PR for that version is already open, the next Monday's run does nothing
  (otherwise it would find the same release again, because `settings.py` on
  `main` would not have it yet).
- Needs the same "Allow GitHub Actions to create … pull requests" setting as
  the agent workflow, and permissions `contents: write` and `pull-requests: write`
  instead of `pages: write`.
- Then a ruleset on `main` requiring pull requests (with you as bypass) protects
  everything, agents and data alike.

The cost is a monthly tap from you, and the map is only as fresh as your
merge. In exchange, everything public has passed through you, which is the
principle you set for the agents.

If you choose B, I will prepare it as a separate pull request so the change to
publishing is reviewed on its own.
