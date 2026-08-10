from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from shisa_client import normalize_transcript, parse_hotwords, transcribe_audio


class TranscribeAudioTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        audio_file = tool_parameters.get("audio")
        if audio_file is None or not hasattr(audio_file, "blob"):
            raise ValueError("An audio file is required")

        language = str(tool_parameters.get("language") or "").strip() or None
        raw_hotwords = tool_parameters.get("hotwords")
        hotwords = parse_hotwords(raw_hotwords) if raw_hotwords else None

        def optional_float(name: str) -> float | None:
            value = tool_parameters.get(name)
            if value is None or value == "":
                return None
            try:
                return float(value)
            except (TypeError, ValueError) as error:
                raise ValueError(f"{name} must be a number") from error

        raw_vad = tool_parameters.get("vad")
        try:
            vad = None if raw_vad is None or raw_vad == "" else int(raw_vad)
        except (TypeError, ValueError) as error:
            raise ValueError("vad must be an integer") from error

        result = transcribe_audio(
            self.runtime.credentials,
            audio_file.blob,
            language=language,
            hotwords=hotwords,
            temperature=optional_float("temperature"),
            top_p=optional_float("top_p"),
            frequency_penalty=optional_float("frequency_penalty"),
            repetition_penalty=optional_float("repetition_penalty"),
            vad=vad,
        )
        transcript = normalize_transcript(str(result["text"]))
        if transcript != result["text"]:
            result = {**result, "text": transcript}

        yield self.create_text_message(transcript)
        yield self.create_json_message(result)
