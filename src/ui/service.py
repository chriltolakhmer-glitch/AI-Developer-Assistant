"""Thin adapters for explicit repository operations and review-only Phase 67."""

from pathlib import Path
from typing import Any

from src.config import PrototypeConfig


class RepositoryService:
    def __init__(self, config: PrototypeConfig):
        self.config = config

    def _workspace(self, workspace: str):
        from src.developer.local_workflow import DeveloperWorkspace
        return DeveloperWorkspace(Path(workspace), research_roots=(
            self.config.data_root, self.config.corpus_root,
            self.config.validation_output, self.config.embedding_model_cache,
        ))

    def read_repository(self, repository: str, workspace: str) -> dict[str, Any]:
        from src.developer.ui_read import read_repository
        return read_repository(self._workspace(workspace), Path(repository))

    def scan(self, repository: str, workspace: str) -> dict[str, Any]:
        return self._workspace(workspace).scan(Path(repository))

    def index(self, repository: str, workspace: str) -> dict[str, Any]:
        return self._workspace(workspace).index(Path(repository))

    def catalog_tests(self, repository: str, workspace: str) -> dict[str, list[str]]:
        from src.developer.local_workflow import scan_local_repository
        from src.developer_testing import catalog
        developer = self._workspace(workspace)
        inventory = scan_local_repository(Path(repository))
        developer._validate_isolation(inventory.root)
        return catalog(inventory.root)

    def plan(self, repository: str, workspace: str, *, goal: str,
             top_k: int = 10, expected_tests: tuple[str, ...] = ()) -> dict[str, Any]:
        from src.developer.implementation_planning import plan_change
        return plan_change(self._workspace(workspace), Path(repository), goal=goal,
                           top_k=top_k, expected_tests=expected_tests)

    def import_candidate(self, repository: str, workspace: str, *, plan_run_id: str,
                         proposal: dict[str, Any], patch_path: str) -> dict[str, Any]:
        from src.developer.patch_drafting import SuppliedPatchGenerator, draft_patch
        root = Path(repository).expanduser().resolve()
        candidate = Path(patch_path).expanduser().resolve(strict=True)
        if candidate == root or root in candidate.parents:
            raise ValueError("Candidate patch file must be outside the target repository.")
        # Binary read preserves CRLF and all other UTF-8 text exactly.
        text = candidate.read_bytes().decode("utf-8")
        return draft_patch(self._workspace(workspace), root, proposal,
                           SuppliedPatchGenerator(text), plan_run_id=plan_run_id)

    def review_patch(self, repository: str, workspace: str, *, patch_run_id: str) -> dict[str, Any]:
        from src.developer.ui_read import review_patch
        return review_patch(self._workspace(workspace), Path(repository), patch_run_id)

    def decide(self, repository: str, workspace: str, *, patch_run_id: str,
               decision: str, approved_by: str, note: str | None,
               expected_branch: str | None = None) -> dict[str, Any]:
        from src.developer.patch_authorization import record_patch_decision
        from src.developer.ui_read import _git_read
        from src.developer.local_workflow import LocalWorkflowError
        root = Path(repository).expanduser().resolve(strict=True)
        developer = self._workspace(workspace)
        developer._validate_isolation(root)
        if decision == "approve" and expected_branch is not None:
            branch = _git_read(root, "rev-parse", "--symbolic-full-name", "HEAD").decode("utf-8", errors="replace").strip()
            if branch != expected_branch:
                raise LocalWorkflowError("Repository branch context changed; reload the session and review explicitly.")
        return record_patch_decision(developer, root, patch_run_id,
                                     decision, approved_by=approved_by, note=note)

    def apply(self, repository: str, workspace: str, authorization_run_id: str) -> dict[str, Any]:
        from src.developer.patch_application import apply_approved_patch
        return apply_approved_patch(self._workspace(workspace), Path(repository), authorization_run_id)

    def test(self, repository: str, workspace: str, execution_run_id: str) -> dict[str, Any]:
        from src.developer.test_execution import execute_applied_patch_tests
        return execute_applied_patch_tests(self._workspace(workspace), Path(repository), execution_run_id, tests=())

    def verify(self, repository: str, workspace: str, execution_run_id: str,
               observation_run_id: str) -> dict[str, Any]:
        from src.developer.execution_verification import verify_execution
        return verify_execution(self._workspace(workspace), Path(repository), execution_run_id, observation_run_id)

    def evaluate(self, repository: str, workspace: str, verification_run_id: str) -> dict[str, Any]:
        from src.developer.recovery_evaluation import evaluate_recovery
        return evaluate_recovery(self._workspace(workspace), Path(repository), verification_run_id)

    def read_log(self, repository: str, workspace: str, observation_run_id: str,
                 stream: str, offset: int = 0) -> dict[str, Any]:
        from src.developer.ui_read import read_observation_log
        return read_observation_log(self._workspace(workspace), Path(repository),
                                    observation_run_id, stream, offset)
