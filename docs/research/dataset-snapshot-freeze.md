# Dataset Snapshot Freeze — Phase 5.4.1

**Status:** Snapshot identities frozen; preprocessing validation passed 9/9. This freeze does **not** clear the corpus for indexing or embeddings.

- **Freeze / validation date:** 2026-09-27
- **Snapshot ID:** `corpus-snapshot-v1`
- **Preprocessing implementation commit:** `2c3e5ec` (Phase 5.4 baseline; documentation-only changes follow this implementation)
- **Preprocessing version:** manifest schema `1.0`; file filter `phase4.5-python-v1`; pipeline report schema `1.0`; Python AST parser Phase 5.2; semantic chunker Phase 5.3; Python `3.14.7`.
- **External checkout root:** `C:\Apps\Temp\Phase5.4\corpus` (outside the thesis Git project)
- **Validation report:** `C:\Apps\Temp\Phase5.4\reports\corpus-checkout-validation\pipeline-validation.md` and `.json` (external; contains aggregate metadata only)

The repository SHA is the immutable snapshot identity. Branches and tags are not substitutes. The selected source remains upstream-owned and is not copied into this thesis repository.

## Frozen repository set

| Stratum | Repository | Pinned commit SHA | Root license evidence | Eligible Python files | Eligible Python LOC |
|---|---|---|---|---:|---:|
| Small | [theskumar/python-dotenv](https://github.com/theskumar/python-dotenv) | `a00cb2eed0704cd6d2071b2004c37e95ccc86ee5` | BSD-3-Clause; `LICENSE` | 20 | 2,776 |
| Small | [python-humanize/humanize](https://github.com/python-humanize/humanize) | `392aef707c0e74341ab4a51420984e9ea6b566c5` | MIT; `LICENCE` | 13 | 2,915 |
| Small | [python-validators/validators](https://github.com/python-validators/validators) | `70de324322def13a49a93d222f798ec1ab700885` | MIT; `LICENSE.txt` | 64 | 4,353 |
| Medium | [pallets/flask](https://github.com/pallets/flask) | `d73fa1cdcbd8b1465c151db8924ba58b1dd14e35` | BSD-3-Clause; `LICENSE.txt` | 83 | 13,301 |
| Medium | [encode/httpx](https://github.com/encode/httpx) | `b5addb64f0161ff6bfe94c124ef76f6a1fba5254` | BSD-3-Clause; `LICENSE.md` | 60 | 13,800 |
| Medium | [Textualize/rich](https://github.com/Textualize/rich) | `9d8f9a372cc5916fd4781fec207ced7ddac2f08f` | MIT; `LICENSE` | 213 | 45,223 |
| Large | [pytest-dev/pytest](https://github.com/pytest-dev/pytest) | `8721173580390a9d297e5af06cac3f0b6841f425` | MIT; `LICENSE` | 245 | 93,998 |
| Large | [python/mypy](https://github.com/python/mypy) | `0861bb6450d6d3658e44dbca9cd2ba478faf3c1d` | MIT for most code; PSF-2.0 notices apply to specified files; `LICENSE` | 444 | 144,316 |
| Large | [sphinx-doc/sphinx](https://github.com/sphinx-doc/sphinx) | `b04a2101295ac3fb725b16111eda0284b6da4cca` | BSD-2-Clause default; inspect per-file notices; `LICENSE.rst` | 774 | 118,987 |

License identifiers and file-level qualifications follow [repository-corpus-final.md](repository-corpus-final.md). Retain upstream notices and honor file-specific terms; this record is not legal advice.

## Freeze validation outcome

On the validation date, all nine external checkouts matched their frozen SHAs and the scanner reproduced the approved file and LOC baselines. The pipeline parsed all **1,916/1,916** eligible files with **zero parse failures**, generated **33,415** deterministic semantic chunks with **zero chunk-generation failures**, and reported preprocessing readiness **PASS**. The combined screening total is **439,669 eligible Python LOC**. Per-repository metrics and the exact methodology are in [corpus-checkout-validation.md](corpus-checkout-validation.md).

The external pipeline report contains aggregate metadata and omits source text, per-file paths, and checkout paths. Checkouts, raw validation outputs, and secret-scan reports remain outside this repository, consistent with [ADR-008](../decisions/ADR-008-source-code-privacy.md).

## Explicitly open clearance gates

- Gitleaks `8.30.1` was run against each checked-out snapshot and the locally available shallow Git history. Snapshot scanning reported eight candidate findings across Flask (six), pytest (one), and Sphinx (one). Findings have **not** been manually dispositioned; the Git-history scan for Sphinx also logged an unsupported `.dot` file error. Clones contain only the pinned shallow commit, not complete upstream history. Detailed, redacted reports remain external.
- A personal/confidential-data review has not been completed or claimed.
- Therefore corpus privacy clearance is **OPEN**. Do not start embeddings, FAISS, any vector database, or LLM processing until the findings and privacy review are documented and the next phase is explicitly authorized. Passing preprocessing validation is not privacy clearance.

## References

- [Final corpus selection](repository-corpus-final.md)
- [Phase 4.5 manifest validation](corpus-manifest-validation.md)
- [Phase 5.4.1 checkout validation report](corpus-checkout-validation.md)
- [ADR-006: corpus selection](../decisions/ADR-006-corpus-selection.md)
- [ADR-013: dataset snapshot freeze](../decisions/ADR-013-dataset-snapshot-freeze.md)
- [ADR-008: source-code privacy](../decisions/ADR-008-source-code-privacy.md)
