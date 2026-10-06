"""Focused Phase 65 evidence-grounded implementation-planning coverage."""

from contextlib import redirect_stderr, redirect_stdout
import difflib
from io import StringIO
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from src.cli import main
from src.developer.implementation_planning import ProposedAction, plan_change
from src.developer.local_workflow import DeveloperWorkspace, LocalWorkflowError


class _Tokenizer:
    def __call__(self, text, add_special_tokens=True, **kwargs):
        return {"input_ids": [1] * max(1, len(text.split()) + (2 if add_special_tokens else 0))}


class _Model:
    tokenizer = _Tokenizer()

    def encode(self, texts, **kwargs):
        vectors = np.ones((len(texts), 384), dtype=np.float32)
        return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


class ImplementationPlanningTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repository = self.root / "repository"
        self.workspace_path = self.root / "workspace"
        (self.repository / "src").mkdir(parents=True)
        (self.repository / "tests").mkdir()
        (self.repository / "src" / "config.py").write_text("TOKEN_MODE = 'strict'\n", encoding="utf-8")
        (self.repository / "src" / "helpers.py").write_text(
            "def validate(value):\n    if not value:\n        raise ValueError('missing')\n    return value\n",
            encoding="utf-8",
        )
        (self.repository / "src" / "app.py").write_text(
            "from src.config import TOKEN_MODE\nfrom src.helpers import validate\n\n"
            "def run(value):\n    return validate(value) if TOKEN_MODE else value\n\n"
            "def unrelated():\n    return 'nearby'\n",
            encoding="utf-8",
        )
        (self.repository / "tests" / "test_app.py").write_text(
            "from src.app import run\n\nimport unittest\n\nclass AppTests(unittest.TestCase):\n"
            "    def test_run(self):\n        self.assertEqual('x', run('x'))\n",
            encoding="utf-8",
        )
        self.git("init", "--quiet")
        self.git("config", "user.name", "Phase 65 Test")
        self.git("config", "user.email", "phase65@example.invalid")
        self.git("add", "--all")
        self.git("commit", "--quiet", "-m", "baseline")
        self.developer = DeveloperWorkspace(self.workspace_path, (self.root / "research",))

    def git(self, *arguments):
        return subprocess.run(
            ["git", "-C", str(self.repository), *arguments], check=True,
            capture_output=True, text=True,
        ).stdout.strip()

    def index(self):
        with patch("src.developer.local_workflow.load_model", return_value=_Model()):
            self.developer.index(self.repository)

    @staticmethod
    def query_payload(question="Add validation to run"):
        return {
            "question": question,
            "results": [{
                "file_path": "src/app.py", "qualified_name": "run", "start_line": 4,
                "end_line": 5, "rank": 1, "ranking_reason": {"matched_metadata_terms": ["run"]},
                "chunk_id": "run-id", "related_context": [{"file_path": "src/helpers.py",
                "symbol_name": "validate", "reason": "call relationship"}],
            }],
            "context": {"relationship_diagnostics": [], "omitted_context": [],
                        "included_context": [{"file_path": "src/app.py", "symbol_name": "run"}]},
            "run_id": "query-run",
        }

    def plan(self, goal="Add validation to run", query=None):
        query = self.query_payload(goal) if query is None else query
        with patch("src.developer.local_workflow.load_model", return_value=_Model()), \
                patch.object(self.developer, "query", return_value=query):
            return plan_change(self.developer, self.repository, goal=goal)

    def source_snapshot(self):
        return {path.relative_to(self.repository).as_posix(): path.read_bytes()
                for path in self.repository.rglob("*") if path.is_file() and ".git" not in path.parts}

    def test_clean_current_index_uses_goal_retrieval_with_traceable_targets(self):
        self.index()
        before = self.source_snapshot()
        report = self.plan()
        self.assertEqual("developer-local-implementation-plan", report["mode"])
        self.assertEqual("completed", report["status"])
        self.assertEqual([], report["change_impact"]["changes"]["files"])
        targets = {(row["file_path"], row["qualified_symbol"]): row
                   for row in report["implementation_targets"]}
        self.assertEqual("primary_target", targets[("src/app.py", "run")]["role"])
        self.assertEqual("related_context", targets[("src/helpers.py", "validate")]["role"])
        self.assertIn("retrieval_evidence", targets[("src/app.py", "run")]["evidence_types"])
        self.assertTrue(targets[("src/app.py", "run")]["current_index_evidence"])
        self.assertEqual(list(range(1, len(report["implementation_steps"]) + 1)),
                         [row["order"] for row in report["implementation_steps"]])
        self.assertEqual("T4_final_gate", report["recommended_validation"][-1]["scope"])
        self.assertFalse(report["tests_executed"])
        self.assertFalse(report["source_changes_made"])
        self.assertEqual(before, self.source_snapshot())

    def test_clean_start_binds_existing_exact_tests_from_planned_imports(self):
        self.index()
        report = self.plan()
        selected = report["tests"]["expected_test_selection"]
        self.assertEqual("known", selected["status"])
        self.assertEqual(["tests.test_app.AppTests.test_run"], selected["selected_tests"])
        self.assertEqual(selected["selected_tests"], report["tests"]["selected_tests"])
        self.assertEqual("planned_target_static_import", selected["evidence"][0]["source"])
        self.assertIn("src/app.py", selected["evidence"][0]["target_paths"])

    def test_omitted_context_for_exactly_bound_test_is_visible_warning(self):
        self.index()
        query = self.query_payload()
        query["context"]["omitted_context"] = [{
            "chunk_id": "omitted-test-chunk", "file_path": "tests/test_app.py",
            "symbol_name": "AppTests.test_run", "reason": "relationship expansion limit",
        }]
        report = self.plan(query=query)
        omission = next(row for row in report["warnings"] if row["type"] == "retrieval_omission")
        self.assertEqual("non_blocking", omission["classification"])
        self.assertEqual("exact_expected_test_binding", omission["basis"]["kind"])
        self.assertIn("tests.test_app.AppTests.test_run",
                      report["tests"]["expected_test_selection"]["selected_tests"])
        self.assertNotIn("omitted_context", {row["type"] for row in report["unresolved_evidence"]})
        self.assertEqual("completed", report["status"])

    def test_omitted_test_module_and_class_are_warnings_when_all_catalogued_tests_are_bound(self):
        self.index()
        query = self.query_payload()
        query["context"]["omitted_context"] = [
            {"chunk_id": "omitted-test-class", "file_path": "tests/test_app.py",
             "symbol_name": "AppTests", "reason": "relationship expansion limit"},
            {"chunk_id": "omitted-test-module", "file_path": "tests/test_app.py",
             "symbol_name": "tests.test_app", "reason": "relationship expansion limit"},
        ]
        report = self.plan(query=query)
        warnings = [row for row in report["warnings"] if row["type"] == "retrieval_omission"]
        self.assertEqual({"exact_expected_test_container_binding"},
                         {row["basis"]["kind"] for row in warnings})
        self.assertEqual(2, len(warnings))
        self.assertEqual("completed", report["status"])
        self.assertFalse(any(row["type"] == "omitted_context" for row in report["unresolved_evidence"]))

    def test_omitted_context_without_independent_target_or_test_evidence_blocks(self):
        self.index()
        query = self.query_payload()
        query["context"]["omitted_context"] = [{
            "chunk_id": "unproven-contract-chunk", "file_path": "tests/test_app.py",
            "symbol_name": "AppTests.test_discount_contract", "reason": "relationship expansion limit",
        }]
        report = self.plan(query=query)
        omission = next(row for row in report["unresolved_evidence"] if row["type"] == "omitted_context")
        self.assertEqual("blocking", omission["classification"])
        self.assertIsNone(omission["basis"])
        self.assertEqual("limited", report["status"])

    def test_omitted_dependency_is_warning_only_when_selected_chunk_proves_exact_edge(self):
        self.index()
        query = self.query_payload()
        query["results"][0]["developer_context"] = {
            "import_bindings": [{"module": "src.helpers", "imported_name": "validate",
                                 "binding": "validate"}],
            "called_symbol_names": ["validate"],
            "relationship_references": [{"file_path": "src/helpers.py", "symbol": "validate",
                                          "kind": "call_relationship"}],
        }
        query["results"][0]["relationship_references"] = query["results"][0]["developer_context"]["relationship_references"]
        query["context"]["omitted_context"] = [{
            "chunk_id": "omitted-helper", "file_path": "src/helpers.py",
            "symbol_name": "validate", "reason": "relationship expansion limit",
        }]
        report = self.plan(query=query)
        omission = next(row for row in report["warnings"] if row["type"] == "retrieval_omission")
        self.assertEqual("non_blocking", omission["classification"])
        self.assertEqual("selected_context_relationship", omission["basis"]["kind"])
        self.assertEqual("src/helpers.py", omission["basis"]["target"]["file_path"])
        self.assertFalse(any(row["type"] == "omitted_context" for row in report["unresolved_evidence"]))

    def test_omitted_module_container_is_warning_only_when_exact_relationship_is_included(self):
        self.index()
        query = self.query_payload()
        query["results"][0]["developer_context"] = {
            "relationship_references": [{"file_path": "src/helpers.py", "symbol": "src.helpers",
                                          "kind": "importer_relationship"}],
        }
        query["results"][0]["relationship_references"] = query["results"][0]["developer_context"]["relationship_references"]
        query["context"]["omitted_context"] = [{
            "chunk_id": "omitted-module", "file_path": "src/helpers.py",
            "symbol_name": "src.helpers", "reason": "relationship expansion limit",
        }]
        report = self.plan(query=query)
        omission = next(row for row in report["warnings"] if row["type"] == "retrieval_omission")
        self.assertEqual("selected_context_relationship", omission["basis"]["kind"])

    def test_omitted_import_without_exact_call_or_relationship_remains_blocking(self):
        self.index()
        query = self.query_payload()
        query["results"][0]["developer_context"] = {
            "import_bindings": [{"module": "src.helpers", "imported_name": "validate",
                                 "binding": "validate"}],
            "called_symbol_names": [],
            "relationship_references": [],
        }
        query["context"]["omitted_context"] = [{
            "chunk_id": "omitted-helper", "file_path": "src/helpers.py",
            "symbol_name": "validate", "reason": "relationship expansion limit",
        }]
        report = self.plan(query=query)
        omission = next(row for row in report["unresolved_evidence"] if row["type"] == "omitted_context")
        self.assertEqual("blocking", omission["classification"])

    def test_validated_plan_accepts_canonical_proposal_and_rejects_tampering(self):
        from src.developer.proposal_evidence import validated_plan
        from src.developer.local_workflow import _json_bytes
        self.index()
        report = self.plan()
        _, proposal = validated_plan(self.developer, self.repository, report["run_id"])
        self.assertEqual(report["proposed_action"], proposal.to_dict())
        result_path = self.workspace_path / "runs" / report["run_id"] / "results.json"
        original = result_path.read_bytes()
        for alteration in (lambda row: row.update(goal="Forged goal"),
                           lambda row: row["proposed_action"].update(action_id="proposal-forged"),
                           lambda row: row["proposed_action"].update(evidence_refs=[]),
                           lambda row: row["tests"].update(selected_tests=[])):
            changed = json.loads(original)
            alteration(changed)
            result_path.write_bytes(_json_bytes(changed))
            with self.assertRaisesRegex(LocalWorkflowError, "missing, malformed, or tampered"):
                validated_plan(self.developer, self.repository, report["run_id"])
            result_path.write_bytes(original)
        with self.assertRaises(LocalWorkflowError):
            validated_plan(DeveloperWorkspace(self.root / "wrong-workspace"), self.repository,
                           report["run_id"])
        other = self.root / "other-repository"
        other.mkdir()
        with self.assertRaisesRegex(LocalWorkflowError, "repository bindings differ"):
            validated_plan(self.developer, other, report["run_id"])
        impact_run = report["change_impact"]["run_id"]
        impact_path = self.workspace_path / "runs" / impact_run / "results.json"
        impact_bytes = impact_path.read_bytes()
        impact_path.unlink()
        with self.assertRaisesRegex(LocalWorkflowError, "missing, malformed, or tampered"):
            validated_plan(self.developer, self.repository, report["run_id"])
        impact_path.write_bytes(impact_bytes)
        (self.repository / "src" / "app.py").write_text("VALUE = 5\n", encoding="utf-8")
        with self.assertRaisesRegex(LocalWorkflowError, "stale"):
            validated_plan(self.developer, self.repository, report["run_id"])

    def test_cli_draft_accepts_only_validated_clean_start_plan(self):
        self.index()
        report = self.plan()
        source = (self.repository / "src" / "app.py").read_text(encoding="utf-8")
        candidate = source.replace("return validate(value) if TOKEN_MODE else value",
                                   "return validate(value) if TOKEN_MODE else str(value)")
        diff = "".join(difflib.unified_diff(source.splitlines(keepends=True),
                                            candidate.splitlines(keepends=True),
                                            fromfile="a/src/app.py", tofile="b/src/app.py"))
        patch_path = self.root / "candidate.diff"
        patch_path.write_text(diff, encoding="utf-8")
        output, error = StringIO(), StringIO()
        with redirect_stdout(output), redirect_stderr(error):
            code = main(["local", "draft-patch", str(self.repository), "--proposal-run-id",
                         report["run_id"], "--patch-file", str(patch_path), "--workspace",
                         str(self.workspace_path), "--json"])
        self.assertEqual(0, code, error.getvalue())
        draft = json.loads(output.getvalue())
        self.assertEqual("draft", draft["status"])
        self.assertEqual(report["run_id"], draft["source_plan_run_id"])
        self.assertEqual(["src/app.py"], draft["candidate_paths"])

    def test_clean_start_expected_tests_continue_through_recovery_without_reselection(self):
        from src.developer.patch_drafting import SuppliedPatchGenerator, draft_patch
        from src.developer.patch_authorization import record_patch_decision
        from src.developer.patch_application import apply_approved_patch
        from src.developer.test_execution import execute_applied_patch_tests
        from src.developer.execution_verification import verify_execution
        from src.developer.recovery_evaluation import evaluate_recovery

        (self.repository / "tests" / "__init__.py").write_text("", encoding="utf-8")
        with (self.repository / "tests" / "test_app.py").open("a", encoding="utf-8") as target:
            target.write("\n    def test_other(self):\n        self.assertTrue(True)\n")
        self.git("add", "--all")
        self.git("commit", "--quiet", "-m", "package tests")
        self.index()
        report = self.plan()
        expected = report["tests"]["selected_tests"]
        self.assertEqual(["tests.test_app.AppTests.test_other", "tests.test_app.AppTests.test_run"], expected)
        source = (self.repository / "src" / "app.py").read_text(encoding="utf-8")
        candidate = source.replace("return validate(value) if TOKEN_MODE else value",
                                   "return validate(value) if TOKEN_MODE else str(value)")
        diff = "".join(difflib.unified_diff(source.splitlines(keepends=True),
                                            candidate.splitlines(keepends=True),
                                            fromfile="a/src/app.py", tofile="b/src/app.py"))
        draft = draft_patch(self.developer, self.repository, report["proposed_action"],
                            SuppliedPatchGenerator(diff), plan_run_id=report["run_id"])
        self.assertEqual("draft", draft["status"])
        approval = record_patch_decision(self.developer, self.repository, draft["run_id"], "approve")
        applied = apply_approved_patch(self.developer, self.repository, approval["run_id"])
        with self.assertRaisesRegex(LocalWorkflowError, "differ from the approved Phase 65"):
            execute_applied_patch_tests(self.developer, self.repository, applied["run_id"],
                                        tests=(expected[0],))
        observation = execute_applied_patch_tests(self.developer, self.repository, applied["run_id"])
        self.assertEqual(expected, observation["test_identities"])
        self.assertEqual("passed", observation["status"])
        verified = verify_execution(self.developer, self.repository, applied["run_id"], observation["run_id"])
        self.assertEqual("verified", verified["status"],
                         (verified.get("deviations"), repr(diff), repr(applied.get("diff_after"))))
        recovery = evaluate_recovery(self.developer, self.repository, verified["run_id"])
        self.assertEqual("no_recovery_required", recovery["classification"])

    def test_unknown_expected_tests_require_a_human_test_decision(self):
        (self.repository / "tests" / "test_app.py").write_text(
            "import unittest\nclass AppTests(unittest.TestCase):\n"
            "    def test_run(self):\n        self.assertTrue(True)\n", encoding="utf-8")
        self.git("add", "--all")
        self.git("commit", "--quiet", "-m", "unrelated test")
        self.index()
        report = self.plan()
        self.assertEqual("unknown", report["tests"]["expected_test_selection"]["status"])
        self.assertEqual([], report["tests"]["selected_tests"])
        self.assertIn("expected_tests_unknown", {row["type"] for row in report["unresolved_evidence"]})

    def test_explicit_expected_test_must_exist(self):
        self.index()
        with patch("src.developer.local_workflow.load_model", return_value=_Model()), \
                patch.object(self.developer, "query", return_value=self.query_payload()), \
                self.assertRaisesRegex(LocalWorkflowError, "exact existing unittest"):
            plan_change(self.developer, self.repository, goal="Add validation to run",
                        expected_tests=("tests.test_app.AppTests.test_missing",))

    def test_phase66_typing_creates_reviewable_proposal_contract(self):
        self.index()
        report = self.plan()
        proposal = report["proposed_action"]
        self.assertEqual("implementation_plan", proposal["action_type"])
        self.assertEqual("human_approval_required", proposal["authority_required"])
        self.assertEqual("developer-local-implementation-plan", proposal["source_mode"])
        self.assertEqual("1.0", proposal["schema_version"])
        self.assertTrue(proposal["action_id"].startswith("proposal-"))
        self.assertEqual("Add validation to run", proposal["goal"])
        self.assertIn("src/app.py", proposal["target_paths"])
        self.assertTrue(proposal["evidence_refs"])
        self.assertEqual([], report["proposed_action"]["required_mutations"])

    def test_phase66_proposal_is_typed_and_stable(self):
        self.index()
        report = self.plan()
        proposal = ProposedAction.from_plan(
            report["change_impact"],
            report["implementation_targets"],
            report["goal"],
            report["unresolved_evidence"],
        )
        self.assertIsInstance(proposal, ProposedAction)
        self.assertEqual("proposed", proposal.status)
        self.assertFalse(proposal.execution_allowed)
        self.assertEqual("human_approval_required", proposal.authority_required)
        self.assertEqual("implementation_plan", proposal.action_type)
        self.assertEqual(report["goal"], proposal.goal)
        self.assertIn("src/app.py", proposal.target_paths)
        self.assertTrue(proposal.evidence_refs)
        self.assertTrue(proposal.unresolved_evidence)
        self.assertEqual(proposal.to_dict()["action_id"], proposal.action_id)

        duplicated = ProposedAction.from_plan(
            report["change_impact"],
            report["implementation_targets"],
            report["goal"],
            report["unresolved_evidence"],
        )
        self.assertEqual(proposal.action_id, duplicated.action_id)

    def test_phase66_proposal_identity_changes_when_state_changes(self):
        self.index()
        report = self.plan()
        first = ProposedAction.from_plan(
            report["change_impact"],
            report["implementation_targets"],
            report["goal"],
            report["unresolved_evidence"],
        )

        app = self.repository / "src" / "app.py"
        app.write_text(app.read_text(encoding="utf-8").replace("return validate(value) if TOKEN_MODE else value",
                                                            "return validate(value.strip()) if TOKEN_MODE else value"),
                      encoding="utf-8")
        changed = self.plan()
        second = ProposedAction.from_plan(
            changed["change_impact"],
            changed["implementation_targets"],
            changed["goal"],
            changed["unresolved_evidence"],
        )
        self.assertNotEqual(first.action_id, second.action_id)
        self.assertEqual("proposed", second.status)

    def test_modified_code_reuses_relationship_and_test_planner_evidence(self):
        app = self.repository / "src" / "app.py"
        app.write_text(app.read_text(encoding="utf-8").replace("validate(value)", "validate(value.strip())"), encoding="utf-8")
        (self.repository / "src" / "unrelated.py").write_text("def nearby():\n    return 1\n", encoding="utf-8")
        report = self.plan(query={"question": "validation", "results": [], "context": {}, "run_id": "q"})
        self.assertEqual("limited", report["status"])
        run = next(row for row in report["implementation_targets"] if row["qualified_symbol"] == "run")
        self.assertEqual("already_changed", run["change_status"])
        self.assertIn("changed_code", run["evidence_types"])
        self.assertIn("static_relationship", run["evidence_types"])
        self.assertTrue(any(row["kind"] == "static_dependency" for row in report["preserved_behavior"]))
        classifications = {row["classification"] for row in report["tests_to_update_or_review"]}
        self.assertIn("existing_test_to_run", classifications)
        self.assertIn("existing_test_to_review", classifications)
        self.assertIn("possible_new_regression_test", classifications)
        self.assertFalse(any(row["file_path"] == "src/unrelated.py" for row in report["implementation_targets"]))
        self.assertFalse(any(row["qualified_symbol"] == "unrelated" for row in report["implementation_targets"]))

    def test_configuration_controlled_behavior_is_descriptive(self):
        app = self.repository / "src" / "app.py"
        app.write_text(app.read_text(encoding="utf-8").replace("TOKEN_MODE else", "TOKEN_MODE == 'strict' else"), encoding="utf-8")
        report = self.plan("Change configuration-controlled run behavior",
                           query={"question": "configuration", "results": [], "context": {}, "run_id": "q"})
        run = next(row for row in report["implementation_targets"] if row["qualified_symbol"] == "run")
        self.assertEqual("configuration_target", run["role"])
        self.assertTrue(any(row["kind"] == "configuration_reference" for row in report["preserved_behavior"]))
        self.assertTrue(any("runtime execution is not confirmed" in reason
                            for row in report["implementation_targets"] for reason in row["reasons"]))

    def test_stale_index_blocks_retrieval_and_marks_plan_limited(self):
        self.index()
        app = self.repository / "src" / "app.py"
        app.write_text(app.read_text(encoding="utf-8").replace("validate(value)", "validate(value.strip())"), encoding="utf-8")
        with patch("src.developer.local_workflow.load_model", return_value=_Model()), \
                patch.object(self.developer, "query") as query:
            report = plan_change(self.developer, self.repository, goal="improve run error")
        query.assert_not_called()
        self.assertEqual("limited", report["status"])
        self.assertEqual("blocked", report["change_impact"]["retrieval"]["status"])
        self.assertFalse(any("retrieval_evidence" in row["evidence_types"]
                             for row in report["implementation_targets"]))
        self.assertTrue(any(row["type"] == "index_not_current" for row in report["unresolved_evidence"]))

    def test_missing_index_is_explicit_and_does_not_reindex(self):
        with patch.object(self.developer, "index") as index:
            report = self.plan(query={"question": "run", "results": [], "context": {}, "run_id": "q"})
        index.assert_not_called()
        self.assertEqual("manual_review_required", report["status"])
        self.assertEqual("missing", report["change_impact"]["index_freshness"]["status"])
        self.assertIn("prototype local index", next(row["action"] for row in report["unresolved_evidence"]
                                                     if row["type"] == "index_not_current"))

    def test_ambiguous_relationship_is_not_promoted_to_definite_target(self):
        (self.repository / "src" / "a.py").write_text("def ping():\n    return 'a'\n", encoding="utf-8")
        (self.repository / "src" / "b.py").write_text("def ping():\n    return 'b'\n", encoding="utf-8")
        (self.repository / "src" / "caller.py").write_text(
            "from src.a import ping\nfrom src.b import ping\n\ndef call():\n    return ping()\n", encoding="utf-8")
        report = self.plan("Change ping behavior",
                           query={"question": "ping", "results": [], "context": {}, "run_id": "q"})
        self.assertEqual("limited", report["status"])
        ambiguous = [row for row in report["unresolved_evidence"]
                     if row["type"] == "ambiguous_or_unresolved_relationship"]
        self.assertTrue(ambiguous)
        self.assertFalse(any(row["file_path"] in {"src/a.py", "src/b.py"}
                             and "static_relationship" in row["evidence_types"]
                             for row in report["implementation_targets"]))

    def test_unsupported_typescript_goal_fails_closed(self):
        other = self.root / "typescript"
        other.mkdir()
        (other / "app.ts").write_text("export function login() { return true; }\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(other), "init", "--quiet"], check=True)
        subprocess.run(["git", "-C", str(other), "config", "user.name", "Phase 65"], check=True)
        subprocess.run(["git", "-C", str(other), "config", "user.email", "phase65@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(other), "add", "--all"], check=True)
        subprocess.run(["git", "-C", str(other), "commit", "--quiet", "-m", "baseline"], check=True)
        (other / "app.ts").write_text("export function login(value: string) { return !!value; }\n", encoding="utf-8")
        developer = DeveloperWorkspace(self.root / "typescript-workspace")
        with patch("src.developer.local_workflow.load_model", side_effect=RuntimeError("offline")):
            report = plan_change(developer, other, goal="Validate the TypeScript login input")
        self.assertEqual("manual_review_required", report["status"])
        self.assertEqual([], report["implementation_targets"])
        self.assertTrue(any(row["type"] == "unsupported_file" for row in report["unresolved_evidence"]))

    def test_no_evidence_goal_requires_manual_review(self):
        self.index()
        empty = {"question": "quantum billing", "results": [], "context": {}, "run_id": "q"}
        report = self.plan("Add quantum billing teleportation", query=empty)
        self.assertEqual("manual_review_required", report["status"])
        self.assertEqual([], report["implementation_targets"])
        self.assertTrue(any(row["type"] == "missing_implementation_evidence" for row in report["unresolved_evidence"]))

    def test_json_and_human_outputs_are_structured_and_planning_only(self):
        self.index()
        for as_json in (False, True):
            output, error = StringIO(), StringIO()
            args = ["local", "plan-change", str(self.repository), "--workspace", str(self.workspace_path),
                    "--goal", "Add validation to run"]
            if as_json:
                args.append("--json")
            with patch("src.developer.local_workflow.load_model", return_value=_Model()), \
                    patch.object(DeveloperWorkspace, "query", return_value=self.query_payload()), \
                    redirect_stdout(output), redirect_stderr(error):
                status = main(args)
            self.assertEqual(0, status, error.getvalue())
            if as_json:
                payload = json.loads(output.getvalue())
                self.assertEqual("developer-local-implementation-plan", payload["mode"])
                self.assertFalse(payload["tests_executed"])
            else:
                text = output.getvalue()
                self.assertIn("Likely implementation targets:", text)
                self.assertIn("Validation sequence:", text)
                self.assertNotIn('"implementation_targets"', text)

    def test_external_workspace_and_no_patch_or_research_coupling(self):
        before = self.source_snapshot()
        report = self.plan(query={"question": "run", "results": [], "context": {}, "run_id": "q"})
        self.assertEqual(before, self.source_snapshot())
        self.assertTrue((self.workspace_path / "runs" / report["run_id"] / "results.json").is_file())
        with self.assertRaises(LocalWorkflowError):
            plan_change(DeveloperWorkspace(self.repository / "workspace"), self.repository, goal="run")
        source = Path("src/developer/implementation_planning.py").read_text(encoding="utf-8").casefold()
        for forbidden in ("src.research", "humanize", "--apply", "--patch", "subprocess.run"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
