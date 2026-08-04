from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from shisa_client import generate_speech, get_voice_catalog, resolve_voice


MIME_TYPES = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "ogg": "audio/ogg",
    "flac": "audio/flac",
    "pcm": "application/octet-stream",
}


class GenerateSpeechTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        text = str(tool_parameters.get("text") or "").strip()
        voice_query = str(tool_parameters.get("voice_id") or "").strip()
        audio_format = str(tool_parameters.get("format") or "mp3").strip().lower()

        if not text:
            raise ValueError("Text must not be empty")
        if not voice_query:
            raise ValueError("Voice name, description, or ID is required")
        if audio_format not in MIME_TYPES:
            raise ValueError(f"Unsupported audio format: {audio_format}")

        voices = get_voice_catalog(self.runtime.credentials)
        selected = resolve_voice(voices, voice_query)
        voice_id = str(selected["id"])

        formats = {str(value).lower() for value in selected.get("formats", [])}
        if audio_format not in formats:
            available = ", ".join(sorted(formats)) or "none"
            raise ValueError(
                f"Voice {voice_id} does not support {audio_format}; available formats: {available}"
            )

        audio = generate_speech(
            self.runtime.credentials, text, voice_id, audio_format
        )
        yield self.create_blob_message(
            blob=audio,
            meta={
                "mime_type": MIME_TYPES[audio_format],
                "voice_id": voice_id,
                "format": audio_format,
            },
        )
