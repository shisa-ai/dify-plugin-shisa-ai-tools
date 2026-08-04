from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from shisa_client import get_voice_catalog, voice_label


class ListVoicesTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        search = str(tool_parameters.get("search") or "").strip().casefold()
        language = str(tool_parameters.get("language") or "").strip().lower()
        audio_format = str(tool_parameters.get("format") or "").strip().lower()
        voices = get_voice_catalog(self.runtime.credentials)

        requested_language = language.split("-")[0]
        language_aliases = {"ja": "japanese", "en": "english", "zh": "chinese"}
        requested_language = language_aliases.get(requested_language, requested_language)

        filtered = []
        for voice in voices:
            formats = [str(value).lower() for value in voice.get("formats", [])]
            searchable = " ".join(
                str(voice.get(field, ""))
                for field in ("id", "displayName", "name", "description")
            ).casefold()
            if search and search not in searchable:
                continue
            if requested_language and requested_language not in str(voice.get("language", "")).lower():
                continue
            if audio_format and audio_format not in formats:
                continue
            filtered.append(voice)

        yield self.create_json_message(filtered)
        if filtered:
            lines = []
            for voice in filtered:
                formats = ", ".join(str(value) for value in voice.get("formats", []))
                lines.append(
                    f"{voice_label(voice)}\n"
                    f"  Voice ID: {voice['id']}\n"
                    f"  Language: {voice.get('language', 'Not specified')}\n"
                    f"  Formats: {formats or 'Not specified'}\n"
                    f"  Streaming: {bool(voice.get('streaming'))}"
                )
            yield self.create_text_message("\n\n".join(lines))
        else:
            yield self.create_text_message("No Shisa AI voices matched the requested filters.")
