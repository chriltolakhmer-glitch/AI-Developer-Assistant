# Phase 12.5 — Thesis Scope Risk Acceptance

**Decision state:** **APPROVED WITH THESIS SCOPE LIMITATIONS**

**Decision date:** 2026-09-27

**Decision owner:** Thesis researcher / project owner

**Scope:** Local thesis experimentation only, using the frozen public open-source corpus and the controls below.

This is a thesis-level residual-risk acceptance. It is not repository-specific privacy clearance, a security audit, perfect privacy clearance, legal advice, or production approval. The nine repository approval records remain individually `BLOCKED` unless their own evidence and attributable decisions are completed.

## Accepted thesis scope

The researcher accepts the documented residual risk of proceeding with narrowly scoped thesis experimentation under these conditions:

1. **Local-only processing.** Source, manifests, excluded-file decisions, chunks, embeddings, indexes, experiment inputs, outputs, and detailed audit evidence remain on the controlled local machine. Do not send source or source-derived data to hosted AI/LLM, embedding, labeling, notebook, search/vector, telemetry, or cloud services. Network access is limited to controlled acquisition of declared public dependencies, model weights, or repository snapshots; experiment execution is offline.
2. **Public open-source corpus only.** Use only the nine repositories and exact full commit SHAs in `corpus-snapshot-v1`. Use Python files within the declared `phase4.5-python-v1` scope. Do not substitute branches, tags, mutable revisions, private repositories, or unapproved files.
3. **Sensitive-file exclusion.** Exclude files or artifacts when secret, personal, confidential, unnecessary, or otherwise unsafe content is identified or cannot be assessed. Do not copy sensitive findings, source excerpts, credentials, detailed paths, or raw audit reports into Git. Stop processing when an unresolved finding, scope mismatch, or handling-control failure is discovered.
4. **Thesis-only purpose.** Use results only for the Master's thesis research protocol, local reproducibility checks, and declared non-production experimentation. Do not redistribute source or derived artifacts, publish repository contents, expose experiment data as a service, or represent results as operational product validation.
5. **Separate annotation gate.** This decision does not authorize benchmark question creation, source-derived annotation, chunk-inventory use for gold labels, or benchmark freeze. Those activities remain disabled until the applicable repository-specific approval and annotation handoff criteria are separately satisfied.
6. **Controlled reporting.** Commit only non-sensitive protocol text and aggregate results. Keep source-derived working records and detailed evidence outside the thesis repository with access, retention, backup, and deletion controls documented locally.

## Known limitations retained

This acceptance does not resolve or erase the following limitations:

- The corpus-wide secret/credential baseline contains eight unresolved candidate findings: six Flask, one pytest, and one Sphinx.
- Recorded checkouts are shallow; history coverage is incomplete, and the Sphinx history scan has an unsupported `.dot` error.
- No complete repository-specific personal/confidential-data review is recorded for the corpus.
- File-level license/notice review is incomplete, particularly for mypy's MIT/PSF-2.0 qualifications and Sphinx notices.
- Exact-SHA manifest evidence is partial for most repositories; humanize has artifact identity/count evidence, but this is not privacy clearance.
- Local handling evidence is incomplete, including access, telemetry/offline, backup, retention, and deletion controls.
- Humanize has an unresolved historical data-handling conflict and remains not approved for pilot annotation.
- Public availability, a root license, preprocessing success, an empty saved scan result, a passing test suite, or this decision does not prove absence of sensitive content or authorize production use.

These limitations must remain visible in experiment manifests, reports, and thesis methodology. A changed snapshot, scope, finding, control, or purpose suspends this acceptance until reviewed.

## Researcher acceptance of residual risk

The thesis researcher accepts the residual risks above only for the limited, local, thesis-only experimentation scope. The researcher will:

- keep the frozen snapshot identities and Python-only scope unchanged;
- stop and record a blocker when a control or evidence assumption fails;
- preserve applicable license notices and exclusion decisions;
- keep detailed source-derived artifacts outside Git and prevent external data egress;
- report limitations and exclusions rather than presenting incomplete evidence as clearance; and
- request a new documented decision before changing purpose, scope, repository membership, external services, publication, or production use.

This acceptance is attributable as a committed thesis protocol decision by the thesis researcher. It is not a fabricated signature, independent review, repository-owner authorization, or legal attestation.

## Authorization boundary

| Activity | Status under this decision |
|---|---|
| Local thesis experimentation within the controls above | **AUTHORIZED WITH THESIS SCOPE LIMITATIONS** |
| Synthetic-fixture tests and implementation validation | **AUTHORIZED** |
| Benchmark question creation or source-derived annotation | **NOT AUTHORIZED** |
| Use of the benchmark as ground truth or benchmark freeze | **NOT AUTHORIZED** |
| External source/data upload or hosted processing | **NOT AUTHORIZED** |
| Public redistribution or publication of source/derived artifacts | **NOT AUTHORIZED** |
| Production deployment or production approval claim | **NOT AUTHORIZED** |

## Review and suspension

Before each experiment, verify the exact SHA, local-only execution, eligible-file scope, sensitive-file exclusions, storage controls, and current blocker list. Suspend this acceptance if any unresolved finding enters the experiment scope, a repository changes, local controls cannot be verified, or the experiment expands beyond thesis-only use. Reconcile the decision with the current [repository approval status report](repository-approval-status-report.md) and [evidence closure workflow](repository-approval-evidence-closure.md).

**Phase 13 annotation:** **DISABLED — this decision does not unlock annotation.**

See [repository-approval-workflow.md](repository-approval-workflow.md), [privacy-clearance-report.md](privacy-clearance-report.md), [privacy-review.md](privacy-review.md), [ADR-008](../decisions/ADR-008-source-code-privacy.md), [ADR-013](../decisions/ADR-013-dataset-snapshot-freeze.md), and [ADR-014](../decisions/ADR-014-embedding-privacy-policy.md).
