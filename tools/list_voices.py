import json
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from shisa_client import get_voice_catalog


class ListVoicesTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        language = str(tool_parameters.get("language") or "").strip().lower()
        audio_format = str(tool_parameters.get("format") or "").strip().lower()
        voices = get_voice_catalog(self.runtime.credentials)

        requested_language = language.split("-")[0]
        language_aliases = {"ja": "japanese", "en": "english", "zh": "chinese"}
        requested_language = language_aliases.get(requested_language, requested_language)

        filtered = []
        for voice in voices:
            formats = [str(value).lower() for value in voice.get("formats", [])]
            if requested_language and requested_language not in str(voice.get("language", "")).lower():
                continue
            if audio_format and audio_format not in formats:
                continue
            filtered.append(voice)

        yield self.create_json_message(filtered)
        yield self.create_text_message(
            json.dumps(filtered, ensure_ascii=False, indent=2)
            if filtered
            else "No Shisa AI voices matched the requested filters."
        )
