# Software Prototype Scope

**Effective:** Phase 19.8 scope reduction, 2026-09-27.

**Project goal:** "Build and validate a working benchmark/retrieval research prototype."

The active project is a **functional research software prototype with a validated pilot dataset**. Its status changes from benchmark expansion preparation to **research software prototype validation**. This document supersedes the active-work interpretation of earlier benchmark workflows and planning documents; historical records remain intact.

## Current status and dataset

| Area | Status / scope |
|---|---|
| Humanize | **COMPLETE / FROZEN**; pilot-only |
| Software | **ACTIVE DEVELOPMENT**; maintain and validate existing functionality |
| Expansion | **DEFERRED** |
| Benchmark growth | **NOT STARTED**; no additional questions or annotation rounds |
| Optional optimization | **PAUSED**; further tuning, additional strategies, new experiments and scaling studies |

The current dataset is **Humanize pilot only**, `python-humanize/humanize` at `392aef707c0e74341ab4a51420984e9ea6b566c5`. Preserve its 12 validated questions, evidence mappings, answers, recorded retrieval evaluations, frozen artifacts and hashes. See the unchanged [pilot status](benchmark-annotation-pilot-status.md) and its linked external evidence. Existing pilot results remain bounded pilot evidence, not unseen multi-repository validation or production readiness.

The other eight registered repositories remain **NOT SELECTED FOR THESIS SCOPE**. Their old findings and approval records are archived, not active evidence-closure tasks. There is no requirement to onboard them, collect Gate 1 evidence or complete repository-clearance forms to maintain this software.

## Remaining active software components

| Capability | Existing implementation | Maintenance and validation scope |
|---|---|---|
| Repository processing / ingestion | [RepositoryScanner](../../src/scanner/repository_scanner.py), [PythonAstParser](../../src/parser/python_ast_parser.py) | Maintain read-only snapshot/file provenance, Python parsing and explicit errors. No new repository onboarding. |
| Chunk generation | [CodeChunker](../../src/chunker/code_chunker.py) | Preserve deterministic chunk IDs, source locations and existing chunk contracts. |
| Embedding and indexing | [EmbeddingPipeline](../../src/embedding/pipeline.py), [BM25Index](../../src/retrieval/bm25_index.py), [VectorIndex](../../src/retrieval/vector_index.py) | Maintain existing local model, index persistence, loading and integrity checks. |
| Retrieval | [Retrieval APIs](../../src/retrieval/__init__.py) | Maintain existing BM25, vector, hybrid/fusion and bounded parent-child behavior. Keeping existing modes does not start work on additional strategies or tune them. |
| Evaluation | [RetrievalEvaluator](../../src/evaluation/retrieval.py), [metrics](../../src/evaluation/metrics.py) | Preserve metric definitions, fixed inputs and reproducible result/error reporting. Keep existing pilot results unchanged. |
| Validation utilities | [PipelineValidationRunner](../../src/evaluation/pipeline_validation.py), [BenchmarkValidator](../../src/evaluation/benchmark_validator.py), [freeze utility](../../src/evaluation/benchmark_freeze.py) | Maintain provenance, artifact integrity, schema and repeatability checks. Retaining a freeze utility is not creating a new release. |
| Automated tests | [tests](../../tests) | Run existing unit/integration tests and fix demonstrated stability regressions. Use synthetic fixtures/offline cached models where already supported. |

These are existing Python APIs and validation utilities, not a claim that every historical blueprint requirement or user interface is implemented. Preserve the current schemas and persisted-artifact contracts. No implementation or retrieval behavior changes are made by this scope update.

## Prototype validation work

Active work is limited to maintaining the above components, reproducing existing behavior, diagnosing failures, correcting necessary stability defects, and documenting actual setup and limitations. A stability change should identify the failing behavior, retain compatible contracts where possible and pass relevant tests. Do not disguise optimization or a new strategy as a stability fix.

Validation uses fixed existing contracts and data; store any temporary test/reproduction output separately. Do not overwrite the Humanize dataset, annotations, results or frozen artifacts. Reproduction checks compare existing behavior and artifacts; they do not introduce new benchmark cases, model comparisons, parameter searches or scaling experiments. This phase runs the application suite, not a new pilot retrieval experiment or source-processing pipeline.

Keep local source/data handling and applicable license conditions. Archived evidence remains available for truthful limitations reporting; this scope change is neither a new source transfer permission nor a retrospective resolution of historical safety findings. Administrative approval chains and multiple-reviewer assignments are not software-maintenance prerequisites.

## Removed active tasks and archive

- Additional repository selection/onboarding, candidate approval, Gate 1 evidence collection and repository clearance: **archived as future expansion work**.
- G0 authorization, gate dashboards, release gates, governance reviews, approval matrices, mandatory multiple reviewers/signatures: **historical/superseded**, not active tasks.
- Additional questions, annotation rounds and full benchmark expansion: **not started and outside active scope**.
- Further retrieval tuning, additional strategies, new experiments and scaling studies: **paused**. Preserve existing implementation, tests and results.

The [earlier governance migration](thesis-benchmark-governance-migration.md) retains the complete inventory of 47 superseded governance/candidate documents. Those documents remain archived; no historical content is deleted. The [lightweight benchmark workflow](thesis-benchmark-workflow.md) is now a future-expansion reference, rather than an active four-phase execution plan. The [evidence tracker](repository-evidence-progress.md) is an archive, not a queue to clear.

The [requirements blueprint](../requirements/system-requirements.md), [experiment design](experiment-design.md) and [evaluation plan](evaluation-plan.md) retain earlier ideas and technical rationale with current scope notices. Their unimplemented features, planned comparisons and scaling studies are not current deliverables. Technical schemas, validation reports, architecture/API documentation and all dedicated Humanize records remain references for maintaining existing functionality.

## Deferred features and future extension points

**Deferred:** multi-repository benchmark, large-scale annotation and production benchmark release. UI/LLM-answer services and other unimplemented blueprint features are not added to the prototype-validation backlog.

"Additional repositories and benchmark growth may be added after prototype validation."

If later brought into scope, extend the existing scanner/parser/chunker interfaces, versioned index/retrieval APIs and benchmark/evaluation schemas while preserving snapshot provenance and prior frozen versions. These are extension points, not scheduled work. Reopening expansion, annotation or optimization requires a separate scope decision; this document starts none of them.

## Validation command and result

Use the existing external environment and offline model cache from the project workspace:

```powershell
$env:EMBEDDING_MODEL_CACHE = 'C:/Apps/Temp/Phase6.2/model-cache'
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
& C:/Apps/Temp/Phase6.2/venv/Scripts/python.exe -m unittest discover -s tests -v
```

These are this workspace's existing paths; another machine needs equivalent installed dependencies and the pinned offline model cache. Do not claim a skip-free offline integration result without that cache.

**Result, 2026-09-27:** `Ran 124 tests in 10.188s` / `OK`; exit 0, no failures, errors or skips. Log: `C:/Apps/Temp/Phase19.8-prototype/tests.log`; SHA-256 `4e84bcb893473b49260bc9a5ad8c3aef6760964266a7e4c5dc53aeee014b128a`.

Validation evidence is stored outside the project at `C:/Apps/Temp/Phase19.8-prototype/`. Before/after workspace hashes and hashes of all 35 external Phase 8 files (including 34 Humanize pilot files) establish preservation. The scope change creates no questions/annotations and changes no source, retrieval, benchmark or test code. No repository source is processed and no benchmark expansion runs. Pre-existing code edits are preserved. The suite result validates the current working software; it does not assert production readiness or create new research results.
