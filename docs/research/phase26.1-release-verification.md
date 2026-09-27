# Phase 26.1 — Release Verification: v0.1.1

**Date:** 2026-09-28
**Release:** `v0.1.1`
**Status:** **PASS — public tag clone, clean installation, CLI workflow, and test suite verified.**

This patch release repairs the v0.1.0 provenance mismatch without rewriting the earlier tag. The repository is public so a new researcher can clone the release without credentials. The code change is limited to software version metadata in run records; retrieval, evaluation, datasets, and Humanize artifacts were not changed.

## Provenance

| Item | Verified value |
|---|---|
| Public repository | `https://github.com/chriltolakhmer-glitch/AI-Developer-Assistant` |
| Published tag | `v0.1.1` |
| Tag target commit | `51329285a882c1b7942d0a5b1c571e628d63dfb4` |
| Public `git ls-remote` tag object | `05688504f74ad51230ee1566fad8cda0f1b1ad97` (annotated tag object) |
| Tag-resolved commit / clean clone HEAD | `51329285a882c1b7942d0a5b1c571e628d63dfb4` |
| GitHub Release | [AI Developer Assistant 0.1.1](https://github.com/chriltolakhmer-glitch/AI-Developer-Assistant/releases/tag/v0.1.1) |
| Post-tag `release-manifest.json` asset | SHA-256 `0bd633bfa6e7834c033e738a74a047f5fa3077541bc81dec5f8a5deffacb6a4a`; `git_sha` equals the tag target |
| v0.1.0 disposition | Preserved; not moved or rewritten. Its embedded manifest mismatch is historical and corrected for new users by v0.1.1. |

A commit cannot include its own commit ID in its tracked tree: changing the manifest changes the commit ID. The tracked manifest therefore records the pre-tag `source_git_sha`; after creating the immutable tag, the release workflow generated a `release-manifest.json` asset with `git_sha` equal to the tag-resolved commit. This removes the self-reference while allowing an independent user to verify the exact release bytes against `git rev-parse v0.1.1^{commit}`.

## Anonymous fresh-clone validation

The verification checkout was created from the public remote in a new external directory with Git credential helpers disabled and terminal prompts suppressed. No local developer worktree, `.venv`, project assumptions, corpus, or repository checkout was used as the clone source.

| Check | Result |
|---|---|
| Public `git ls-remote --tags` | **PASS** — `v0.1.1` advertised. |
| Anonymous depth-1 clone of `v0.1.1` | **PASS** — detached at `51329285a882c1b7942d0a5b1c571e628d63dfb4`. |
| Clean clone worktree before/after verification | **PASS** |
| Download and parse post-tag release manifest asset | **PASS** — asset `git_sha` matches clone HEAD. |
| Python runtime | **PASS** — Python 3.14.7, Windows. |
| New `.venv`, lock install with pip wheel cache disabled | **PASS** |
| `pip install .` and `pip check` | **PASS** — package version `0.1.1`; no broken requirements. |
| `prototype --help` | **PASS** |
| `prototype demo` | **PASS** — three generated-fixture chunks, two synthetic queries, MRR 1.000 and nDCG 1.000. These fixed-fixture metrics are not research results. |
| `prototype evaluate --json` | **PASS** — generated-fixture JSON smoke report. |
| `prototype validate` with no corpus | **EXPECTED NOT-READY** — 0/9 snapshots; preprocessing readiness `no`; no network acquisition. |
| Run-ID lookup and `prototype reproduce` | **PASS** — the demo run was identified from `metadata.json` and its standardized payload matched. |
| Full unittest suite | **PASS** — 142 tests, 0 failures, 0 errors, 0 skips; 23.164 seconds on the release checkout. |

The lock wheels were fetched without the local pip cache. The pinned offline model cache used for the suite was already present outside the repository; model data was not downloaded during validation.

## Scope and preservation checks

- The patch only synchronizes the package, `VERSION`, and run-tracking software version to `0.1.1`, updates the associated version assertion, corrects release-manifest provenance handling, and clarifies release onboarding/reporting.
- No source, Humanize pilot artifacts, benchmark questions or annotations, repositories, datasets, retrieval algorithms, or evaluation behavior changed.
- `git diff --check` passed before the release commit. The public validation clone remained clean after the tests.
- The complete test log and temporary fresh clone/run records were retained outside the repository at `C:\Apps\Temp\Phase26.1-public-validation-20260928`.

## Reproduction for a new researcher

Use the [README](../../README.md) release acquisition steps, verify the post-tag manifest asset against the checked-out commit, follow the Windows quick start, run `prototype demo`, then use the documented metadata-based run-ID lookup and `prototype reproduce RUN_ID`. The guide keeps generated smoke results distinct from corpus or Humanize research results.

**Phase 26.1 disposition:** The v0.1.1 public release satisfies the fresh-clone, install, demo, and smoke-reproduction goal on the validated Windows/Python 3.14.7 environment. Cross-platform behavior and a clean Windows machine without cached model data were not tested; these are not claims of universal reproducibility.