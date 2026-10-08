"""Pure tests for Phase 65/66 evidence presentation preparation."""
import unittest

from src.ui.formatters import format_plan, role_label


class UIPlanFormatterTests(unittest.TestCase):
    def payload(self):
        return {
            "status": "completed", "run_id": "plan-run-exact", "goal": "exact goal",
            "implementation_targets": [
                {"role": "primary_target", "file_path": "src/a.py", "qualified_symbol": "a"},
                {"role": "configuration_target", "file_path": "src/config.py", "qualified_symbol": "load"},
                {"role": "supporting_target", "file_path": "src/helper.py", "qualified_symbol": "help"},
                {"role": "test_target", "file_path": "tests/test_a.py", "qualified_symbol": "TestA.test_a"},
                {"role": "related_context", "file_path": "src/related.py", "qualified_symbol": "related"},
                {"role": "manual_review", "unresolved_notes": ["manual"]},
            ],
            "tests": {"selected_tests": ["tests.test_a.TestA.test_a"], "expected_test_selection": {
                "status": "known", "confidence": "developer_selected", "uncertainty": ["runtime review"],
                "evidence": [{"test": "tests.test_a.TestA.test_a", "source": "explicit_developer_selection"}],
            }},
            "unresolved_evidence": [{"type": "needs_human", "reason": "inspect"}],
            "warnings": [{"type": "token_limit_exclusion", "classification": "non_blocking",
                "evidence": {"file_path": "src/container.py", "qualified_name": "container",
                             "reason": "over_limit", "token_count": 300},
                "basis": {"kind": "exact_retained_leaf_evidence",
                    "container": {"file_path": "src/container.py", "qualified_symbol": "container"},
                    "proofs": [{"kind": "exact_retained_primary_leaf", "chunk_id": "chunk-exact",
                        "file_path": "src/container.py", "qualified_symbol": "container.leaf",
                        "content_sha256": "hash-exact", "target_role": "primary_target"}]},
                "action": "Backend retained exact descendants."}],
            "preserved_behavior": [{"kind": "static_dependency", "statement": "keep behavior"}],
            "implementation_steps": [{"order": 1, "action": "inspect", "target_refs": ["src/a.py::a"]}],
            "recommended_validation": [{"order": 1, "selector": "tests.test_a.TestA.test_a", "scope": "focused"}],
            "limitations": ["dynamic behavior needs review"],
            "proposed_action": {"action_id": "proposal-exact", "status": "proposed",
                "action_type": "implementation_plan", "target_paths": ["src/a.py"],
                "target_symbols": ["a"], "unresolved_evidence": [{"type": "needs_human"}],
                "execution_allowed": False, "authority_required": "human_approval_required"},
            "change_impact": {"index_freshness": {"status": "current"},
                              "repository": {"repository_id": "repo-exact", "current_commit": "commit-exact"}},
        }

    def test_exact_role_grouping_keeps_primary_and_configuration_separate(self):
        formatted = format_plan(self.payload())
        self.assertEqual(1, len(formatted["targets_by_role"]["primary_target"]))
        self.assertEqual(1, len(formatted["targets_by_role"]["configuration_target"]))
        self.assertEqual({"primary_target", "configuration_target", "supporting_target", "test_target",
                          "related_context", "manual_review"}, set(formatted["targets_by_role"]))
        self.assertEqual("Primary target (primary_target)", role_label("primary_target"))
        self.assertEqual("Configuration target (configuration_target)", role_label("configuration_target"))

    def test_blockers_and_warnings_and_retained_leaf_are_separate_and_exact(self):
        formatted = format_plan(self.payload())
        self.assertEqual("needs_human", formatted["unresolved_evidence"][0]["type"])
        self.assertEqual("token_limit_exclusion", formatted["warnings"][0]["type"])
        proof = formatted["retained_leaf_proofs"][0]["proof"]
        self.assertEqual("exact_retained_leaf_evidence", proof["kind"])
        self.assertEqual("src/container.py", proof["container"]["file_path"])
        self.assertEqual("exact_retained_primary_leaf", proof["proofs"][0]["kind"])
        self.assertEqual("hash-exact", proof["proofs"][0]["content_sha256"])

    def test_behavior_tests_proposal_steps_validation_and_limitations_are_retained(self):
        formatted = format_plan(self.payload())
        self.assertEqual("keep behavior", formatted["preserved_behavior"][0]["statement"])
        self.assertEqual(["tests.test_a.TestA.test_a"], formatted["selected_tests"])
        self.assertEqual("explicit_developer_selection", formatted["test_evidence"][0]["source"])
        self.assertEqual("proposal-exact", formatted["proposed_action"]["action_id"])
        self.assertEqual("src/a.py::a", formatted["implementation_steps"][0]["target_refs"][0])
        self.assertEqual("focused", formatted["recommended_validation"][0]["scope"])
        self.assertEqual("dynamic behavior needs review", formatted["limitations"][0])

    def test_missing_optional_fields_remain_absent_without_success_defaults(self):
        formatted = format_plan({"status": "manual_review_required", "implementation_targets": [{"role": "odd_role"}]})
        self.assertEqual("manual_review_required", formatted["status"])
        self.assertEqual([{"role": "odd_role"}], formatted["targets_by_role"]["odd_role"])
        self.assertEqual({}, formatted["proposed_action"])
        self.assertEqual([], formatted["limitations"])
        self.assertEqual([], formatted["warnings"])
        self.assertEqual([], formatted["preserved_behavior"])
        self.assertIsNone(formatted["run_id"])
        self.assertEqual([], formatted["retained_leaf_proofs"])

    def test_warning_without_proof_does_not_create_retained_leaf_claim(self):
        payload = self.payload()
        payload["warnings"] = [{"type": "token_limit_exclusion", "reason": "no proof"}]
        self.assertEqual([], format_plan(payload)["retained_leaf_proofs"])


if __name__ == "__main__":
    unittest.main()
