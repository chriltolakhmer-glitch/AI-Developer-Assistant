"""Offline preprocessing validation and retrieval evaluation."""

from importlib import import_module

__all__ = [
    "APPROVED_CORPUS",
    "PipelineValidationReport",
    "PipelineValidationRunner",
    "RepositorySpec",
    "Benchmark",
    "BenchmarkCase",
    "BenchmarkLoader",
    "BenchmarkFreezeMetadata",
    "BenchmarkFreezeUtility",
    "BenchmarkStatistics",
    "BenchmarkValidationReport",
    "BenchmarkValidator",
    "calculate_benchmark_statistics",
    "create_annotation_template",
    "EvaluationReport",
    "QueryEvaluation",
    "RetrievalEvaluator",
    "load_benchmark",
    "ndcg_at_k",
    "recall_at_k",
    "reciprocal_rank",
]


def __getattr__(name: str) -> object:
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name = (
        "src.evaluation.pipeline_validation"
        if name in {"APPROVED_CORPUS", "PipelineValidationReport", "PipelineValidationRunner", "RepositorySpec"}
        else "src.evaluation.benchmark"
        if name in {"Benchmark", "BenchmarkCase", "BenchmarkLoader", "load_benchmark"}
        else "src.evaluation.benchmark_validator"
        if name in {"BenchmarkValidationReport", "BenchmarkValidator"}
        else "src.evaluation.benchmark_freeze"
        if name in {"BenchmarkFreezeMetadata", "BenchmarkFreezeUtility"}
        else "src.evaluation.benchmark_statistics"
        if name in {"BenchmarkStatistics", "calculate_benchmark_statistics", "create_annotation_template"}
        else "src.evaluation.retrieval"
        if name in {"EvaluationReport", "QueryEvaluation", "RetrievalEvaluator"}
        else "src.evaluation.metrics"
    )
    module = import_module(module_name)
    exported = getattr(module, name)
    globals()[name] = exported
    return exported