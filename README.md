# Shisa AI Tools for Dify

Advanced workflow tools for the native Shisa AI speech API.

## Tools

- **List TTS Voices** dynamically retrieves and searches voice names/descriptions, IDs, languages, native formats, and streaming capabilities from Shisa AI.
- **Generate Speech** accepts a human-readable description such as `JA Female Kids Show Host` (or a UUID) and produces a complete MP3, WAV, OGG, FLAC, or PCM file when supported by that voice.

Dify tool outputs are complete files, so this plugin intentionally uses Shisa's non-streaming TTS response. It does not claim progressive playback inside Dify workflows.

## Configuration

Add your Shisa AI API key and keep the default API base URL:

```text
https://api.shisa.ai
```

Use a voice description directly in **Generate Speech**, or use **List TTS Voices** to search the current catalogue and inspect formats.
