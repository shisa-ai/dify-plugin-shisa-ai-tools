# Contributing

Thank you for helping improve the Shisa AI Tools integration for Dify.

## Before opening a pull request

1. Open or reference an issue that describes the change.
2. Keep standard LLM, ASR, and TTS model interfaces in the separate Model Provider repository; advanced synchronous workflow tools belong here.
3. Do not add undocumented claims about models, prices, formats, voices, performance, availability, or Dify endorsement.
4. Use current official documentation from https://docs.shisa.ai/ and dynamic API catalogues where available.
5. Never commit API keys, `.env`, `.dev.vars`, Dify application tokens, user content, remote-debug credentials, or generated `.difypkg` files.
6. Dify Tool outputs are completed results; do not claim progressive workflow audio or translation streaming.

## Validation

```bash
python3.12 -m venv .venv
. .venv/bin/activate
UV_EXCLUDE_NEWER=2026-07-29T00:00:00Z uv sync --frozen --no-install-project
uv run --frozen python -m compileall -q .
uv run --frozen python -m unittest discover -s tests -v
uv run --frozen pip-audit --require-hashes -r requirements.txt
uv run --frozen python scripts/validate_workflows.py
```

Package and install the plugin in a test Dify workspace when changing API behavior. Test affected tools with non-sensitive data and do not expose production credentials in output, logs, or fixtures.

## Releases

Release publication is automated and tag-only. After the version PR has passed CI and been merged to `main`, create the matching protected tag (for example, `v1.0.0`) on that merge commit. Do not publish packages from pull requests or commit generated release files. The release workflow builds and validates the package, scans dependencies, embeds the runtime SBOM in the package and records provenance.

## Pull requests

Keep changes focused, update `CHANGELOG.md`, and describe user-visible behavior and validation performed. Contributions are accepted under the [Apache License 2.0](LICENSE).
