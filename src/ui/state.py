"""Display state only; no persisted evidence or execution authority."""

from dataclasses import dataclass, field
from typing import Any


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
    operation: str | None = None
    _active: ReadRequest | None = field(default=None, repr=False)

    def select(self, repository: str, workspace: str) -> None:
        if (repository, workspace) != (self.repository, self.workspace):
            self.generation += 1
            self.repository, self.workspace = repository, workspace
            self.facts, self.error = None, None
            self.scan_result = self.index_result = self.test_catalog = self.plan_result = None
            self.selected_tests = ()

    def planning_inputs(self, goal: str, tests: tuple[str, ...]) -> None:
        if (goal, tests) != (self.goal, self.selected_tests):
            self.generation += 1
            self.goal, self.selected_tests = goal, tests
            self.plan_result = None

    def begin(self, repository: str, workspace: str) -> ReadRequest | None:
        if self.loading or self.close_pending:
            return None
        self.select(repository, workspace)
        self.facts, self.error = None, None
        self.plan_result = None
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
        if operation not in {"scan", "index", "catalog_tests", "plan"}:
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
        if operation == "scan":
            self.scan_result = None
        if operation == "index":
            self.index_result = None
        self.token += 1
        self.loading, self.operation = True, operation
        self._active = ReadRequest(self.generation, self.token, repository, workspace,
                                   operation, self.goal, self.selected_tests)
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
                              "catalog_tests": "test_catalog", "plan": "plan_result"}[request.operation]
                setattr(self, field_name, facts)
            return True
        self.facts = facts
        if facts is not None:
            self.repository = facts["repository_path"]
            self.workspace = facts["workspace_path"]
        return True
