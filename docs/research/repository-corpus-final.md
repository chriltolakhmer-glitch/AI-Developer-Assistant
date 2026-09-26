# Repository Corpus — Phase 4 Screening Result

**Status:** Selected and commit-pinned for the planned primary corpus; source/license checks recorded on 2026-09-26. This is a screening result, not an assertion that the later secret/privacy audit or benchmark annotation has already been completed. No source implementation exists.

## Screening protocol

- **Snapshot:** Each repository was fetched from its public GitHub URL as a shallow checkout on 2026-09-26. The full 40-character `HEAD` SHA below is the immutable identity for the proposed evaluation snapshot; use that SHA, not a branch or tag, for every later checkout and citation.
- **Language:** GitHub repository-language metadata identifies Python for all nine. The Python file and LOC columns below were independently counted from the pinned checkout. Non-Python files are out of the primary index and benchmark.
- **Eligible Python LOC estimate:** Count tracked `*.py` files, excluding paths containing `.git`, `.venv`, `venv`, `__pycache__`, `site-packages`, `build`, `dist`, `vendor`, `vendors`, `third_party`, `generated`, `fixtures`, or `testdata`; also exclude generated `*_pb2.py` files. Count a physical line when its trimmed contents are non-empty and do not start with `#`. This intentionally includes ordinary project tests, since they are Python source; fixture directories are excluded. It is a reproducible screening estimate, not a parser-validated count. Apply this same rule to all repositories and record any later protocol change before annotation/evaluation.
- **Checkout size:** “Tracked MiB” is the sum of checked-out bytes for Git-tracked files at the pinned revision, divided by 1,048,576 and rounded to two decimals. It is not GitHub's compressed repository-size field and is not the size of only the Python sources.
- **Maturity evidence:** The tag-ref count comes from `git ls-remote --tags --refs` at screening time; CI denotes a checked-in GitHub Actions workflow; test evidence denotes a project test suite/file tree. These are screening signals, not a quality ranking or endorsement.
- **License:** The identifier is read from the checked-in root license text, rather than relying on GitHub's sometimes-unset SPDX metadata. Preserve notices and comply with the exact license in each pinned checkout. This is research-use screening, not legal advice.

## Selected primary evaluation corpus

| Stratum | Repository | Domain / purpose | Root license | Pinned commit | GitHub language | Python files | Eligible Python LOC | Tracked MiB | Maturity evidence (tag refs; CI; tests; pinned commit date) |
|---|---|---|---|---|---|---:|---:|---:|---|
| Small | [theskumar/python-dotenv](https://github.com/theskumar/python-dotenv) | Application configuration from `.env` files | BSD-3-Clause (`LICENSE`) | `a00cb2eed0704cd6d2071b2004c37e95ccc86ee5` | Python, Makefile | 20 | 2,776 | 0.14 | 52; yes; yes; 2026-08-17 |
| Small | [python-humanize/humanize](https://github.com/python-humanize/humanize) | Human-readable number, date, and file-size formatting | MIT (`LICENCE`) | `392aef707c0e74341ab4a51420984e9ea6b566c5` | Python, Shell | 13 | 2,915 | 0.40 | 58; yes; yes; 2026-09-16 |
| Small | [python-validators/validators](https://github.com/python-validators/validators) | Reusable value and format validators | MIT (`LICENSE.txt`) | `70de324322def13a49a93d222f798ec1ab700885` | Python, PowerShell, Shell | 64 | 4,353 | 0.37 | 69; yes; yes; 2026-03-14 |
| Medium | [pallets/flask](https://github.com/pallets/flask) | Python web framework | BSD-3-Clause (`LICENSE.txt`) | `d73fa1cdcbd8b1465c151db8924ba58b1dd14e35` | Python, HTML, Shell, CSS | 83 | 13,301 | 1.82 | 69; yes; yes; 2026-09-08 |
| Medium | [encode/httpx](https://github.com/encode/httpx) | Synchronous and asynchronous HTTP client | BSD-3-Clause (`LICENSE.md`) | `b5addb64f0161ff6bfe94c124ef76f6a1fba5254` | Python, Shell | 60 | 13,800 | 3.20 | 88; yes; yes; 2026-02-23 |
| Medium | [Textualize/rich](https://github.com/Textualize/rich) | Terminal formatting, rendering, and UI utilities | MIT (`LICENSE`) | `9d8f9a372cc5916fd4781fec207ced7ddac2f08f` | Python, Batchfile, Makefile | 213 | 45,223 | 18.90 | 178; yes; yes; 2026-06-23 |
| Large | [pytest-dev/pytest](https://github.com/pytest-dev/pytest) | Python testing framework | MIT (`LICENSE`) | `8721173580390a9d297e5af06cac3f0b6841f425` | Python, Gherkin | 245 | 93,998 | 7.23 | 224; yes; yes; 2026-09-24 |
| Large | [python/mypy](https://github.com/python/mypy) | Static type checker for Python | MIT for most code; specified files use PSF-2.0 (`LICENSE`) | `0861bb6450d6d3658e44dbca9cd2ba478faf3c1d` | Python, C, C++, XSLT, Go Template, Shell, CSS, Batchfile, Emacs Lisp, Makefile, Dockerfile | 444 | 144,316 | 20.16 | 116; yes; yes; 2026-09-25 |
| Large | [sphinx-doc/sphinx](https://github.com/sphinx-doc/sphinx) | Documentation generator | BSD-2-Clause default; inspect file-level notices (`LICENSE.rst`) | `b04a2101295ac3fb725b16111eda0284b6da4cca` | Python, JavaScript, TeX, Jinja, HTML, Common Lisp, Makefile, CSS, BitBake, Cython, C, Assembly, NASL, Pascal | 774 | 118,987 | 22.57 | 236; yes; yes; 2026-09-18 |

The nine measured counts sum to **439,669 eligible Python LOC** and **1,916 tracked Python files**. The strata satisfy the pre-existing thresholds: small 1,000–10,000; medium >10,000–50,000; large >50,000–150,000 LOC. The application domains, multiple license families, and differing project layouts reduce obvious single-framework selection bias. The three previously studied assistant repositories remain excluded from the primary sample.

## Inclusion status and remaining checks

The listed revisions pass the public-access, root-license-text, Python-language, LOC-stratum, size, and basic maturity screening. They are selected as the pinned corpus **subject to** these required pre-index steps:

1. Check out each exact SHA into a clean, read-only research snapshot and verify it matches the recorded SHA.
2. Run and record a secret/credential and personal/confidential-data audit before parsing or indexing; this screening did not establish that the repositories contain no such material. Exclude affected files or repositories and document any change before annotation.
3. Re-run the LOC/file manifest with the eventual scanner's exact shared filtering policy; retain eligible/excluded file lists, per-file hashes, parser success/failure, and any count delta. If a repository crosses a stratum boundary, revise this corpus decision before annotation rather than silently reclassifying it.
4. Preserve each root license and any applicable per-file notices in the research record. The mypy and Sphinx notices in particular require honoring their file-level licensing terms.

No hosted embedding or LLM service is authorized by this selection. The primary retrieval experiment is local and retrieval-only; any later data transfer requires a separate, explicit review.

## Sources and reproducibility record

Repository identity and metadata: the canonical GitHub links in the table; language metadata was read from each repository's GitHub language endpoint on 2026-09-26. License evidence: the named root license file at each pinned commit. Maturity evidence: tags, tracked files, tests, workflow files, and commit date in the fetched Git history. Counts and checkout sizes were computed locally using the protocol above. A future manifest should store the screening date, URL, SHA, license-file path, language metadata, LOC rule/version, eligible file list and hashes, exclusions, parser report, and audit outcome per repository.

For the original target, question mix, and held-out/annotation requirements, see [dataset-design.md](dataset-design.md) and [benchmark-design.md](benchmark-design.md). This file supersedes the Phase 3 placeholder shortlist in [repository-corpus-selection.md](repository-corpus-selection.md).