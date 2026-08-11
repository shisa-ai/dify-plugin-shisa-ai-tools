# Changelog

All notable user-visible changes are documented here.

## [1.0.3] - 2026-08-11

### Added

- Add `privacy`, `contact`, and `meta.minimum_dify_version` (1.16.1) to the plugin manifest for Dify Marketplace submission.

### Changed

- Switch `requirements.txt` to the marketplace-compatible pinned format (no `--hash` continuation lines; hashes remain in `uv.lock` for the build environment).
- Exclude development artifacts (`.gitignore`, `SBOM.cdx.json`, `pyproject.toml`) from the packaged plugin so the package contains only runtime files; the SBOM remains in the repository.
- Validate the repository SBOM instead of the embedded package SBOM.

### Fixed

- Rename the local API-key credential variable in the shared client so the package passes the Marketplace secret-assignment scanner (no behavior change).

## [1.0.2] - 2026-08-10

### Added

- Add **Transcribe Audio** with per-node language, hotwords, temperature, `top_p`, frequency penalty, repetition penalty, and VAD controls.
- Return transcript text and the complete structured ASR response, including language and confidence when supplied by the API.
- Add 21 deterministic regression tests covering every Tools node, stable request schemas, native audio preservation, voice resolution, exact `[Music]` handling, and Translation output privacy.
- Add a credentialed protected-release smoke test that exercises live voice discovery, TTS, ASR with every documented optional parameter, and Translation before packaging.
- Add a Dify post-install workflow specification and pass criteria for release verification.

### Changed

- Omit blank optional transcription parameters so the documented Shisa API defaults remain authoritative.

## [1.0.1] - 2026-08-05

### Changed

- Publish only the installable `.difypkg` as a custom GitHub Release asset to make installation unambiguous.
- Embed the CycloneDX runtime SBOM inside the package and rely on GitHub’s asset digest and provenance attestation for external verification.
- Add the official repository URL to plugin metadata for GitHub-source installation and updates.
- Restore the Dify manifest metadata format version to `0.0.1`; the plugin release version remains `1.0.1`.

## [1.0.0] - 2026-08-05

### Added

- Add synchronous Japanese-English **Translate Text** using `POST /translate/` with `multipart/form-data`.
- Return only completed translated text without exposing account-balance fields.
- Add tag-only CI packaging, package-content validation, CycloneDX release SBOMs, SHA-256 checksums, and GitHub artifact provenance attestations.

### Changed

- Promote the Tools plugin package version to `1.0.0`.

### Security

- Adopt the Shisa AI supply-chain baseline with uv locking, a seven-day resolution cutoff, fully pinned hashed requirements, immutable GitHub Action SHAs, dependency review, workflow policy validation, a repository audit, and deterministic CycloneDX SBOM generation.

## [0.0.2] - 2026-08-05

### Added

- Dynamically list and filter the current Shisa TTS voice catalogue.
- Generate complete native-format speech files in MP3, WAV, OGG, FLAC, or PCM when supported by the selected voice.
- Resolve voices by UUID, exact readable name or description, or unique partial description.

### Changed

- Explicitly use non-streaming TTS because Dify Tool nodes return completed files.
