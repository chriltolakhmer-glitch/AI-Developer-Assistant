# Phase 9 — Final Research Corpus Selection

**Status:** Repository membership and pinned snapshot identities frozen for the primary research corpus on 2026-09-27. This is a corpus-definition freeze, **not** privacy clearance to annotate, index, embed, or evaluate source.

**Project baseline:** `6fee0fbdf5e1e9c6abc1cc355f38c55eb4b25677`
**Snapshot set:** `corpus-snapshot-v1`
**Language scope:** Python source files only. Other languages listed in GitHub metadata are not part of the primary preprocessing/evaluation scope.

## Frozen corpus

Size categories use the previously declared eligible-Python-LOC thresholds: Small 1,000–10,000; Medium >10,000–50,000; Large >50,000–150,000. File and LOC counts are the Phase 5.4.1 validated screening baseline; ordinary Python tests are included under the shared `phase4.5-python-v1` filter. “Language” records the GitHub language metadata, while only Python is eligible for this study.

| Category | Repository name | URL | Pinned commit SHA | Root license evidence | GitHub languages | Eligible Python files / LOC | Selection justification |
|---|---|---|---|---|---|---:|---|
| Small | `python-dotenv` | https://github.com/theskumar/python-dotenv | `a00cb2eed0704cd6d2071b2004c37e95ccc86ee5` | BSD-3-Clause (`LICENSE`) | Python, Makefile | 20 / 2,776 | Small configuration-management library; supplies the small stratum and a focused package layout. |
| Small | `humanize` | https://github.com/python-humanize/humanize | `392aef707c0e74341ab4a51420984e9ea6b566c5` | MIT (`LICENCE`) | Python, Shell | 13 / 2,915 | Small formatting library with number, date, and file-size functionality; adds a distinct utility-library domain. |
| Small | `validators` | https://github.com/python-validators/validators | `70de324322def13a49a93d222f798ec1ab700885` | MIT (`LICENSE.txt`) | Python, PowerShell, Shell | 64 / 4,353 | Small validation library with multiple modules; provides cross-file structure within the small stratum. |
| Medium | `flask` | https://github.com/pallets/flask | `d73fa1cdcbd8b1465c151db8924ba58b1dd14e35` | BSD-3-Clause (`LICENSE.txt`) | Python, HTML, Shell, CSS | 83 / 13,301 | Medium-sized web framework; adds a framework domain and a different package structure. |
| Medium | `httpx` | https://github.com/encode/httpx | `b5addb64f0161ff6bfe94c124ef76f6a1fba5254` | BSD-3-Clause (`LICENSE.md`) | Python, Shell | 60 / 13,800 | Medium-sized synchronous/asynchronous HTTP client; contributes a network-client domain distinct from web frameworks. |
| Medium | `rich` | https://github.com/Textualize/rich | `9d8f9a372cc5916fd4781fec207ced7ddac2f08f` | MIT (`LICENSE`) | Python, Batchfile, Makefile | 213 / 45,223 | Medium-sized terminal rendering and UI utilities; spans a broad but still predeclared medium-size codebase. |
| Large | `pytest` | https://github.com/pytest-dev/pytest | `8721173580390a9d297e5af06cac3f0b6841f425` | MIT (`LICENSE`) | Python, Gherkin | 245 / 93,998 | Large testing framework; represents test tooling and supplies a large-stratum sample. |
| Large | `mypy` | https://github.com/python/mypy | `0861bb6450d6d3658e44dbca9cd2ba478faf3c1d` | MIT for most code; PSF-2.0 applies to specified files (`LICENSE`) | Python, C, C++, XSLT, Go Template, Shell, CSS, Batchfile, Emacs Lisp, Makefile, Dockerfile | 444 / 144,316 | Large static type checker; adds static-analysis functionality. Python is the only indexed language, and applicable file-level notices must be retained and honored. |
| Large | `sphinx` | https://github.com/sphinx-doc/sphinx | `b04a2101295ac3fb725b16111eda0284b6da4cca` | BSD-2-Clause default; inspect file-level notices (`LICENSE.rst`) | Python, JavaScript, TeX, Jinja, HTML, Common Lisp, Makefile, CSS, BitBake, Cython, C, Assembly, NASL, Pascal | 774 / 118,987 | Large documentation generator; adds a documentation-tooling domain and a different repository structure. Python-only filtering limits the study scope; inspect applicable file-level notices. |

**Aggregate baseline:** 9 repositories; 1,916 eligible Python files; 439,669 eligible Python LOC. The pinned snapshots and these counts were validated in the Phase 5.4.1 preprocessing run. This freezes the intended corpus; any replacement, SHA change, or filter/count change requires a documented decision and reconciliation before annotation.

## Selection rationale and exclusions

The corpus preserves the predeclared three-size-stratum design (three repositories per stratum) while covering configuration, formatting, validation, web frameworks, HTTP clients, terminal UI, testing, static analysis, and documentation tooling. This reduces obvious single-domain/framework dependence while keeping the primary analysis Python-only and feasible for a single researcher. The three previously studied assistant repositories—`codebase-rag`, `Codebase-RAG-Assistant`, and `ai-codebase-assistant`—are excluded from primary evaluation to avoid selection bias toward systems already analyzed during thesis planning.

Root-license identifiers above are screening evidence, not legal advice or blanket clearance. Preserve license texts and applicable file-level notices; in particular, check the named qualifications for `mypy` and `sphinx`.

## Privacy and use gate

The Phase 8 thesis-level privacy decision is **APPROVED WITH CONTROLS**. It approves the handling rules; it does not clear each snapshot or override unresolved snapshot-specific review gates. The Phase 5.4.1 record reports eight unresolved Gitleaks snapshot candidates across Flask (six), pytest (one), and Sphinx (one), a Sphinx history-scan `.dot` error, shallow single-commit checkouts, and no completed personal/confidential-data review. The specific humanize pilot review also remains **NOT APPROVED — PILOT ANNOTATION REMAINS BLOCKED** because its history scope, personal/confidential-data review, file-notice review, handling evidence, and attributable approval are unresolved.

Therefore this document freezes only repository membership, revisions, and the stated screening baseline. Do not create benchmark questions or use source/chunk inventories for annotation, indexing, embeddings, retrieval, or evaluation until the applicable repository-specific gates have been completed and explicitly approved. A clean preprocessing result or an approved general policy is not a substitute for that clearance.

## Reproducibility references

- [Repository corpus screening and metadata](repository-corpus-final.md)
- [Dataset snapshot freeze](dataset-snapshot-freeze.md)
- [Phase 5.4.1 checkout validation](corpus-checkout-validation.md)
- [Phase 8 thesis privacy review](privacy-review.md)
- [Phase 8.8 pilot privacy review](pilot-privacy-final-review.md)
- [ADR-006: corpus selection](../decisions/ADR-006-corpus-selection.md)
- [ADR-008: source-code privacy](../decisions/ADR-008-source-code-privacy.md)
- [ADR-013: dataset snapshot freeze](../decisions/ADR-013-dataset-snapshot-freeze.md)
