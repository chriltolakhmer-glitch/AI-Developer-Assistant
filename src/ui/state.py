"""Display state only; no persisted evidence or execution authority."""

from dataclasses import dataclass, field
from typing import Any
from copy import deepcopy


@dataclass(frozen=True)
class ReadRequest:
    generation: int
    token: int
    repository: str
    workspace: str
    operation: str = "read_repository"
    goal: str = ""
    expected_tests: tuple[str, ...] = ()
    top_k: int = 10
    plan_run_id: str = ""
    proposal: dict[str, Any] | None = None
    patch_path: str = ""


@dataclass
class ViewState:
    repository: str = ""
    workspace: str = ""
    loading: bool = False
    facts: dict[str, Any] | None = None
    error: str | None = None
    generation: int = 0
    token: int = 0
    close_pending: bool = False
    goal: str = ""
    selected_tests: tuple[str, ...] = ()
    scan_result: dict[str, Any] | None = None
    index_result: dict[str, Any] | None = None
    test_catalog: dict[str, list[str]] | None = None
    plan_result: dict[str, Any] | None = None
    candidate_path: str = ""
    selected_plan_run_id: str = ""
    candidate_result: dict[str, Any] | None = None
    operation: str | None = None
    _active: ReadRequest | None = field(default=None, repr=False)

    def clear_candidate(self):
        self.candidate_result = None

    def candidate_inputs(self, path: str, plan_run_id: str):
        if not self.plan_result or plan_run_id != self.plan_result.get('run_id'):
            plan_run_id = ''
        if (path, plan_run_id) != (self.candidate_path, self.selected_plan_run_id):
            self.generation += 1
            self.candidate_path, self.selected_plan_run_id = path, plan_run_id
            self.clear_candidate()
            self.error = None

    def select(self, repository: str, workspace: str) -> None:
        if (repository, workspace) != (self.repository, self.workspace):
            self.generation += 1
            self.repository, self.workspace = repository, workspace
            self.facts, self.error = None, None
            self.scan_result = self.index_result = self.test_catalog = self.plan_result = None
            self.selected_tests = ()
            self.selected_plan_run_id = ""
            self.clear_candidate()

    def planning_inputs(self, goal: str, tests: tuple[str, ...]) -> None:
        if (goal, tests) != (self.goal, self.selected_tests):
            self.generation += 1
            self.goal, self.selected_tests = goal, tests
            self.plan_result = None
            self.selected_plan_run_id = ""
            self.clear_candidate()

    def begin(self, repository: str, workspace: str) -> ReadRequest | None:
        if self.loading or self.close_pending:
            return None
        self.select(repository, workspace)
        self.facts, self.error = None, None
        self.plan_result = None
        self.selected_plan_run_id = ""
        self.clear_candidate()
        if not repository.strip() or not workspace.strip():
            self.error = "Choose or enter both a repository root and an external workspace."
            return None
        self.token += 1
        self.loading = True
        self.operation = "read_repository"
        self._active = ReadRequest(self.generation, self.token, repository, workspace)
        return self._active

    def begin_operation(self, operation: str, repository: str, workspace: str) -> ReadRequest | None:
        if operation == "read_repository":
            return self.begin(repository, workspace)
        if self.loading or self.close_pending:
            return None
        if operation not in {"scan", "index", "catalog_tests", "plan", "import_candidate"}:
            raise ValueError("Unsupported UI operation")
        self.select(repository, workspace)
        self.error = None
        if self.facts is None:
            self.error = "Open the selected repository before requesting an operation."
            return None
        if operation == "plan" and not self.goal.strip():
            self.error = "Development goal must be nonempty text."
            return None
        if operation in {"scan", "index", "plan"}:
            self.plan_result = None
            self.selected_plan_run_id = ""
            self.clear_candidate()
        if operation == "import_candidate":
            self.clear_candidate()
            plan = self.plan_result or {}
            proposal = plan.get("proposed_action")
            if (plan.get("status") != "completed" or not self.selected_plan_run_id
                    or self.selected_plan_run_id != plan.get("run_id")
                    or not isinstance(proposal, dict) or not proposal.get("action_id")
                    or not self.candidate_path):
                self.error = "Select a completed Phase 65 plan and an external candidate file. Backend validation remains required."
                return None
        if operation == "scan":
            self.scan_result = None
        if operation == "index":
            self.index_result = None
        self.token += 1
        self.loading, self.operation = True, operation
        self._active = ReadRequest(self.generation, self.token, repository, workspace,
                                   operation, self.goal, self.selected_tests,
                                   plan_run_id=self.selected_plan_run_id,
                                   proposal=deepcopy(self.plan_result.get("proposed_action")) if operation == "import_candidate" else None,
                                   patch_path=self.candidate_path)
        return self._active

    def complete(self, request: ReadRequest, facts: dict[str, Any] | None, error: str | None) -> bool:
        if request != self._active:
            return False
        self.loading, self._active = False, None
        if request.generation != self.generation:
            return False
        self.error = error
        if request.operation != "read_repository":
            if facts is not None:
                field_name = {"scan": "scan_result", "index": "index_result",
                              "catalog_tests": "test_catalog", "plan": "plan_result",
                              "import_candidate": "candidate_result"}[request.operation]
                if request.operation == "plan":
                    self.selected_plan_run_id = ""
                    self.clear_candidate()
                setattr(self, field_name, facts)
            return True
        self.facts = facts
        if facts is not None:
            self.repository = facts["repository_path"]
            self.workspace = facts["workspace_path"]
        return True
