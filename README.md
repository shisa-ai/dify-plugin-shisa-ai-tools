# Shisa AI Tools for Dify

Advanced workflow tools for the native Shisa AI speech API.

## Tools

- **List TTS Voices** dynamically retrieves voice IDs, languages, native formats, and streaming capabilities from Shisa AI.
- **Generate Speech** produces a complete MP3, WAV, OGG, FLAC, or PCM file when supported by the selected voice.

Dify tool outputs are complete files, so this plugin intentionally uses Shisa's non-streaming TTS response. It does not claim progressive playback inside Dify workflows.

## Configuration

Add your Shisa AI API key and keep the default API base URL:

```text
https://api.shisa.ai
```

Use **List TTS Voices** to discover a voice UUID before configuring **Generate Speech**.
