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
pip install -r requirements.txt
python -m compileall -q .
python -m unittest discover -s tests -v
```

Package and install the plugin in a test Dify workspace when changing API behavior. Test affected tools with non-sensitive data and do not expose production credentials in output, logs, or fixtures.

## Pull requests

Keep changes focused, update `CHANGELOG.md`, and describe user-visible behavior and validation performed. Contributions are accepted under the [Apache License 2.0](LICENSE).
