# Release smoke-test

Every Tools release must prove the nodes work against the live Shisa API and the
real Dify workflow before the package is published.

## Automated protected-release gate

The protected GitHub `release` environment must contain:

- Secret `SHISA_API_KEY`: a limited test-account API key.

The voice is selected dynamically from the current catalogue. The test prefers a
Japanese voice and WAV, then falls back only to another currently advertised
ASR-compatible native format.

Every protected `v*` tag runs:

```bash
uv run --frozen python -m unittest discover -s tests -v
uv run --frozen python scripts/live_smoke_test.py
```

The live test exercises the same client paths used by all four Tools nodes:

1. Fetch the dynamic voice catalogue.
2. Select a voice and generate a native audio file without transcoding.
3. Transcribe that generated audio while sending every documented optional ASR parameter.
4. Translate Japanese text to English using multipart form data.

It fails on an empty or invalid result, missing voice format, tiny audio
response, authentication failure, or the non-preferred `シサAI` brand spelling.
Credentials and generated audio are not printed or saved.

## Verified Dify workflow

The Dify node execution is verified with the committed fixture in the
[shisa-dify-workflows](https://github.com/shisa-ai/shisa-dify-workflows)
repository:

```text
fixtures/shisa-tools-smoke.yml
```

Chain:

```text
Start
  → List TTS Voices            (dynamic, Japanese + WAV)
  → Select Dynamic Voice       (Code node, flattens Dify output)
  → Generate Speech            (native WAV)
  → Transcribe Audio (full)    (all documented optional ASR parameters)
  → Transcribe Audio (blank)   (optional fields omitted → API defaults)
  → Translate Text             (Japanese → English)
  → End
```

Verified baseline: Dify Cloud run `297e1a02-1438-4fcb-a1e0-85cb80bd5070`
(status: succeeded, 8 steps).

## Pass criteria

- Voice-list JSON is non-empty and the selected voice advertises WAV.
- Generated audio is a non-empty WAV file.
- Full-parameter ASR transcript is non-empty and does not contain `シサAI`.
- Blank-parameter ASR request omits every optional field, preserving Shisa API defaults.
- Structured ASR output preserves `text`, `language`, and `confidence` when supplied by the API.
- Translation returns non-empty English text with no account-balance object.

## DSL verification rule

Commit only DSLs that have passed a real **Dify import → execution → re-export**
cycle. Re-import `Shisa-AI-Tools-Release-Smoke-Test.yml` into the target Dify
version, run it, then commit the re-exported baseline so the file stays
byte-for-byte what Dify produced.
