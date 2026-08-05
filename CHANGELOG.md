# Changelog

All notable user-visible changes are documented here.

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
