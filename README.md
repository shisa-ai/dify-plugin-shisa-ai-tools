# Shisa AI Tools for Dify

Advanced Dify workflow tools for Shisa AI speech and Translation APIs.

> This repository is maintained by Shisa AI. It does not imply certification, endorsement, or support by Dify unless separately stated by Dify.

Use this plugin separately from the [Shisa AI Model Provider](https://github.com/shisa-ai/dify-plugin-shisa-ai). Each plugin has its own Dify credential configuration.

## Tools

### List TTS Voices

Dynamically retrieves and filters current voice names, descriptions, UUIDs, languages, native formats, and streaming capabilities from `GET /tts/voices`.

### Generate Speech

Accepts a human-readable description such as `JA Female Kids Show Host`, or a voice UUID, and generates a complete MP3, WAV, OGG, FLAC, or PCM file when the selected voice supports that format.

### Translate Text

Translates completed text between Japanese and English with `POST /translate/`. Translation requests use `multipart/form-data`, and the tool returns only the translated text rather than account-balance fields from the API response.

Dify Tool nodes are synchronous. This plugin intentionally uses non-streaming TTS and Translation responses and does not claim progressive playback or partial translation inside Dify workflows.

## Requirements

- A Shisa AI account and API key from [Shisa Platform](https://platform.shisa.ai/)
- A Dify installation that supports Tool plugins
- Python 3.12 for local development

Current prices, quotas, available voices, formats, and service behavior can change. Check [Shisa Platform](https://platform.shisa.ai/) and the [official API documentation](https://docs.shisa.ai/) for current information.

## Installation

1. Download `shisa-ai-tools-1.0.1.difypkg` from the [v1.0.0 GitHub Release](https://github.com/shisa-ai/dify-plugin-shisa-ai-tools/releases/tag/v1.0.1).
2. Optionally verify its GitHub-provided SHA-256 digest and provenance attestation.
3. In Dify, open **Plugins**, choose installation from a local package, and upload the file.
4. Configure the Tools provider with your Shisa AI API key.
5. Add the desired Shisa AI Tool node to a Workflow or Chatflow.

Only the `.difypkg` file is installable in Dify. GitHub’s automatically generated **Source code (zip)** and **Source code (tar.gz)** archives are not plugin packages.

The default API base URL is:

```text
https://api.shisa.ai
```

## Usage

For speech generation, use **List TTS Voices** to inspect the live catalogue, then pass a readable voice description or exact UUID to **Generate Speech**.

For translation, choose different source and target languages:

```text
Text: 今日は素晴らしい天気ですね。
Source: ja
Target: en
```

Official references:

- [TTS documentation](https://docs.shisa.ai/tts/)
- [Translation API reference](https://docs.shisa.ai/translation/endpoints)
- [Authentication](https://docs.shisa.ai/guides/authentication)

## Development

```bash
python3.12 -m venv .venv
. .venv/bin/activate
uv sync --frozen --no-install-project
uv run --frozen python main.py
```

Never publish `.env`, `.dev.vars`, Shisa API keys, Dify application tokens, or remote-debug credentials.

## Package

With the Dify plugin CLI installed:

```bash
dify plugin package .
```

Protected `v*` tags invoke `.github/workflows/release.yml`. CI builds and validates the `.difypkg`, embeds a runtime SBOM, attests provenance, and publishes only the installable package to the matching GitHub Release. Generated release files are excluded from Git.

## License

Licensed under the [Apache License 2.0](LICENSE).

## Security and privacy

- Report vulnerabilities according to [SECURITY.md](SECURITY.md).
- Data-handling details are documented in [PRIVACY.md](PRIVACY.md).
- Contributions are described in [CONTRIBUTING.md](CONTRIBUTING.md).
