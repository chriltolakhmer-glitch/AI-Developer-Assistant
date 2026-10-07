"""Display state only; no persisted evidence or execution authority."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ReadRequest:
    generation: int
    token: int
    repository: str
    workspace: str


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
    _active: ReadRequest | None = field(default=None, repr=False)

    def select(self, repository: str, workspace: str) -> None:
        if (repository, workspace) != (self.repository, self.workspace):
            self.generation += 1
            self.repository, self.workspace = repository, workspace
            self.facts, self.error = None, None

    def begin(self, repository: str, workspace: str) -> ReadRequest | None:
        if self.loading or self.close_pending:
            return None
        self.select(repository, workspace)
        self.facts, self.error = None, None
        if not repository.strip() or not workspace.strip():
            self.error = "Choose or enter both a repository root and an external workspace."
            return None
        self.token += 1
        self.loading = True
        self._active = ReadRequest(self.generation, self.token, repository, workspace)
        return self._active

    def complete(self, request: ReadRequest, facts: dict[str, Any] | None, error: str | None) -> bool:
        if request != self._active:
            return False
        self.loading, self._active = False, None
        if request.generation != self.generation:
            return False
        self.facts, self.error = facts, error
        if facts is not None:
            self.repository = facts["repository_path"]
            self.workspace = facts["workspace_path"]
        return True
