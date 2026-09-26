# Corpus Manifest Validation — Phase 4.5

**Validation date:** 2026-09-26  
**Source manifest:** [repository-corpus-final.md](repository-corpus-final.md)  
**Status:** Pin, root-license-file, Python-file-count, LOC-rule, and size-stratum checks passed. Secret/privacy screening and final scanner-manifest verification are still required before indexing.

## Validation method and result

For each entry in the selected manifest, the recorded full SHA was fetched from the repository's Git remote into an isolated temporary checkout and matched to `FETCH_HEAD`. The same tracked-file Python filter and line-count rule documented in the source manifest was reapplied to that exact commit. The cited root license file was verified in the commit tree. Test-source paths and checked-in GitHub Actions workflow files were also checked as basic maturity evidence.

The LOC rule counts tracked `.py` files; excludes `.git`, `.venv`, `venv`, `__pycache__`, `site-packages`, `build`, `dist`, `vendor`, `vendors`, `third_party`, `generated`, `fixtures`, and `testdata` paths and generated `*_pb2.py`; and counts each non-empty physical line whose trimmed contents do not start with `#`. It includes ordinary test code and is a screening LOC estimate, not parser output. Source paths and file content are not copied into this thesis repository.

**Result:** all nine exact commit fetches matched; Python-file counts and LOC matched the Phase 4 table; all cited root license files were present; all nine repositories had test source and GitHub Actions workflows. Combined total: **1,916 eligible Python files** and **439,669 eligible Python LOC**.

## Validated corpus

| Size category | Repository | Commit SHA | Root license evidence | Python scope | Revalidated LOC | Validation notes |
|---|---|---|---|---|---:|---|
| Small | [theskumar/python-dotenv](https://github.com/theskumar/python-dotenv) | `a00cb2eed0704cd6d2071b2004c37e95ccc86ee5` | BSD-3-Clause; `LICENSE` present | Tracked `.py` files only; 20 eligible files | 2,776 | Exact SHA fetch matched; file/LOC count matched; tests and CI workflow present. |
| Small | [python-humanize/humanize](https://github.com/python-humanize/humanize) | `392aef707c0e74341ab4a51420984e9ea6b566c5` | MIT; `LICENCE` present | Tracked `.py` files only; 13 eligible files | 2,915 | Exact SHA fetch matched; file/LOC count matched; tests and CI workflow present. |
| Small | [python-validators/validators](https://github.com/python-validators/validators) | `70de324322def13a49a93d222f798ec1ab700885` | MIT; `LICENSE.txt` present | Tracked `.py` files only; 64 eligible files | 4,353 | Exact SHA fetch matched; file/LOC count matched; tests and CI workflow present. |
| Medium | [pallets/flask](https://github.com/pallets/flask) | `d73fa1cdcbd8b1465c151db8924ba58b1dd14e35` | BSD-3-Clause; `LICENSE.txt` present | Tracked `.py` files only; 83 eligible files | 13,301 | Exact SHA fetch matched; file/LOC count matched; tests and CI workflow present. |
| Medium | [encode/httpx](https://github.com/encode/httpx) | `b5addb64f0161ff6bfe94c124ef76f6a1fba5254` | BSD-3-Clause; `LICENSE.md` present | Tracked `.py` files only; 60 eligible files | 13,800 | Exact SHA fetch matched; file/LOC count matched; tests and CI workflow present. |
| Medium | [Textualize/rich](https://github.com/Textualize/rich) | `9d8f9a372cc5916fd4781fec207ced7ddac2f08f` | MIT; `LICENSE` present | Tracked `.py` files only; 213 eligible files | 45,223 | Exact SHA fetch matched; file/LOC count matched; tests and CI workflow present. |
| Large | [pytest-dev/pytest](https://github.com/pytest-dev/pytest) | `8721173580390a9d297e5af06cac3f0b6841f425` | MIT; `LICENSE` present | Tracked `.py` files only; 245 eligible files | 93,998 | Exact SHA fetch matched; file/LOC count matched; tests and CI workflow present. |
| Large | [python/mypy](https://github.com/python/mypy) | `0861bb6450d6d3658e44dbca9cd2ba478faf3c1d` | MIT for most code; named C runtime files use PSF-2.0; `LICENSE` present | Tracked `.py` files only; 444 eligible files | 144,316 | Exact SHA fetch matched; file/LOC count matched; tests and CI workflow present. Respect per-file notices; non-Python code is excluded from the study. |
| Large | [sphinx-doc/sphinx](https://github.com/sphinx-doc/sphinx) | `b04a2101295ac3fb725b16111eda0284b6da4cca` | BSD-2-Clause default; check individual file notices; `LICENSE.rst` present | Tracked `.py` files only; 774 eligible files | 118,987 | Exact SHA fetch matched; file/LOC count matched; tests and CI workflow present. Respect per-file notices; non-Python code is excluded from the study. |

## Scope and eligibility observations

- All nine pinned snapshots contain substantive Python code and fall within the predeclared strata: small 1,000–10,000 LOC; medium >10,000–50,000 LOC; large >50,000–150,000 LOC.
- GitHub language metadata recorded in the source manifest includes additional languages for some projects. Those files are not part of the primary corpus; only the Python subset is indexed or evaluated.
- MIT/BSD root notices do not remove the obligation to retain notices or inspect applicable file-level notices. This is a research selection record, not legal advice.
- The established source-snapshot and count checks do **not** establish that a repository contains no credentials, personal data, or confidential material.

## Outstanding pre-index validation gates

1. Run a maintained secret scanner over each exact snapshot, including history if available, and manually review findings. Record scanner name/version, configuration, date, false-positive adjudications, excluded paths, and outcome. No secret-scan pass is claimed by this document.
2. Review likely personal/confidential-data locations and scanner findings. Exclude affected files or replace a repository before annotation if necessary; document the decision and recalculate its stratum.
3. Run the eventual implementation's scanner against each exact SHA using the same filters. Save a machine-readable file manifest, per-file hashes, exclusions/reasons, parser version/results, parse success/failure counts, and a LOC comparison. Reconcile any difference before annotation; do not silently adjust strata.
4. Keep checked-out source, index data, embeddings, and audit outputs outside Git and apply [ADR-008](../decisions/ADR-008-source-code-privacy.md).

Until these gates are complete, the corpus is **revision- and count-validated but not cleared for indexing**.