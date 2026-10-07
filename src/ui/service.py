"""Slice 1 adapter: a single read operation, no lifecycle API."""

from pathlib import Path
from typing import Any

from src.config import PrototypeConfig


class RepositoryService:
    def __init__(self, config: PrototypeConfig):
        self.config = config

    def read_repository(self, repository: str, workspace: str) -> dict[str, Any]:
        # Keep the retrieval environment off the startup/UI thread.
        from src.developer.local_workflow import DeveloperWorkspace
        from src.developer.ui_read import read_repository

        developer = DeveloperWorkspace(Path(workspace), research_roots=(
            self.config.data_root, self.config.corpus_root,
            self.config.validation_output, self.config.embedding_model_cache,
        ))
        return read_repository(developer, Path(repository))
