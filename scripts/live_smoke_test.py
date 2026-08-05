#!/usr/bin/env python3
"""Run paid, credentialed smoke tests against every Shisa AI Tools endpoint.

The script prints no credentials and stores no API responses or generated audio.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shisa_client import (  # noqa: E402
    generate_speech,
    get_voice_catalog,
    transcribe_audio,
    translate_text,
    voice_label,
)


def fail(message: str) -> None:
    raise RuntimeError(message)


def supported_formats(voice: dict[str, Any]) -> list[str]:
    accepted = {"wav", "mp3", "ogg", "flac"}
    return [str(value).lower() for value in voice.get("formats", []) if str(value).lower() in accepted]


def select_voice(voices: list[dict[str, Any]]) -> tuple[dict[str, Any], str]:
    candidates = voices

    japanese = [
        voice for voice in candidates
        if "japan" in str(voice.get("language", "")).casefold()
        or str(voice.get("language", "")).casefold().startswith("ja")
    ]
    for voice in japanese + candidates:
        formats = supported_formats(voice)
        if formats:
            preferred = next((item for item in ("wav", "flac", "ogg", "mp3") if item in formats), formats[0])
            return voice, preferred
    fail("No live TTS voice advertises an ASR-compatible native format")


def main() -> int:
    api_key = os.environ.get("SHISA_API_KEY", "").strip()
    if not api_key:
        fail("SHISA_API_KEY is required")
    credentials = {
        "api_key": api_key,
        "api_base": os.environ.get("SHISA_API_BASE", "https://api.shisa.ai"),
    }

    voices = get_voice_catalog(credentials)
    voice, audio_format = select_voice(voices)

    spoken_text = os.environ.get(
        "SHISA_TEST_SPEECH_TEXT",
        "シーサ・エーアイの音声認識と音声合成をテストします。",
    )
    audio = generate_speech(
        credentials,
        spoken_text,
        str(voice["id"]),
        audio_format,
    )
    if len(audio) < 100:
        fail("TTS returned unexpectedly little audio data")

    asr = transcribe_audio(
        credentials,
        audio,
        language="ja",
        hotwords=["Shisa AI", "Shisa V2.1", "Dify"],
        temperature=0.0,
        top_p=0.85,
        frequency_penalty=0.5,
        repetition_penalty=1.05,
        vad=1,
    )
    transcript = str(asr.get("text", "")).strip()
    if not transcript:
        fail("ASR returned an empty transcript")
    if "シサAI" in transcript:
        fail("ASR returned the non-preferred シサAI brand spelling")

    translation = translate_text(
        credentials,
        text="Shisa AIの音声ツールをテストします。",
        source_lang="ja",
        target_lang="en",
    ).strip()
    if not translation:
        fail("Translation returned empty text")

    report = {
        "voices": {"status": "pass", "count": len(voices)},
        "tts": {
            "status": "pass",
            "voice": voice_label(voice),
            "format": audio_format,
            "bytes": len(audio),
        },
        "asr": {
            "status": "pass",
            "text": transcript,
            "language": asr.get("language"),
            "confidence": asr.get("confidence"),
        },
        "translation": {"status": "pass", "text": translation},
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"live smoke test failed: {error}", file=sys.stderr)
        raise SystemExit(1)
