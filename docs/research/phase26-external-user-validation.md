# Phase 26 — External User Validation

**Date:** 2026-09-28
**Status:** **SUPERSEDED by the verified v0.1.1 public release.**
**Scope:** Installation, README walkthrough, demo usability, run reproduction, and documentation feedback only.

No datasets, repositories, benchmark questions, annotations, retrieval behavior, or evaluation methodology were added or changed. Validation run records and the temporary checkout were kept outside this repository.

## Executive result

The documented package workflow succeeds in a clean Python 3.14.7 virtual environment when run from an isolated shallow checkout of the local `v0.1.0` Git tag. The pinned lock, package install, `pip check`, CLI help, demo, JSON evaluation smoke check, missing-corpus validation, and demo reproduction all behaved as documented. The full suite ran 142 tests; two model-backed integration tests skipped because no offline model cache was supplied.

This was **not** a passing fresh-machine/public-tag test. At the time of Phase 26, the public GitHub remote did not advertise `refs/tags/v0.1.0`; a direct clone by that tag failed with `Remote branch v0.1.0 not found in upstream origin`. A shallow clone from the local Git object store was used only to test the release snapshot independently of the working-tree files. The repository was subsequently made public with the owner's approval, and Phase 26.1 published a corrected v0.1.1 tag. Its anonymous clone/install/reproduction results are in the [Phase 26.1 release verification report](phase26.1-release-verification.md) and the [public GitHub release](https://github.com/chriltolakhmer-glitch/AI-Developer-Assistant/releases/tag/v0.1.1).

The local tag also contains a release-manifest provenance mismatch: tag `v0.1.0` resolves to commit `89e697a34d2a3aa8e6f0939f2d0b9b6401b859ba`, while the manifest inside that tag records `9a103131690ee42bb621de37aa655a429dde7376`. The current local `main` checkout has a later manifest correction, but that later file is not part of the tagged snapshot. Do not rewrite a published tag; decide on a corrected, immutable release version and publish it before claiming that a new user can clone v0.1.0.

## Test record

| Check | Result |
|---|---|
| Public remote tag lookup / clone | **BLOCKED** — v0.1.0 was not advertised remotely; remote clone failed. |
| Isolated local-tag shallow checkout | **PASS** — detached at `89e697a34d2a3aa8e6f0939f2d0b9b6401b859ba`; this is a simulation, not a remote clone. |
| New virtual environment | **PASS** — Python 3.14.7 on Windows. |
| `pip install -r requirements-lock.txt` | **PASS** — exact pinned dependencies installed. The machine's package-wheel cache may have supplied downloads, so this was not a network-clean host test. |
| `pip install .` and `pip check` | **PASS** — package installed; no broken requirements. |
| `prototype --help` | **PASS** |
| `prototype demo` | **PASS** — 3 chunks from generated `demo.py`, 2 synthetic queries, MRR 1.000, nDCG 1.000. |
| `prototype evaluate --json` | **PASS** — JSON smoke report for two generated queries. |
| `prototype validate` without corpus | **EXPECTED NOT-READY** — 0/9 snapshots, preprocessing readiness `no`; command exited successfully and did not fetch anything. |
| `prototype reproduce <demo-run-id>` | **PASS** — saved standardized demo payload matched. |
| README PowerShell run-ID lookup and reproduction sequence | **PASS** — selected a demo run from `metadata.json` and replayed it successfully. |
| `python -m unittest discover -s tests -v` | **PASS WITH SKIPS** — 142 tests run, 2 skipped because `EMBEDDING_MODEL_CACHE` was not set. |

The demo's perfect metrics are properties of fixed synthetic fixtures/rankings; they are not Humanize, corpus, or retrieval-quality results. Complete model-backed test coverage requires the separately acquired pinned offline cache described in the project documentation.

## New-user feedback and documentation changes

| Feedback | Disposition |
|---|---|
| README began at “project root” and assumed a checkout; it did not show how to obtain the exact release tag or what to do if the tag was unavailable. | Added tag-only clone and manifest verification steps to README and the release guide. Missing remote tag is explicitly a stop condition, not an invitation to use `main`. |
| `prototype reproduce RUN_ID` did not explain how to identify a run. An existing CLI-guide example selected the first directory, which could be a different command. | README and CLI guide now select the newest run whose metadata says `command: demo`. |
| Demo output was terse; chunk and metric counts could be mistaken for real retrieval results. | README and CLI guide now describe the generated fixture, 3 chunks, 2 synthetic queries, printed MRR/nDCG, and the fact that perfect scores are not research results. |
| A missing corpus makes `prototype validate` return successfully while reporting no readiness. | README now explicitly describes `0/9` and `Preprocessing ready: no` as expected without local corpus inputs, not a validation pass. |
| Full pinned installation and model-dependent testing have different prerequisites. | README now distinguishes the complete lock from the smaller CLI smoke install; the offline model-cache requirement remains explicit in the release guide. |
| PowerShell can block venv activation on a default Windows policy. | README and release guide now document a process-scoped `RemoteSigned` workaround; it does not change the machine-wide policy. |

The direct user journey is documented in [README](../../README.md), with additional command details in the [release guide](release-guide.md) and [prototype CLI guide](prototype-cli.md).

## Required follow-up before declaring success

The v0.1.0 issue is closed for new users by publishing the immutable v0.1.1 tag; the old tag remains unchanged. See the Phase 26.1 report for the new release evidence. Model-backed tests still require the pinned offline cache; do not download model data as an implicit part of the walkthrough.

**Phase 26 disposition:** Documentation friction was corrected. Phase 26.1 supersedes the outstanding release-publication follow-ups for new users.