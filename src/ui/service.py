"""Slice 2 adapter: explicit inventory/index/planning, no patch or execution API."""

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
