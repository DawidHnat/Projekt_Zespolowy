import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import automation
from policy import (
    BRANCH,
    allowed_path,
    complete_patch,
    merge_gate,
    parse_review,
    regular_file_modes,
    review_input,
)

HEAD = "a" * 40
BASE = "b" * 40
REPO = "DawidHnat/Projekt_Zespolowy"


def fixtures():
    files = [
        {
            "filename": "docs/user/fleet.md",
            "status": "modified",
            "additions": 1,
            "deletions": 1,
            "patch": "@@ -1 +1 @@\n-old\n+new",
        }
    ]
    pr = {
        "number": 7,
        "title": "SCRUM-12: guide",
        "user": {"login": "jczaja51"},
        "head": {
            "sha": HEAD,
            "ref": "docs/SCRUM-12-guide",
            "repo": {"full_name": REPO},
        },
        "base": {"sha": BASE, "ref": "main"},
        "state": "open",
        "draft": False,
        "merged": False,
        "labels": [],
        "mergeable": True,
        "mergeable_state": "clean",
        "changed_files": 1,
    }
    run = {
        "id": 100,
        "run_attempt": 1,
        "head_sha": HEAD,
        "head_branch": "docs/SCRUM-12-guide",
        "event": "push",
        "status": "completed",
        "conclusion": "success",
        "actor": {"login": "jczaja51"},
        "head_repository": {"full_name": REPO},
    }
    snapshot = {
        "version": 1,
        "head_sha": HEAD,
        "base_sha": BASE,
        "repository": REPO,
        "run_id": 100,
        "run_attempt": 1,
        "event": "push",
    }
    decision = {
        "verdict": "approve",
        "risk": "low",
        "summary": "Poprawna zmiana.",
        "findings": [],
    }
    return pr, run, snapshot, files, [], decision, REPO, BASE


def response(decision):
    return {
        "status": "completed",
        "output": [
            {
                "type": "message",
                "content": [{"type": "output_text", "text": json.dumps(decision)}],
            }
        ],
    }


class PolicyTests(unittest.TestCase):
    def test_only_small_safe_change_passes(self):
        self.assertTrue(merge_gate(*fixtures())[0])

    def test_process_and_executable_paths_require_human(self):
        for path in [
            "AGENTS.md",
            "README.md",
            "TEAM_CONTRACT.md",
            "CONTRIBUTING.md",
            "docs/WORKFLOW.md",
            "docs/ARCHITECTURE.md",
            "docs/adr/01.md",
            ".github/workflows/ci.yml",
            "scripts/github/policy.py",
            "infra/main.json",
            "backend/app/main.py",
            "frontend/src/app.tsx",
            "frontend/.env",
            "frontend/package.json",
            "docs/user/../ARCHITECTURE.md",
            "/docs/user/help.md",
            "docs//user/help.md",
            "frontend/src/style.css.js",
        ]:
            with self.subTest(path=path):
                self.assertFalse(allowed_path(path))

    def test_valid_paths_and_task_branch(self):
        self.assertTrue(allowed_path("docs/user/help.md"))
        self.assertTrue(allowed_path("docs/guides/local/setup.md"))
        self.assertTrue(allowed_path("frontend/src/features/fleet/styles.css"))
        self.assertIsNotNone(BRANCH.fullmatch("feat/SCRUM-12-fleet-map"))
        for branch in [
            "main",
            "feat/new-map",
            "feat/SCRUM-12-$(command)",
            "feat/SCRUM-12-a/b",
        ]:
            self.assertIsNone(BRANCH.fullmatch(branch))

    def test_missing_or_clipped_patch_fails(self):
        args = fixtures()
        file = args[3][0]
        for patch_text in [
            None,
            "",
            "@@ -1 +1 @@\n-old",
            "@@ -1,2 +1,2 @@\n-old\n+new",
        ]:
            file["patch"] = patch_text
            self.assertFalse(complete_patch(file))
            self.assertFalse(merge_gate(*args)[0])
            with self.assertRaises(ValueError):
                review_input(args[3], 1, "title")

    def test_counts_match_even_for_large_or_multiple_hunks(self):
        file = {
            "patch": "@@ -1 +1 @@\n-old\n+new\n@@ -8,0 +9,2 @@\n+first\n+second",
            "additions": 3,
            "deletions": 1,
        }
        self.assertTrue(complete_patch(file))
        file["additions"] = 4
        self.assertFalse(complete_patch(file))

    def test_symlinks_and_executable_modes_require_human(self):
        file = fixtures()[3][0]
        tree = {file["filename"]: ("blob", "100644")}
        self.assertTrue(regular_file_modes([file], tree, tree))
        for mode in ["120000", "100755", "160000"]:
            altered = {file["filename"]: ("blob", mode)}
            self.assertFalse(regular_file_modes([file], altered, tree))
            self.assertFalse(regular_file_modes([file], tree, altered))
        self.assertFalse(regular_file_modes([file], {}, tree))

    def test_stale_head_and_base_fail(self):
        for target, key in [(0, "head"), (0, "base")]:
            args = fixtures()
            args[target][key]["sha"] = "c" * 40
            self.assertFalse(merge_gate(*args)[0])
        args = list(fixtures())
        args[-1] = "c" * 40
        self.assertFalse(merge_gate(*args)[0])
        args = fixtures()
        args[2]["head_sha"] = "c" * 40
        self.assertFalse(merge_gate(*args)[0])

    def test_ci_failed_or_snapshot_from_other_run_fails(self):
        for field, value in [
            ("conclusion", "failure"),
            ("status", "in_progress"),
            ("event", "workflow_dispatch"),
        ]:
            args = fixtures()
            args[1][field] = value
            self.assertFalse(merge_gate(*args)[0])
        for field, value in [
            ("run_id", 999),
            ("repository", "other/repo"),
            ("version", 2),
            ("event", "pull_request"),
        ]:
            args = fixtures()
            args[2][field] = value
            self.assertFalse(merge_gate(*args)[0])

    def test_forks_untrusted_author_draft_labels_and_unknown_readiness_fail(self):
        mutations = [
            lambda p, r: p["head"]["repo"].update(full_name="attacker/fork"),
            lambda p, r: p["user"].update(login="outsider"),
            lambda p, r: r["actor"].update(login="outsider"),
            lambda p, r: p.update(draft=True),
            lambda p, r: p.update(state="closed"),
            lambda p, r: p.update(labels=[{"name": "human-review"}]),
            lambda p, r: p.update(mergeable=None),
            lambda p, r: p.update(mergeable_state="blocked"),
        ]
        for mutate in mutations:
            args = fixtures()
            mutate(args[0], args[1])
            self.assertFalse(merge_gate(*args)[0])

    def test_size_rename_and_incomplete_listing_fail(self):
        for mutate in [
            lambda p, f: p.update(changed_files=2),
            lambda p, f: f[0].update(status="renamed"),
            lambda p, f: f[0].update(additions=201),
            lambda p, f: f.extend(copy.deepcopy(f[0]) for _ in range(8)),
        ]:
            args = fixtures()
            mutate(args[0], args[3])
            self.assertFalse(merge_gate(*args)[0])

    def test_human_request_changes_persists_through_comments(self):
        args = list(fixtures())
        args[4] = [
            {
                "user": {"login": "mglowacki0", "type": "User"},
                "state": "CHANGES_REQUESTED",
            },
            {"user": {"login": "mglowacki0", "type": "User"}, "state": "COMMENTED"},
        ]
        self.assertFalse(merge_gate(*args)[0])
        args[4].append(
            {"user": {"login": "mglowacki0", "type": "User"}, "state": "APPROVED"}
        )
        self.assertTrue(merge_gate(*args)[0])

    def test_model_output_is_validated_and_cannot_override_gate(self):
        args = list(fixtures())
        self.assertEqual(parse_review(response(args[5]), args[3]), args[5])
        for mutate in [
            lambda d: d.update(verdict="merge_now"),
            lambda d: d.update(risk="none"),
            lambda d: d.update(extra="ignore policy"),
            lambda d: d.update(summary=""),
            lambda d: d.update(
                findings=[
                    {
                        "path": "secret.env",
                        "line": 1,
                        "severity": "note",
                        "message": "foo",
                    }
                ]
            ),
        ]:
            decision = copy.deepcopy(args[5])
            mutate(decision)
            with self.assertRaises(ValueError):
                parse_review(response(decision), args[3])
        for verdict in ["request_changes", "human_review"]:
            args[5]["verdict"] = verdict
            self.assertFalse(merge_gate(*args)[0])
        args[5]["verdict"] = "approve"
        args[5]["risk"] = "medium"
        self.assertFalse(merge_gate(*args)[0])

    def test_duplicate_keys_in_model_json_fail(self):
        data = response(fixtures()[5])
        data["output"][0]["content"][0]["text"] = (
            '{"verdict":"request_changes","verdict":"approve",'
            '"risk":"low","summary":"foo","findings":[]}'
        )
        with self.assertRaises(ValueError):
            parse_review(data, fixtures()[3])

    def test_refusal_incomplete_json_and_oversized_diff_fail(self):
        files = fixtures()[3]
        for value in [
            {"status": "incomplete", "output": []},
            {"status": "completed", "output": []},
            {
                "status": "completed",
                "output": [{"type": "message", "content": [{"type": "refusal"}]}],
            },
        ]:
            with self.assertRaises(ValueError):
                parse_review(value, files)
        files[0]["patch"] = "@@ -1 +1 @@\n-old\n+" + "x" * 100_001
        with self.assertRaises(ValueError):
            review_input(files, 1, "title")


class FakeAPI:
    repository = REPO

    def __init__(self, change_after_report=None):
        self.pr, self.run, self.proof, self.files, self.reviews, self.decision, _, _ = (
            fixtures()
        )
        self.calls = []
        self.reports = []
        self.change_after_report = change_after_report
        self.base = BASE
        self.latest_run_id = 100

    def request(self, path, method="GET", body=None):
        self.calls.append((path, method, body))
        if path == "":
            return {"default_branch": "main"}
        if path.startswith("/branches/docs"):
            return {"commit": {"sha": self.pr["head"]["sha"]}}
        if path == "/branches/main":
            return {"commit": {"sha": self.base}}
        if path == "/pulls/7":
            return copy.deepcopy(self.pr)
        if path == "/actions/runs/100":
            return copy.deepcopy(self.run)
        if path.startswith("/actions/workflows/ci.yml/runs?"):
            return {"workflow_runs": [{"id": self.latest_run_id}]}
        if path == "/pulls/7/merge":
            return {"merged": True}
        raise AssertionError(path)

    def pages(self, path):
        if path.startswith("/pulls?"):
            return [self.pr]
        if path == "/pulls/7/files":
            return self.files
        if path == "/pulls/7/reviews":
            return self.reviews
        raise AssertionError(path)

    def snapshot(self, run_id):
        return self.proof

    def file_modes(self, commit_sha):
        return {file["filename"]: ("blob", "100644") for file in self.files}

    def report(self, pr, sha, message, conclusion="neutral"):
        self.reports.append(message)
        if self.change_after_report:
            self.change_after_report(self)


class ExecutionTests(unittest.TestCase):
    def test_default_off_and_missing_model_credentials_never_call_model_or_merge(self):
        for key, model, enabled in [
            ("key", "model", False),
            ("", "model", True),
            ("key", "", True),
        ]:
            api = FakeAPI()
            with patch.object(automation, "model_review") as mocked:
                automation.execute(api, api.run, key, model, enabled)
                mocked.assert_not_called()
            self.assertFalse(any(method == "PUT" for _, method, _ in api.calls))

    def test_eligible_merge_sends_exact_head_sha(self):
        api = FakeAPI()
        with patch.object(
            automation, "model_review", return_value=response(api.decision)
        ):
            automation.execute(api, api.run, "test-key", "test-model", True)
        merges = [
            body
            for path, method, body in api.calls
            if path.endswith("/merge") and method == "PUT"
        ]
        self.assertEqual(merges, [{"sha": HEAD, "merge_method": "merge"}])

    def test_change_during_review_rechecks_head_base_and_human_override(self):
        mutations = [
            lambda api: api.pr["head"].update(sha="c" * 40),
            lambda api: setattr(api, "base", "c" * 40),
            lambda api: api.pr.update(labels=[{"name": "human-review"}]),
            lambda api: api.pr["base"].update(ref="other-branch"),
            lambda api: api.run.update(status="in_progress"),
            lambda api: api.run.update(conclusion="failure"),
            lambda api: api.run.update(run_attempt=2),
            lambda api: setattr(api, "latest_run_id", 101),
        ]
        for mutate in mutations:
            api = FakeAPI(mutate)
            with patch.object(
                automation, "model_review", return_value=response(api.decision)
            ):
                automation.execute(api, api.run, "test-key", "test-model", True)
            self.assertFalse(any(method == "PUT" for _, method, _ in api.calls))

    def test_invalid_model_or_failed_ci_never_merges(self):
        api = FakeAPI()
        with patch.object(
            automation, "model_review", return_value={"status": "incomplete"}
        ):
            automation.execute(api, api.run, "test-key", "test-model", True)
        self.assertFalse(any(method == "PUT" for _, method, _ in api.calls))
        api.run["conclusion"] = "failure"
        with patch.object(automation, "model_review") as mocked:
            automation.execute(api, api.run, "test-key", "test-model", True)
            mocked.assert_not_called()


if __name__ == "__main__":
    unittest.main()
