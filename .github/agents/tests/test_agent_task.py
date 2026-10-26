"""Tests for .github/agents/scripts/agent_task.py. Run: python3 -m unittest discover -s .github/agents/tests"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import agent_task as at  # noqa: E402

BRIEF = "Assess the five source leads in issue 25. Research only, no code."


def env(**kw):
    base = {
        "EVENT_NAME": "issue_comment", "ACTOR": "ksai4u-glitch", "ACTOR_TYPE": "User",
        "ACTOR_PERMISSION": "admin", "REPO_OWNER": "ksai4u-glitch", "AGENT_MAINTAINERS": "",
        "ISSUE_NUMBER": "25", "ISSUE_STATE": "open", "ISSUE_IS_PR": "false", "ISSUE_LABELS": "[]",
        "COMMENT_BODY": "/agent review\n" + BRIEF, "RUN_NUMBER": "7",
    }
    base.update(kw)
    return base


class Authorize(unittest.TestCase):
    def test_owner_review(self):
        r = at.authorize(env())
        self.assertTrue(r["ok"], r)
        self.assertEqual((r["mode"], r["max_rounds"], r["branch"]), ("review", 3, "agent/issue-25-run-7"))
        self.assertEqual(r["brief"], BRIEF)

    def test_rounds_option(self):
        r = at.authorize(env(COMMENT_BODY="/agent implement rounds=2\n" + BRIEF))
        self.assertEqual((r["mode"], r["max_rounds"]), ("implement", 2))

    def test_refusals(self):
        cases = [
            env(ACTOR="someone"),                                  # not a maintainer
            env(ACTOR_PERMISSION="write"),                         # not admin/maintain
            env(ACTOR="ksai4u-glitch[bot]"), env(ACTOR_TYPE="Bot"),
            env(ISSUE_IS_PR="true"), env(ISSUE_STATE="closed"),
            env(ISSUE_LABELS='["agent:stop"]'),
            env(AGENT_AUTOMATION="off"),
            env(COMMENT_BODY="/agent review"),                     # no brief
            env(COMMENT_BODY="/agent review rounds=4\n" + BRIEF),
            env(COMMENT_BODY="/agent review please\n" + BRIEF),
            env(COMMENT_BODY="/agent merge\n" + BRIEF),
            env(COMMENT_BODY="hello /agent review\n" + BRIEF),
        ]
        for e in cases:
            self.assertFalse(at.authorize(e)["ok"], e)

    def test_maintainer_list(self):
        self.assertTrue(at.authorize(env(AGENT_MAINTAINERS="a, KSAI4U-glitch"))["ok"])
        self.assertFalse(at.authorize(env(AGENT_MAINTAINERS="someone-else"))["ok"])

    def test_dispatch(self):
        r = at.authorize(env(EVENT_NAME="workflow_dispatch", COMMENT_BODY="",
                             DISPATCH_MODE="review", DISPATCH_ROUNDS="1", DISPATCH_BRIEF=BRIEF))
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["max_rounds"], 1)


class Paths(unittest.TestCase):
    TD = "agent-tasks/issue-25-run-7"

    def test_review_mode(self):
        self.assertEqual(at.check_paths([self.TD + "/work/memo.md"], "review", self.TD), [])
        for p in ["build_map.py", self.TD + "/record/task.json", "agent-tasks/other/work/x.md"]:
            self.assertTrue(at.check_paths([p], "review", self.TD), p)

    def test_implement_mode(self):
        self.assertEqual(at.check_paths(["history/build_history.py", self.TD + "/work/notes.md"], "implement", self.TD), [])
        for p in [".github/workflows/x.yml", "docs/index.html", "AGENTS.md", "CLAUDE.md", ".gitignore",
                  ".env", self.TD + "/record/codex-review-1.json", "agent-tasks/issue-1-run-1/work/a.md",
                  "../outside", "a/../docs/index.html"]:
            self.assertTrue(at.check_paths([p], "implement", self.TD), p)

    def test_symlink_text(self):
        self.assertTrue(at.check_patch_text("diff --git a/x b/x\nnew file mode 120000\n"))
        self.assertEqual(at.check_patch_text("diff --git a/x b/x\nnew file mode 100644\n"), [])

    def test_patch_paths_with_git(self):
        with tempfile.TemporaryDirectory() as d:
            run = lambda *a: subprocess.run(a, cwd=d, check=True, capture_output=True)
            run("git", "init", "-q")
            run("git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "x")
            os.makedirs(os.path.join(d, "docs"))
            open(os.path.join(d, "docs", "index.html"), "w").write("x\n")
            open(os.path.join(d, "ok.py"), "w").write("y\n")
            run("git", "add", "-A")
            patch = subprocess.run(["git", "diff", "--cached", "--binary"], cwd=d, capture_output=True, check=True).stdout
            run("git", "reset", "-q", "--hard")
            run("git", "clean", "-qfd")
            pf = os.path.join(d, "..", os.path.basename(d) + ".patch")
            open(pf, "wb").write(patch)
            try:
                self.assertEqual(sorted(at.patch_paths(pf, d)), ["docs/index.html", "ok.py"])
            finally:
                os.remove(pf)


def review(findings, rec="defer"):
    return {"summary": "s", "recommendation": rec, "recommendation_reason": "r", "findings": findings,
            "checks_performed": [], "unverified_claims": []}


def finding(fid, status="open", severity="major"):
    return {"id": fid, "severity": severity, "status": status, "title": "t", "detail": "d",
            "evidence": "e", "location": "l", "assessment_of_response": ""}


class Decide(unittest.TestCase):
    def test_converged(self):
        d = at.decide(review([finding("F1", "resolved"), finding("F2", severity="note")]), {}, 1, 3)
        self.assertEqual(d["next"], "stop")

    def test_respond_then_limit(self):
        self.assertEqual(at.decide(review([finding("F1")]), {}, 1, 3)["next"], "respond")
        self.assertEqual(at.decide(review([finding("F1")]), {}, 3, 3)["next"], "final_response")
        self.assertEqual(at.decide(review([finding("F1")]), {}, 1, 1)["next"], "final_response")

    def test_disagreement_is_not_forced(self):
        d = at.decide(review([finding("F1")]), {"F1": "disagree"}, 2, 3)
        self.assertEqual((d["next"], d["disputed"]), ("stop", ["F1"]))
        d = at.decide(review([finding("F1"), finding("F2")]), {"F1": "disagree"}, 2, 3)
        self.assertEqual((d["next"], d["open"], d["disputed"]), ("respond", ["F2"], ["F1"]))

    def test_parse_review(self):
        self.assertEqual(at.parse_review("noise " + json.dumps(review([finding("F1")])))["findings"][0]["id"], "F1")
        for bad in ["", "not json", json.dumps({"summary": "x"})]:
            with self.assertRaises((ValueError, json.JSONDecodeError)):
                at.parse_review(bad)


class Records(unittest.TestCase):
    def test_full_flow_report(self):
        with tempfile.TemporaryDirectory() as repo:
            td = "agent-tasks/issue-25-run-7"
            rd = os.path.join(repo, td, "record")
            task = at.authorize(env(BASE_SHA="a" * 40))
            at.save_json(os.path.join(rd, "task.json"), task)
            claude = {"summary": "Memo written.", "changes": [], "responses": [], "checks_run": [{"what": "opened PDF", "result": "ok"}],
                      "sources": [{"title": "1976 Gazette", "url": "https://x", "opened": False, "what_was_checked": "", "rights": ""}],
                      "unverified_claims": ["Kogi boundary"], "open_questions_for_maintainer": [],
                      "recommendation": "defer", "recommendation_reason": "x"}
            res, use, out = (os.path.join(repo, n) for n in ("res.json", "use.json", "c.md"))
            at.save_json(res, claude)
            at.save_json(use, {"available": True, "num_turns": 9, "input_tokens": 1, "output_tokens": 2,
                               "total_cost_usd": 0.5, "duration_ms": 60000})
            at.main(["record-claude", "--repo", repo, "--task-dir", td, "--stage", "work", "--result", res,
                     "--usage", use, "--files", td + "/work/memo.md", "--comment-out", out])
            msg = os.path.join(repo, "msg.txt")
            with open(msg, "w") as f:
                f.write(json.dumps(review([finding("F1")])))
            os.environ.pop("GITHUB_OUTPUT", None)
            at.main(["record-review", "--repo", repo, "--task-dir", td, "--round", "1", "--sha", "b" * 40,
                     "--message", msg, "--comment-out", out])
            rec = at.load_json(os.path.join(rd, "codex-review-1.json"))
            self.assertEqual((rec["reviewed_sha"], rec["decision"]["next"]), ("b" * 40, "respond"))
            claude["responses"] = [{"finding_id": "F1", "position": "disagree", "evidence": "ev", "action_taken": "none"}]
            at.save_json(res, claude)
            at.main(["record-claude", "--repo", repo, "--task-dir", td, "--stage", "response", "--round", "1",
                     "--result", res, "--usage", use, "--comment-out", out])
            at.main(["record-review", "--repo", repo, "--task-dir", td, "--round", "2", "--sha", "c" * 40,
                     "--message", msg, "--comment-out", out])
            self.assertEqual(at.load_json(os.path.join(rd, "codex-review-2.json"))["decision"]["next"], "stop")
            at.main(["final-report", "--repo", repo, "--task-dir", td, "--head-sha", "c" * 40,
                     "--needs", json.dumps({"codex_2": {"result": "success"}}), "--comment-out", out])
            with open(os.path.join(rd, "FINAL-REPORT.md")) as f:
                report = f.read()
            self.assertIn("Workflow recommendation: DEFER", report)
            self.assertIn("Unresolved disagreements", report)
            self.assertIn("Kogi boundary", report)
            self.assertIn("1976 Gazette", report)
            self.assertIn("not an approval", report)

    def test_unusable_review_stops(self):
        with tempfile.TemporaryDirectory() as repo:
            td = "agent-tasks/t"
            at.save_json(os.path.join(repo, td, "record", "task.json"), {"max_rounds": 3})
            msg, out = os.path.join(repo, "m"), os.path.join(repo, "o")
            with open(msg, "w") as f:
                f.write("I could not finish")
            at.main(["record-review", "--repo", repo, "--task-dir", td, "--round", "1", "--sha", "d" * 40,
                     "--message", msg, "--comment-out", out])
            rec = at.load_json(os.path.join(repo, td, "record", "codex-review-1.json"))
            self.assertEqual(rec["decision"]["next"], "stop")
            at.main(["final-report", "--repo", repo, "--task-dir", td, "--head-sha", "d" * 40, "--comment-out", out])
            with open(os.path.join(repo, td, "record", "FINAL-REPORT.md")) as f:
                self.assertIn("Workflow recommendation: DEFER", f.read())

    def test_usage_from_execution(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "e.json")
            at.save_json(p, [{"type": "system"}, {"type": "result", "num_turns": 4, "total_cost_usd": 0.12,
                                                  "usage": {"input_tokens": 10, "output_tokens": 5},
                                                  "modelUsage": {"m": {}}}])
            u = at.usage_from_execution(p)
            self.assertEqual((u["num_turns"], u["input_tokens"], u["models"]), (4, 10, ["m"]))
            self.assertFalse(at.usage_from_execution(os.path.join(d, "missing"))["available"])


if __name__ == "__main__":
    unittest.main()
