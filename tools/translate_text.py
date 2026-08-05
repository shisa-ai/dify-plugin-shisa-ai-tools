from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from shisa_client import translate_text


class TranslateTextTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        text = str(tool_parameters.get("text") or "").strip()
        source_lang = str(tool_parameters.get("source_lang") or "").strip().lower()
        target_lang = str(tool_parameters.get("target_lang") or "").strip().lower()

        if not text:
            raise ValueError("Text must not be empty")
        if source_lang not in {"ja", "en"}:
            raise ValueError("Source language must be ja or en")
        if target_lang not in {"ja", "en"}:
            raise ValueError("Target language must be ja or en")
        if source_lang == target_lang:
            raise ValueError("Source and target languages must be different")

        translation = translate_text(
            self.runtime.credentials,
            text=text,
            source_lang=source_lang,
            target_lang=target_lang,
        )
        yield self.create_text_message(translation)
