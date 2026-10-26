"""
Helper for the Claude + Codex task workflow (.github/workflows/agent-*.yml).

Everything that decides something lives here, so it can be tested without
GitHub: who may start a task, which files an agent may change, when the
review loop stops, and what goes into the final report. The workflows only
move files around and call GitHub.

Uses only the Python standard library. Run it with `python3 -I` so nothing
in the checked-out task branch can shadow a standard module.
"""

import argparse
import json
import os
import re
import subprocess
import sys

COMMANDS = {"/agent review": "review", "/agent implement": "implement"}
MAX_ROUNDS = 3
MIN_BRIEF = 20
MAX_BRIEF = 8000
MAX_PATCH_BYTES = 2_000_000
BRANCH_PREFIX = "agent/"
COMMENT_LIMIT = 60_000

# Paths no agent may change in any mode. The workflow, the shared
# instructions and the task records must stay exactly as main (or the
# workflow itself) wrote them, and docs/ is the live site.
DENIED_PREFIXES = (
    ".github/", ".claude/", ".codex/", "docs/", ".env",
)
DENIED_FILES = {
    "AGENTS.md", "CLAUDE.md", "AGENTS.override.md", "CLAUDE.local.md",
    ".gitignore", ".gitattributes", ".gitmodules", ".mcp.json", ".claude.json",
}


# ---------------------------------------------------------------- small utils

def write_output(name, value):
    """Set a step output (multi-line safe)."""
    path = os.environ.get("GITHUB_OUTPUT")
    value = str(value)
    if not path:
        print(f"{name}={value}")
        return
    with open(path, "a", encoding="utf-8") as f:
        if "\n" in value:
            f.write(f"{name}<<__AGENT_EOF__\n{value}\n__AGENT_EOF__\n")
        else:
            f.write(f"{name}={value}\n")


def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def save_text(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def clip(text, limit=COMMENT_LIMIT):
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n…(cut to fit a GitHub comment; the full text is in the task record on the branch)\n"


def one_line(text, limit=300):
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


# -------------------------------------------------------------- authorization

def parse_command(body):
    """Return (mode, rounds, brief) from a '/agent …' comment, or raise ValueError."""
    body = (body or "").replace("\r\n", "\n").strip()
    first, _, rest = body.partition("\n")
    first = first.strip()
    mode = None
    for prefix, name in COMMANDS.items():
        if first == prefix or first.startswith(prefix + " "):
            mode = name
            extra = first[len(prefix):].strip()
            break
    if mode is None:
        raise ValueError("the first line must be '/agent review' or '/agent implement'")
    rounds = MAX_ROUNDS
    if extra:
        m = re.fullmatch(r"rounds\s*=\s*(\d+)", extra)
        if not m:
            raise ValueError(f"unknown option on the command line: {extra!r} (only rounds=1..3)")
        rounds = int(m.group(1))
    if not 1 <= rounds <= MAX_ROUNDS:
        raise ValueError(f"rounds must be between 1 and {MAX_ROUNDS}")
    brief = rest.strip()
    if len(brief) < MIN_BRIEF:
        raise ValueError("write the task brief (scope, out of scope, expected output) under the command line")
    if len(brief) > MAX_BRIEF:
        raise ValueError(f"the brief is longer than {MAX_BRIEF} characters")
    return mode, rounds, brief


def authorize(env):
    """Decide whether this event may start a task. Returns a dict; never raises."""
    def refuse(reason):
        return {"ok": False, "reason": reason}

    if (env.get("AGENT_AUTOMATION") or "on").strip().lower() == "off":
        return refuse("agent automation is switched off (repository variable AGENT_AUTOMATION=off)")

    actor = env.get("ACTOR", "")
    owner = env.get("REPO_OWNER", "")
    allowed = [a.strip().lower() for a in (env.get("AGENT_MAINTAINERS") or owner).split(",") if a.strip()]
    if env.get("ACTOR_TYPE", "User") != "User" or actor.endswith("[bot]"):
        return refuse(f"{actor} is a bot; only maintainers can start tasks")
    if actor.lower() not in allowed:
        return refuse(f"{actor} is not in AGENT_MAINTAINERS")
    if env.get("ACTOR_PERMISSION") not in ("admin", "maintain"):
        return refuse(f"{actor} does not have admin or maintain permission")

    if env.get("ISSUE_IS_PR") == "true":
        return refuse("tasks are started from issues, not pull requests")
    if env.get("ISSUE_STATE", "open") != "open":
        return refuse("the issue is closed")
    labels = [l.lower() for l in json.loads(env.get("ISSUE_LABELS") or "[]")]
    if "agent:stop" in labels:
        return refuse("the issue has the agent:stop label; remove it to allow new tasks")

    try:
        if env.get("EVENT_NAME") == "workflow_dispatch":
            first = f"/agent {env.get('DISPATCH_MODE', '')} rounds={env.get('DISPATCH_ROUNDS') or MAX_ROUNDS}"
            mode, rounds, brief = parse_command(first + "\n" + (env.get("DISPATCH_BRIEF") or ""))
        else:
            mode, rounds, brief = parse_command(env.get("COMMENT_BODY"))
    except ValueError as e:
        return refuse(str(e))

    try:
        issue = int(env.get("ISSUE_NUMBER", ""))
    except ValueError:
        return refuse("no issue number")
    task_id = f"issue-{issue}-run-{env.get('RUN_NUMBER', '0')}"
    return {
        "ok": True,
        "reason": "authorized",
        "mode": mode,
        "max_rounds": rounds,
        "brief": brief,
        "issue": issue,
        "task_id": task_id,
        "task_dir": f"agent-tasks/{task_id}",
        "branch": BRANCH_PREFIX + task_id,
        "authorized_by": actor,
        "authorized_via": env.get("COMMENT_URL") or "workflow_dispatch",
        "authorized_at": env.get("EVENT_TIME", ""),
        "base_sha": env.get("BASE_SHA", ""),
        "run_url": env.get("RUN_URL", ""),
    }


def cmd_authorize(args):
    result = authorize(os.environ)
    for key in ("ok", "reason", "mode", "max_rounds", "issue", "task_id", "task_dir", "branch"):
        write_output(key, str(result.get(key, "")).lower() if key == "ok" else result.get(key, ""))
    if not result["ok"]:
        print(f"Not starting a task: {result['reason']}")
        return 0
    task_dir = os.path.join(args.repo, result["task_dir"])
    save_json(os.path.join(task_dir, "record", "task.json"), result)
    save_text(os.path.join(task_dir, "record", "TASK.md"), render_task(result))
    save_text(os.path.join(task_dir, "work", ".gitkeep"), "")
    print(f"Authorized {result['mode']} task {result['task_id']} by {result['authorized_by']}")
    return 0


def render_task(task):
    edits = ("Only files under `{0}/work/` may be added or changed."
             if task["mode"] == "review" else
             "Repository files may be changed on the task branch, except the workflow, "
             "agent instructions, task records, `docs/` (the live site) and `.env`/`.gitignore`.")
    return (
        f"# Task {task['task_id']}\n\n"
        f"- Mode: **{task['mode']}** ({'research and proposals only' if task['mode'] == 'review' else 'implementation on the task branch'})\n"
        f"- Issue: #{task['issue']}\n"
        f"- Authorized by: @{task['authorized_by']} via {task['authorized_via']}\n"
        f"- Review rounds allowed: {task['max_rounds']}\n"
        f"- Branch: `{task['branch']}` (agents never merge, push to main or deploy)\n"
        f"- Base commit: `{task['base_sha']}`\n\n"
        f"{edits.format(task['task_dir'])}\n\n"
        "## Brief (the maintainer's own words; this is the whole authorization)\n\n"
        f"{task['brief']}\n"
    )


# ------------------------------------------------------------ patch checking

def patch_paths(patch_file, repo):
    """List every path a patch touches, using git's own parser."""
    out = subprocess.run(
        ["git", "apply", "--numstat", "-z", patch_file],
        cwd=repo, capture_output=True, check=True,
    ).stdout.decode("utf-8", "replace")
    paths, parts, i = [], out.split("\0"), 0
    while i < len(parts):
        entry = parts[i]
        if not entry:
            i += 1
            continue
        fields = entry.split("\t")
        if len(fields) == 3 and fields[2] == "":        # rename: old and new follow
            paths += [parts[i + 1], parts[i + 2]]
            i += 3
        else:
            paths.append(fields[2])
            i += 1
    return paths


def check_paths(paths, mode, task_dir):
    """Return a list of problems (empty when every path is allowed)."""
    problems = []
    work = task_dir.rstrip("/") + "/work/"
    for p in paths:
        norm = os.path.normpath(p).replace("\\", "/")
        if norm.startswith("../") or norm.startswith("/") or norm != p:
            problems.append(f"{p}: unusual path")
        elif mode == "review" and not norm.startswith(work):
            problems.append(f"{p}: review tasks may only write under {work}")
        elif norm in DENIED_FILES or any(norm == d.rstrip("/") or norm.startswith(d) for d in DENIED_PREFIXES):
            problems.append(f"{p}: protected path")
        elif norm.startswith("agent-tasks/") and not norm.startswith(work):
            problems.append(f"{p}: only this task's work/ folder may be changed under agent-tasks/")
    return problems


def check_patch_text(text):
    problems = []
    if re.search(r"^(new file mode|new mode|old mode|deleted file mode) (120000|160000)", text, re.M):
        problems.append("symlinks and submodules are not allowed")
    return problems


def cmd_check_patch(args):
    size = os.path.getsize(args.patch)
    if size == 0:
        write_output("has_changes", "false")
        print("No file changes.")
        return 0
    write_output("has_changes", "true")
    problems = []
    if size > MAX_PATCH_BYTES:
        problems.append(f"patch is {size} bytes (limit {MAX_PATCH_BYTES})")
    with open(args.patch, encoding="utf-8", errors="replace") as f:
        problems += check_patch_text(f.read())
    paths = patch_paths(args.patch, args.repo)
    problems += check_paths(paths, args.mode, args.task_dir)
    if problems:
        print("Patch rejected:\n- " + "\n- ".join(problems))
        return 1
    print("Patch accepted:\n- " + "\n- ".join(paths))
    return 0


# ------------------------------------------------------------------- records

def usage_from_execution(path):
    """Pull turns, cost and tokens from claude-code-action's execution file."""
    data = load_json(path, [])
    if isinstance(data, dict):
        data = [data]
    result = next((m for m in reversed(data or []) if isinstance(m, dict) and m.get("type") == "result"), None)
    if not result:
        return {"available": False}
    usage = result.get("usage") or {}
    return {
        "available": True,
        "num_turns": result.get("num_turns"),
        "duration_ms": result.get("duration_ms"),
        "total_cost_usd": result.get("total_cost_usd"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
        "models": sorted((result.get("modelUsage") or {}).keys()),
        "subtype": result.get("subtype"),
    }


def cmd_usage(args):
    save_json(args.out, usage_from_execution(args.execution_file))
    return 0


def stage_name(stage, rnd):
    return "claude-work" if stage == "work" else f"claude-response-{rnd}"


def cmd_record_claude(args):
    task_dir = os.path.join(args.repo, args.task_dir)
    result = load_json(args.result)
    record = {
        "stage": args.stage,
        "round": args.round,
        "base_sha": args.base_sha,
        "edits_allowed": args.edits_allowed == "true",
        "files_changed": [p for p in (args.files or "").split("\n") if p],
        "result": result,
        "result_valid": isinstance(result, dict) and "summary" in result,
        "usage": load_json(args.usage, {"available": False}),
    }
    name = stage_name(args.stage, args.round)
    save_json(os.path.join(task_dir, "record", name + ".json"), record)
    comment = render_claude(record, load_json(os.path.join(task_dir, "record", "task.json"), {}))
    save_text(os.path.join(task_dir, "record", name + ".md"), comment)
    save_text(args.comment_out, clip(comment))
    return 0


def render_claude(record, task):
    r = record["result"] if record["result_valid"] else {}
    title = ("Claude: first draft" if record["stage"] == "work"
             else f"Claude: answers to Codex round {record['round']}")
    lines = [f"### {title}", ""]
    if not record["result_valid"]:
        lines += ["Claude did not return a structured result (it may have hit the turn, budget or time limit). "
                  "See the workflow run log.", ""]
    else:
        lines += [r.get("summary", ""), ""]
    if record["files_changed"]:
        lines += ["**Files changed**", ""] + [f"- `{p}`" for p in record["files_changed"]] + [""]
    elif record["stage"] != "work" and not record["edits_allowed"]:
        lines += ["_Round limit reached: written answers only, no further edits._", ""]
    if r.get("responses"):
        lines += ["| Finding | Position | Evidence | Action |", "|---|---|---|---|"]
        for x in r["responses"]:
            lines.append(f"| {x['finding_id']} | {x['position'].replace('_', ' ')} | "
                         f"{one_line(x['evidence'], 400)} | {one_line(x['action_taken'], 200)} |")
        lines.append("")
    if r.get("checks_run"):
        lines += ["**Checks Claude says it ran** (claims, not verified by the workflow)", ""]
        lines += [f"- {one_line(c['what'])}: {one_line(c['result'])}" for c in r["checks_run"]] + [""]
    if r.get("unverified_claims"):
        lines += ["**Unverified**", ""] + [f"- {one_line(c)}" for c in r["unverified_claims"]] + [""]
    lines += [usage_line(record["usage"], "Claude")]
    return "\n".join(lines) + "\n"


def usage_line(u, who):
    if not u or not u.get("available"):
        return f"_{who} usage: not reported._"
    cost = u.get("total_cost_usd")
    cost = f", estimated ${cost:.2f}" if isinstance(cost, (int, float)) else ""
    return (f"_{who} usage: {u.get('num_turns')} turns, {u.get('input_tokens')} input / "
            f"{u.get('output_tokens')} output tokens{cost} "
            f"({round((u.get('duration_ms') or 0) / 60000, 1)} min)._")


# --------------------------------------------------------- review + decision

def parse_review(text):
    """Parse Codex's final message (JSON per the schema). Raise ValueError if unusable."""
    text = (text or "").strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("Codex did not return JSON")
    data = json.loads(m.group(0))
    for key in ("findings", "summary", "recommendation"):
        if key not in data:
            raise ValueError(f"Codex review is missing '{key}'")
    for f in data["findings"]:
        for key in ("id", "severity", "status", "title"):
            if key not in f:
                raise ValueError(f"a finding is missing '{key}'")
    return data


def previous_positions(record_dir, rnd):
    """Claude's position on each finding in the response to round rnd-1."""
    prev = load_json(os.path.join(record_dir, f"claude-response-{rnd - 1}.json"), {}) or {}
    result = prev.get("result") or {}
    return {x["finding_id"]: x["position"] for x in result.get("responses", []) if "finding_id" in x}


def decide(review, positions, rnd, max_rounds):
    """
    What happens after Codex review round `rnd`:
      respond         Claude answers and may edit; Codex checks again next round
      final_response  round limit reached: Claude answers in writing only, then stop
      stop            nothing actionable left (converged, or only disagreements remain)
    A finding Claude disagreed with that Codex still keeps open counts as an
    unresolved disagreement: it is reported, never argued about again.
    """
    open_items, disputed = [], []
    for f in review["findings"]:
        if f["status"] == "unresolved_disagreement":
            disputed.append(f["id"])
        elif f["status"] == "open" and f["severity"] != "note":
            if positions.get(f["id"]) == "disagree":
                f["status"] = "unresolved_disagreement"
                disputed.append(f["id"])
            else:
                open_items.append(f["id"])
    if not open_items:
        reason = ("only unresolved disagreements remain" if disputed else "no open findings")
        return {"next": "stop", "reason": reason, "open": open_items, "disputed": disputed}
    if rnd >= max_rounds:
        return {"next": "final_response", "reason": f"round limit ({max_rounds}) reached",
                "open": open_items, "disputed": disputed}
    return {"next": "respond", "reason": f"{len(open_items)} open finding(s)",
            "open": open_items, "disputed": disputed}


def cmd_record_review(args):
    task_dir = os.path.join(args.repo, args.task_dir)
    record_dir = os.path.join(task_dir, "record")
    task = load_json(os.path.join(record_dir, "task.json"), {})
    with open(args.message, encoding="utf-8", errors="replace") as f:
        raw = f.read()
    try:
        review = parse_review(raw)
        error = None
    except (ValueError, json.JSONDecodeError) as e:
        review, error = None, str(e)

    if review is None:
        decision = {"next": "stop", "reason": f"Codex review unusable: {error}", "open": [], "disputed": []}
        review = {"summary": "", "findings": [], "checks_performed": [], "unverified_claims": [],
                  "recommendation": "defer", "recommendation_reason": decision["reason"], "raw": raw[:20000]}
    else:
        decision = decide(review, previous_positions(record_dir, args.round), args.round,
                          int(task.get("max_rounds", MAX_ROUNDS)))
    claimed = review.get("reviewed_sha", "")
    review["reviewed_sha_claimed"] = claimed
    review["reviewed_sha"] = args.sha          # the commit the job actually checked out
    review["round"] = args.round
    record = {"round": args.round, "reviewed_sha": args.sha, "usable": error is None,
              "review": review, "decision": decision}
    save_json(os.path.join(record_dir, f"codex-review-{args.round}.json"), record)
    comment = render_review(record, args.repo_url)
    save_text(os.path.join(record_dir, f"codex-review-{args.round}.md"), comment)
    save_text(args.comment_out, clip(comment))

    state = ("error" if error else
             "success" if not decision["open"] and not decision["disputed"] else "failure")
    write_output("next", decision["next"])
    write_output("status_state", state)
    write_output("status_description",
                 f"Round {args.round}: {len(decision['open'])} open, {len(decision['disputed'])} disputed"[:140])
    return 0


def render_review(record, repo_url=""):
    rv, d, sha = record["review"], record["decision"], record["reviewed_sha"]
    link = f"[`{sha[:10]}`]({repo_url}/commit/{sha})" if repo_url else f"`{sha[:10]}`"
    lines = [f"### Codex review, round {record['round']} of commit {link}", "", rv.get("summary", ""), ""]
    if rv.get("findings"):
        lines += ["| # | Severity | Status | Finding |", "|---|---|---|---|"]
        for f in rv["findings"]:
            lines.append(f"| {f['id']} | {f['severity']} | {f['status'].replace('_', ' ')} | "
                         f"**{one_line(f['title'], 120)}** {one_line(f.get('detail'), 500)} "
                         f"{('Where: ' + one_line(f.get('location'), 120)) if f.get('location') else ''} |")
        lines.append("")
        assessed = [f for f in rv["findings"] if f.get("assessment_of_response")]
        if assessed:
            lines += ["**On Claude's previous answers**", ""]
            lines += [f"- {f['id']}: {one_line(f['assessment_of_response'], 400)}" for f in assessed] + [""]
    if rv.get("checks_performed"):
        lines += ["**Checks Codex says it performed**", ""] + [f"- {one_line(c)}" for c in rv["checks_performed"]] + [""]
    lines += [f"Codex's view: **{rv.get('recommendation')}**: {one_line(rv.get('recommendation_reason'), 400)} "
              "(an agent opinion, not approval)", "",
              f"Next step: **{d['next'].replace('_', ' ')}** ({d['reason']}).",
              "_Codex usage is not reported by codex-action; see the OpenAI usage page._"]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------- final report

def cmd_final_report(args):
    task_dir = os.path.join(args.repo, args.task_dir)
    record_dir = os.path.join(task_dir, "record")
    task = load_json(os.path.join(record_dir, "task.json"), {})
    jobs = json.loads(args.needs or "{}")
    checks = load_json(args.checks, {}) or {}
    text, verdict = render_final(task, record_dir, jobs, checks, args)
    save_text(os.path.join(record_dir, "FINAL-REPORT.md"), text)
    save_text(args.comment_out, clip(text))
    write_output("verdict", verdict)
    return 0


def recommend(task, last_review, jobs, checks, scope_violation):
    failed = [n for n, j in jobs.items() if j.get("result") in ("failure", "cancelled")]
    if scope_violation or checks.get("failed"):
        return "reject", "checks failed or an agent tried to change files outside its authorization"
    if failed:
        return "defer", "the workflow did not finish (" + ", ".join(sorted(failed)) + ")"
    if not last_review or not last_review.get("usable", True):
        return "defer", "no usable Codex review was completed"
    d = last_review["decision"]
    if d["open"] or d["disputed"]:
        return "defer", f"{len(d['open'])} open finding(s) and {len(d['disputed'])} unresolved disagreement(s)"
    return "approve", "Codex reported no open findings and the workflow checks passed; read the work before deciding"


def render_final(task, record_dir, jobs, checks, args):
    reviews = []
    for r in range(1, MAX_ROUNDS + 1):
        rec = load_json(os.path.join(record_dir, f"codex-review-{r}.json"))
        if rec:
            reviews.append(rec)
    work = load_json(os.path.join(record_dir, "claude-work.json"), {}) or {}
    responses = [load_json(os.path.join(record_dir, f"claude-response-{r}.json")) for r in range(1, MAX_ROUNDS + 1)]
    responses = [x for x in responses if x]
    last = reviews[-1] if reviews else None
    scope_violation = any(n.startswith("rejected-") for n in os.listdir(record_dir)) if os.path.isdir(record_dir) else False
    verdict, why = recommend(task, last, jobs, checks, scope_violation)

    L = [f"## Final report: {task.get('mode', '?')} task on #{task.get('issue', '?')}", "",
         f"**Workflow recommendation: {verdict.upper()}** ({why}).",
         *([f"The run did not complete normally: {', '.join(sorted(n for n, j in jobs.items() if j.get('result') in ('failure', 'cancelled')))}."]
           if any(j.get("result") in ("failure", "cancelled") for j in jobs.values()) else []),
         "This is the workflow's summary, not an approval. Only your merge, or your decision on the issue, approves anything.", "",
         f"- Authorized by @{task.get('authorized_by')} via {task.get('authorized_via')}",
         f"- Branch `{task.get('branch')}` at `{args.head_sha[:10]}`" + (f", pull request {args.pr_url}" if args.pr_url else ""),
         f"- Workflow run: {args.run_url}", ""]

    L += ["### What was proposed or changed", ""]
    wr = work.get("result") or {}
    L += [wr.get("summary", "_No structured summary from Claude._"), ""]
    files = sorted(set(work.get("files_changed", []) + [p for x in responses for p in x.get("files_changed", [])]))
    L += [f"- `{p}`" for p in files] or ["- No files changed."]
    L += ["", f"Compare: {args.repo_url}/compare/{task.get('base_sha', '')[:12]}...{args.head_sha}" if args.repo_url else "", ""]

    L += ["### Preview and artifacts", ""]
    if checks.get("preview"):
        L.append(f"- {checks['preview']}")
    L.append(f"- Readable files: {args.repo_url}/tree/{task.get('branch')}/{task.get('task_dir')}" if args.repo_url else "")
    L.append("- Full records (task, every review and answer as JSON and Markdown): `" + task.get("task_dir", "") + "/record/`")
    L.append("")

    L += ["### Evidence and tests", "", "**Run by the workflow itself (verified):**", ""]
    L += [f"- {c['name']}: {c['result']}" for c in checks.get("checks", [])] or ["- None recorded."]
    L += ["", "**Claimed by the agents (not re-run by the workflow):**", ""]
    for who, items in (("Claude", [c for x in [work] + responses for c in (x.get("result") or {}).get("checks_run", [])]),
                       ("Codex", [c for rv in reviews for c in rv["review"].get("checks_performed", [])])):
        for c in items[:30]:
            L.append(f"- {who}: " + (one_line(f"{c['what']}: {c['result']}") if isinstance(c, dict) else one_line(c)))
    L.append("")

    L += ["### Findings", ""]
    if last:
        L += ["| # | Severity | Final status | Finding | Claude's last position |", "|---|---|---|---|---|"]
        positions = {}
        for x in responses:
            for y in (x.get("result") or {}).get("responses", []):
                positions[y["finding_id"]] = y["position"].replace("_", " ")
        seen = {}
        for rv in reviews:
            for f in rv["review"]["findings"]:
                seen[f["id"]] = f
        for fid, f in seen.items():
            L.append(f"| {fid} | {f['severity']} | {f['status'].replace('_', ' ')} | {one_line(f['title'], 140)} | "
                     f"{positions.get(fid, '–')} |")
        d = last["decision"]
        L += ["", f"Last Codex review: round {last['round']}, outcome **{d['next'].replace('_', ' ')}** ({d['reason']})."]
        if d["disputed"]:
            L += ["", "**Unresolved disagreements** (both positions are in the round records; the workflow does not force agreement): "
                  + ", ".join(d["disputed"])]
    else:
        L.append("No Codex review completed.")
    L.append("")

    unverified = [c for x in [work] + responses for c in (x.get("result") or {}).get("unverified_claims", [])]
    unverified += [c for rv in reviews for c in rv["review"].get("unverified_claims", [])]
    L += ["### Unverified claims and source or licensing gaps", ""]
    L += [f"- {one_line(c, 400)}" for c in dict.fromkeys(unverified)] or ["- None listed by the agents."]
    sources = {}
    for x in [work] + responses:            # later answers replace earlier entries for the same URL
        for src in (x.get("result") or {}).get("sources", []):
            sources[src.get("url") or src.get("title")] = src
    for src in list(sources.values())[:40]:
        if not src.get("opened") or not src.get("rights") or "unknown" in src.get("rights", "").lower():
            L.append(f"- Source gap: {one_line(src['title'], 120)} ({src['url']}): "
                     f"{'opened' if src.get('opened') else 'NOT opened'}, rights: {one_line(src.get('rights') or 'not stated', 160)}")
    questions = [q for x in [work] + responses for q in (x.get("result") or {}).get("open_questions_for_maintainer", [])]
    if questions:
        L += ["", "**Questions for you**", ""] + [f"- {one_line(q, 400)}" for q in dict.fromkeys(questions)]
    L.append("")

    if sources:
        L += ["### Sources Claude reports using", ""]
        L += [f"- {one_line(src['title'], 120)}: {src['url']} ({'opened' if src.get('opened') else 'not opened'}; "
              f"checked: {one_line(src.get('what_was_checked') or '-', 200)}; rights: {one_line(src.get('rights') or 'not stated', 120)})"
              for src in list(sources.values())[:40]]
        L.append("")

    L += ["### Usage", ""]
    L += [f"- {usage_line(x.get('usage'), 'Claude ' + ('draft' if x.get('stage') == 'work' else 'round ' + str(x.get('round'))))}"
          for x in [work] + responses if x]
    L += ["- Codex: token usage is not exposed by codex-action; check https://platform.openai.com/usage.", ""]

    L += ["### Job results", ""] + [f"- {n}: {j.get('result')}" for n, j in jobs.items()] + [""]
    L += ["### Your decision", "",
          "- **Approve**: review the pull request and merge it yourself.",
          "- **Defer**: leave the pull request open (draft) and say what is missing; a new `/agent …` command starts a fresh task.",
          "- **Reject**: close the pull request; the branch stays for reference until you delete it.", ""]
    return "\n".join(l for l in L if l is not None) + "\n", verdict


# ------------------------------------------------------------------- prompts

def cmd_prompt(args):
    """Fill {placeholders} in a prompt template from KEY=VALUE pairs."""
    with open(args.template, encoding="utf-8") as f:
        text = f.read()
    for pair in args.set or []:
        key, _, value = pair.partition("=")
        text = text.replace("{" + key + "}", value)
    left = sorted(set(re.findall(r"\{([a-z_]+)\}", text)))
    if left:
        print("Unfilled placeholders: " + ", ".join(left))
        return 1
    save_text(args.out, text)
    return 0


# --------------------------------------------------------------------- main

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("authorize")
    a.add_argument("--repo", default=".")
    a.set_defaults(func=cmd_authorize)

    a = sub.add_parser("check-patch")
    a.add_argument("--repo", default=".")
    a.add_argument("--patch", required=True)
    a.add_argument("--mode", required=True, choices=["review", "implement"])
    a.add_argument("--task-dir", required=True)
    a.set_defaults(func=cmd_check_patch)

    a = sub.add_parser("usage")
    a.add_argument("--execution-file", default="")
    a.add_argument("--out", required=True)
    a.set_defaults(func=cmd_usage)

    a = sub.add_parser("record-claude")
    a.add_argument("--repo", default=".")
    a.add_argument("--task-dir", required=True)
    a.add_argument("--stage", required=True, choices=["work", "response"])
    a.add_argument("--round", type=int, default=0)
    a.add_argument("--base-sha", default="")
    a.add_argument("--edits-allowed", default="true")
    a.add_argument("--files", default="")
    a.add_argument("--result", required=True)
    a.add_argument("--usage", required=True)
    a.add_argument("--comment-out", required=True)
    a.set_defaults(func=cmd_record_claude)

    a = sub.add_parser("record-review")
    a.add_argument("--repo", default=".")
    a.add_argument("--task-dir", required=True)
    a.add_argument("--round", type=int, required=True)
    a.add_argument("--sha", required=True)
    a.add_argument("--message", required=True)
    a.add_argument("--repo-url", default="")
    a.add_argument("--comment-out", required=True)
    a.set_defaults(func=cmd_record_review)

    a = sub.add_parser("final-report")
    a.add_argument("--repo", default=".")
    a.add_argument("--task-dir", required=True)
    a.add_argument("--needs", default="{}")
    a.add_argument("--checks", default="")
    a.add_argument("--head-sha", default="")
    a.add_argument("--pr-url", default="")
    a.add_argument("--run-url", default="")
    a.add_argument("--repo-url", default="")
    a.add_argument("--comment-out", required=True)
    a.set_defaults(func=cmd_final_report)

    a = sub.add_parser("prompt")
    a.add_argument("--template", required=True)
    a.add_argument("--out", required=True)
    a.add_argument("--set", action="append", metavar="KEY=VALUE")
    a.set_defaults(func=cmd_prompt)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
