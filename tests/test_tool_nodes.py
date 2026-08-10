import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from dify_plugin.entities.tool import ToolRuntime

from tools.generate_speech import GenerateSpeechTool
from tools.list_voices import ListVoicesTool
from tools.transcribe_audio import TranscribeAudioTool
from tools.translate_text import TranslateTextTool


class ToolNodeRegressionTests(unittest.TestCase):
    def runtime(self) -> ToolRuntime:
        return ToolRuntime(
            credentials={"api_key": "test"}, user_id="release-test", session_id="release-test"
        )

    @patch("tools.list_voices.get_voice_catalog")
    def test_list_voices_node_emits_json_and_readable_text(self, catalog: Mock):
        catalog.return_value = [
            {
                "id": "voice-ja",
                "displayName": "Japanese Test Voice",
                "language": "Japanese",
                "formats": ["wav", "mp3"],
                "streaming": False,
            },
            {
                "id": "voice-en",
                "displayName": "English Test Voice",
                "language": "English",
                "formats": ["wav"],
                "streaming": True,
            },
        ]
        tool = ListVoicesTool(self.runtime(), Mock())

        messages = list(tool._invoke({"language": "ja", "format": "wav"}))

        self.assertEqual([message.type.value for message in messages], ["json", "text"])
        self.assertEqual(messages[0].message.json_object[0]["id"], "voice-ja")
        self.assertIn("Japanese Test Voice", messages[1].message.text)
        self.assertNotIn("English Test Voice", messages[1].message.text)

    @patch("tools.generate_speech.generate_speech", return_value=b"native-wav")
    @patch("tools.generate_speech.get_voice_catalog")
    def test_generate_speech_node_emits_native_blob_with_metadata(
        self, catalog: Mock, generate: Mock
    ):
        catalog.return_value = [
            {
                "id": "voice-ja",
                "displayName": "Japanese Test Voice",
                "formats": ["wav"],
            }
        ]
        tool = GenerateSpeechTool(self.runtime(), Mock())

        messages = list(
            tool._invoke(
                {
                    "text": "Shisa AI",
                    "voice_id": "Japanese Test Voice",
                    "format": "wav",
                }
            )
        )

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].type.value, "blob")
        self.assertEqual(messages[0].message.blob, b"native-wav")
        self.assertEqual(messages[0].meta["mime_type"], "audio/wav")
        generate.assert_called_once_with(
            {"api_key": "test"}, "Shisa AI", "voice-ja", "wav"
        )

    @patch("tools.transcribe_audio.transcribe_audio")
    def test_transcribe_node_forwards_every_parameter_and_emits_structured_result(
        self, transcribe: Mock
    ):
        transcribe.return_value = {
            "text": "Shisa AI",
            "language": "ja",
            "confidence": 0.99,
        }
        tool = TranscribeAudioTool(self.runtime(), Mock())
        audio = SimpleNamespace(blob=b"wav-bytes")

        messages = list(
            tool._invoke(
                {
                    "audio": audio,
                    "language": "ja",
                    "hotwords": '["Shisa AI","Dify"]',
                    "temperature": 0.0,
                    "top_p": 0.85,
                    "frequency_penalty": 0.5,
                    "repetition_penalty": 1.05,
                    "vad": 1,
                }
            )
        )

        self.assertEqual([message.type.value for message in messages], ["text", "json"])
        self.assertEqual(messages[0].message.text, "Shisa AI")
        self.assertEqual(messages[1].message.json_object["confidence"], 0.99)
        transcribe.assert_called_once_with(
            {"api_key": "test"},
            b"wav-bytes",
            language="ja",
            hotwords=["Shisa AI", "Dify"],
            temperature=0.0,
            top_p=0.85,
            frequency_penalty=0.5,
            repetition_penalty=1.05,
            vad=1,
        )

    @patch("tools.transcribe_audio.transcribe_audio", return_value={"text": "[Music]"})
    def test_transcribe_node_suppresses_only_exact_music_marker(self, _: Mock):
        tool = TranscribeAudioTool(self.runtime(), Mock())
        messages = list(tool._invoke({"audio": SimpleNamespace(blob=b"audio")}))
        self.assertEqual(messages[0].message.text, "")
        self.assertEqual(messages[1].message.json_object["text"], "")

    @patch("tools.translate_text.translate_text", return_value="Testing Shisa AI tools.")
    def test_translate_node_emits_only_translation_text(self, translate: Mock):
        tool = TranslateTextTool(self.runtime(), Mock())

        messages = list(
            tool._invoke(
                {
                    "text": "Shisa AIのツールをテストします。",
                    "source_lang": "ja",
                    "target_lang": "en",
                }
            )
        )

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].type.value, "text")
        self.assertEqual(messages[0].message.text, "Testing Shisa AI tools.")
        translate.assert_called_once_with(
            {"api_key": "test"},
            text="Shisa AIのツールをテストします。",
            source_lang="ja",
            target_lang="en",
        )


if __name__ == "__main__":
    unittest.main()
