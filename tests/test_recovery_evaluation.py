"""Focused Phase 72 evidence, classification, and non-execution tests."""
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from src.developer.local_workflow import LocalWorkflowError, _git_index_state
from src.developer.recovery_evaluation import RecoveryEvaluation, evaluate_recovery
from src.developer.execution_verification import verify_execution
from tests import test_test_execution_observation as phase70_fixture


class RecoveryEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = phase70_fixture.TestExecutionObservationTests("test_passing_exact_test_records_external_observation_and_repeat_is_distinct")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def _git(self, *args):
        return subprocess.run(["git", "-C", str(self.fixture.repo), *args], check=True,
                              capture_output=True).stdout

    def _verify(self, observation):
        fixture = self.fixture
        return verify_execution(fixture.workspace, fixture.repo, fixture.applied["run_id"], observation["run_id"])

    def _evaluate(self, verification):
        fixture = self.fixture
        return evaluate_recovery(fixture.workspace, fixture.repo, verification["run_id"])

    def test_verified_chain_requires_no_recovery_and_does_not_execute(self):
        fixture = self.fixture
        observation = fixture.run_tests("tests.test_app.AppTests.test_value")
        verification = self._verify(observation)
        source = (fixture.repo / "app.py").read_bytes()
        head, index, status = self._git("rev-parse", "HEAD"), _git_index_state(fixture.repo), self._git("status", "--short")
        with patch("src.developer.recovery_evaluation._apply_text", side_effect=AssertionError("rollback considered")):
            result = self._evaluate(verification)
        self.assertEqual("no_recovery_required", result["classification"])
        self.assertEqual(["human_lifecycle_review"], result["candidate_actions"])
        self.assertFalse(result["rollback_feasible"])
        self.assertFalse(result["retry_eligible"])
        self.assertFalse(result["execution_authorized"])
        self.assertTrue(result["human_review_required"])
        self.assertEqual(source, (fixture.repo / "app.py").read_bytes())
        self.assertEqual((head, index, status), (self._git("rev-parse", "HEAD"), _git_index_state(fixture.repo), self._git("status", "--short")))
        self.assertEqual(result["evaluation_id"], self._evaluate(verification)["evaluation_id"])

    def test_failed_test_has_exact_safe_rollback_candidate_without_mutation(self):
        fixture = self.fixture
        fixture._reapply_with_test_mode("fail")
        observation = fixture.run_tests("tests.test_app.AppTests.test_value")
        verification = self._verify(observation)
        before = (fixture.repo / "app.py").read_bytes()
        result = self._evaluate(verification)
        self.assertEqual("failed_tests", result["classification"])
        self.assertIn("new_proposal_required", result["candidate_actions"])
        self.assertIn("rollback_candidate", result["candidate_actions"])
        self.assertTrue(result["rollback_feasible"])
        candidate = result["rollback_candidate"]
        self.assertEqual(fixture.applied["run_id"], candidate["execution_run_id"])
        self.assertEqual(["app.py"], candidate["target_paths"])
        self.assertFalse(candidate["execution_authorized"])
        self.assertTrue(candidate["human_approval_required"])
        self.assertFalse(result["retry_eligible"])
        self.assertEqual(1, result["retry_boundary"]["maximum_future_attempts"])
        self.assertEqual(before, (fixture.repo / "app.py").read_bytes())
        self.assertEqual(b"M app.py", self._git("status", "--short").strip())

    def test_stale_repository_blocks_historical_candidate(self):
        fixture = self.fixture
        fixture._reapply_with_test_mode("fail")
        verification = self._verify(fixture.run_tests("tests.test_app.AppTests.test_value"))
        (fixture.repo / "unrelated.txt").write_text("developer work\n", encoding="utf-8")
        result = self._evaluate(verification)
        self.assertEqual("stale_repository", result["classification"])
        self.assertFalse(result["rollback_feasible"])
        self.assertIn("changed_paths_differ_from_phase69", result["blocking_conditions"])
        self.assertTrue((fixture.repo / "unrelated.txt").is_file())

    def test_unexpected_test_side_effect_requires_inspection_and_preserves_artifact(self):
        fixture = self.fixture
        fixture._reapply_with_test_mode("side-effect")
        observation = fixture.run_tests("tests.test_app.AppTests.test_side_effect")
        verification = self._verify(observation)
        result = self._evaluate(verification)
        self.assertEqual("unexpected_side_effect", result["classification"])
        self.assertIn("manual_investigation_required", result["candidate_actions"])
        self.assertTrue(any("unexpected_repository_side_effects" in row for row in result["blocking_conditions"]))
        self.assertFalse(result["rollback_feasible"])
        self.assertTrue((fixture.repo / "side-effect.txt").is_file())

    def test_uncertainty_does_not_become_failure_or_retry(self):
        fixture = self.fixture
        fixture._reapply_with_test_mode("git-refresh", uncertain=True)
        verification = self._verify(fixture.run_tests("tests.test_app.AppTests.test_value"))
        result = self._evaluate(verification)
        self.assertEqual("uncertain_verification", result["classification"])
        self.assertEqual(["additional_evidence_required"], result["candidate_actions"])
        self.assertTrue(result["remaining_uncertainty"])
        self.assertFalse(result["rollback_feasible"])
        self.assertFalse(result["retry_eligible"])

    def test_test_selection_mismatch_is_manual_and_nonactionable(self):
        fixture = self.fixture
        fixture._reapply_with_test_mode("skip")
        observation = fixture.run_tests("tests.test_app.AppTests.test_skipped")
        verification = self._verify(observation)
        result = self._evaluate(verification)
        self.assertEqual("verification_mismatch", result["classification"])
        self.assertEqual(["manual_investigation_required"], result["candidate_actions"])
        self.assertIn("phase65_expected_tests_differ_from_phase70_executed_tests",
                      result["blocking_conditions"])
        self.assertFalse(result["rollback_feasible"])
        self.assertFalse(result["retry_eligible"])

    def test_tampered_missing_wrong_repository_and_wrong_chain_fail_closed(self):
        fixture = self.fixture
        observation = fixture.run_tests("tests.test_app.AppTests.test_value")
        verification = self._verify(observation)
        path = fixture.workspace.root / "runs" / verification["run_id"] / "results.json"
        original = path.read_bytes()
        path.write_bytes(original.replace(b'"status": "verified"', b'"status": "uncertain"'))
        with self.assertRaises(LocalWorkflowError):
            self._evaluate(verification)
        path.write_bytes(original)
        with self.assertRaises(LocalWorkflowError):
            evaluate_recovery(fixture.workspace, fixture.repo, "0" * 20)
        other = fixture.repo.parent / "other"
        other.mkdir()
        subprocess.run(["git", "-C", str(other), "init", "--quiet"], check=True)
        (other / "other.py").write_text("VALUE = 1\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(other), "add", "other.py"], check=True)
        subprocess.run(["git", "-C", str(other), "-c", "user.name=Test", "-c",
                        "user.email=test@example.invalid", "commit", "--quiet", "-m", "initial"], check=True)
        with self.assertRaises(LocalWorkflowError):
            evaluate_recovery(fixture.workspace, other, verification["run_id"])
        wrong = dict(verification)
        wrong["execution_run_id"] = "0" * 20
        wrong.pop("run_id")
        from src.developer.local_workflow import scan_local_repository
        wrong["run_id"] = fixture.workspace._record_run("verify-execution", scan_local_repository(fixture.repo), wrong)
        with self.assertRaises(LocalWorkflowError):
            self._evaluate(wrong)
        wrong_identity = dict(verification)
        wrong_identity["verification_id"] = "verification-" + "0" * 20
        wrong_identity.pop("run_id")
        wrong_identity["run_id"] = fixture.workspace._record_run(
            "verify-execution", scan_local_repository(fixture.repo), wrong_identity)
        with self.assertRaises(LocalWorkflowError):
            self._evaluate(wrong_identity)

    def test_ambiguous_or_missing_linked_evidence_fails_closed(self):
        fixture = self.fixture
        verification = self._verify(fixture.run_tests("tests.test_app.AppTests.test_value"))
        value = dict(verification)
        value["evidence_references"] = value["evidence_references"] + [value["evidence_references"][0]]
        value.pop("run_id")
        from src.developer.local_workflow import scan_local_repository
        value["run_id"] = fixture.workspace._record_run("verify-execution", scan_local_repository(fixture.repo), value)
        with self.assertRaises(LocalWorkflowError):
            self._evaluate(value)

    def test_malformed_recovery_contract_cannot_grant_execution(self):
        fixture = self.fixture
        verification = self._verify(fixture.run_tests("tests.test_app.AppTests.test_value"))
        result = self._evaluate(verification)
        fields = {name: value for name, value in result.items() if name not in {"mode", "run_id"}}
        for name in ("candidate_actions", "blocking_conditions", "reasons", "remaining_uncertainty",
                     "evidence_references"):
            fields[name] = tuple(fields[name])
        fields["execution_authorized"] = True
        with self.assertRaises(ValueError):
            RecoveryEvaluation(**fields)


if __name__ == "__main__":
    unittest.main()
