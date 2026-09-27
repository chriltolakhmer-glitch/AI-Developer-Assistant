# Changelog

## 0.1.1 — Reproducible Release Publication (2026-09-28)

- Correct release provenance handling: the committed manifest identifies the source baseline, while the post-tag release asset records the exact immutable tag commit SHA.
- Publish the v0.1.1 tag and release manifest/verification assets for fresh-clone validation.
- Clarify tag-only installation, demo output limits, and reproducible run-ID discovery.
- No retrieval, evaluation, Humanize pilot, or benchmark behavior changed.

## 0.1.0 — Research Prototype (2026-09-28)

- Package the existing local research prototype with a reproducible CLI entry point.
- Document clean installation, demo, evaluation, validation, and run reproduction.
- Pin the build backend and provide an aggregate exact-version dependency lock.
- Improve configuration, validation-path, corrupted-run, and reproduction diagnostics.
- Add contributor, support, and development workflow guidance.
- Keep the Humanize pilot frozen and benchmark expansion deferred.
