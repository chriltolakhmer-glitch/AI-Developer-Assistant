"""Offline pipeline validation for the pinned research corpus."""

from importlib import import_module

__all__ = [
    "APPROVED_CORPUS",
    "PipelineValidationReport",
    "PipelineValidationRunner",
    "RepositorySpec",
]


def __getattr__(name: str) -> object:
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module("src.evaluation.pipeline_validation")
    exported = getattr(module, name)
    globals()[name] = exported
    return exported