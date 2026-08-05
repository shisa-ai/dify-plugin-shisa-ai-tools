# Release smoke-test workflow

This release gate covers every Shisa AI Tools node and the regressions that must not return.

## Automated protected-release gate

The protected GitHub `release` environment must contain:

- Secret `SHISA_API_KEY`: a limited test-account API key.

The voice is selected dynamically from the current catalogue. The test prefers a Japanese voice and WAV, then falls back only to another currently advertised ASR-compatible native format.

Every protected `v*` tag runs:

```bash
uv run --frozen python -m unittest discover -s tests -v
uv run --frozen python scripts/live_smoke_test.py
```

The live test executes the same client paths used by all four Dify nodes:

1. Fetch the dynamic voice catalogue.
2. Select a voice and generate a native audio file without transcoding.
3. Transcribe that generated audio while sending every documented optional ASR parameter.
4. Translate Japanese text to English using multipart form data.

It fails on an empty or invalid result, missing voice format, tiny audio response, authentication failure, or the non-preferred `シサAI` brand spelling. Credentials and generated audio are not printed or saved.

## Dify post-install workflow

After installing the release package, construct and export a Dify **Workflow** with this deterministic chain:

```text
Start
  → List TTS Voices
  → Generate Speech (WAV)
  → Transcribe Audio
  → Translate Text
  → End
```

### Start inputs

| Input | Type | Suggested value |
|---|---|---|
| `voice_id` | text | Stable Japanese voice UUID from List TTS Voices |
| `speech_text` | text | `シーサ・エーアイの音声認識と音声合成をテストします。` |
| `translation_text` | text | `Shisa AIの音声ツールをテストします。` |

### Node settings

**List TTS Voices**

- `language`: `ja`
- `format`: `wav`

**Generate Speech**

- `text`: `speech_text`
- `voice_id`: `voice_id`
- `format`: `wav`

**Transcribe Audio**

- `audio`: generated WAV file
- `language`: `ja`
- `hotwords`: `["Shisa AI","Shisa V2.1","Dify"]`
- `temperature`: `0.0`
- `top_p`: `0.85`
- `frequency_penalty`: `0.5`
- `repetition_penalty`: `1.05`
- `vad`: `1`

**Translate Text**

- `text`: `translation_text`
- `source_lang`: `ja`
- `target_lang`: `en`

### End outputs and pass criteria

Expose these outputs:

- Voice-list JSON: non-empty and selected voice advertises WAV.
- Generated audio: non-empty WAV.
- ASR text: non-empty and does not contain `シサAI`.
- Complete ASR JSON: contains `text`; preserve `language` and `confidence` when supplied by the API.
- Translation text: non-empty English text; no account-balance object.

Also run one minimal Transcribe Audio node with every optional field blank. Its outgoing request must contain only `audio`, preserving Shisa API defaults.

## DSL verification rule

Do not publish a hand-written DSL as installable. Import the workflow into the target Dify version, run it successfully, then re-export it. Commit only that Dify-exported baseline under `docs/dify-smoke-test/` and rerun it after each plugin update.
