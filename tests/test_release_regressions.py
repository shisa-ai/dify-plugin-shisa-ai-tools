import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import yaml

from shisa_client import (
    generate_speech,
    get_voice_catalog,
    normalize_transcript,
    resolve_voice,
)


class ReleaseDescriptorTests(unittest.TestCase):
    def test_provider_exposes_exact_release_smoke_test_tools(self):
        provider = yaml.safe_load(
            Path("provider/shisa_ai_tools.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(
            provider["tools"],
            [
                "tools/list_voices.yaml",
                "tools/generate_speech.yaml",
                "tools/transcribe_audio.yaml",
                "tools/translate_text.yaml",
            ],
        )

    def test_every_tool_descriptor_points_to_existing_python_source(self):
        provider = yaml.safe_load(
            Path("provider/shisa_ai_tools.yaml").read_text(encoding="utf-8")
        )
        for descriptor_path in provider["tools"]:
            descriptor = yaml.safe_load(
                Path(descriptor_path).read_text(encoding="utf-8")
            )
            source = Path(descriptor["extra"]["python"]["source"])
            self.assertTrue(source.is_file(), f"missing tool source: {source}")

    def test_release_tool_parameters_do_not_drift(self):
        expected = {
            "list_voices": {"search", "language", "format"},
            "generate_speech": {"text", "voice_id", "format"},
            "transcribe_audio": {
                "audio",
                "language",
                "hotwords",
                "temperature",
                "top_p",
                "frequency_penalty",
                "repetition_penalty",
                "vad",
            },
            "translate_text": {"text", "source_lang", "target_lang"},
        }
        for name, parameters in expected.items():
            descriptor = yaml.safe_load(
                Path(f"tools/{name}.yaml").read_text(encoding="utf-8")
            )
            self.assertEqual(
                {item["name"] for item in descriptor["parameters"]}, parameters
            )


class VoiceAndSpeechRegressionTests(unittest.TestCase):
    @patch("shisa_client.httpx.get")
    def test_voice_catalog_is_dynamic_and_uses_official_endpoint(self, get: Mock):
        response = Mock(status_code=200)
        response.json.return_value = {
            "voices": [
                {
                    "id": "voice-1",
                    "displayName": "JA Test Voice",
                    "language": "Japanese",
                    "formats": ["mp3", "wav"],
                }
            ]
        }
        get.return_value = response

        voices = get_voice_catalog({"api_key": "test"})

        self.assertEqual(voices[0]["id"], "voice-1")
        self.assertEqual(get.call_args.args[0], "https://api.shisa.ai/tts/voices")
        self.assertEqual(get.call_args.kwargs["headers"], {"Authorization": "Bearer test"})

    def test_voice_resolution_supports_uuid_name_and_description(self):
        voices = [
            {
                "id": "voice-uuid",
                "displayName": "Japanese Host",
                "description": "JA Female Kids Show Host",
            }
        ]
        self.assertEqual(resolve_voice(voices, "voice-uuid")["id"], "voice-uuid")
        self.assertEqual(resolve_voice(voices, "Japanese Host")["id"], "voice-uuid")
        self.assertEqual(resolve_voice(voices, "Kids Show")["id"], "voice-uuid")

    def test_ambiguous_voice_description_is_rejected(self):
        voices = [
            {"id": "one", "description": "Japanese Host One"},
            {"id": "two", "description": "Japanese Host Two"},
        ]
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            resolve_voice(voices, "Japanese Host")

    @patch("shisa_client.httpx.post")
    def test_native_tts_payload_is_non_streaming_and_bytes_are_unchanged(self, post: Mock):
        native_audio = b"native-audio-without-transcoding"
        post.return_value = Mock(status_code=200, content=native_audio)

        result = generate_speech(
            {"api_key": "test"}, "Shisa AI", "voice-uuid", "flac"
        )

        self.assertIs(result, native_audio)
        self.assertEqual(post.call_args.args[0], "https://api.shisa.ai/tts")
        self.assertEqual(
            post.call_args.kwargs["json"],
            {
                "text": "Shisa AI",
                "voice_id": "voice-uuid",
                "format": "flac",
                "stream": False,
            },
        )


class TranscriptRegressionTests(unittest.TestCase):
    def test_only_exact_music_marker_is_suppressed(self):
        self.assertEqual(normalize_transcript("[Music]"), "")
        self.assertEqual(normalize_transcript(" [MUSIC] "), "")
        self.assertEqual(normalize_transcript("music"), "music")
        self.assertEqual(normalize_transcript("[Music] hello"), "[Music] hello")


class ErrorRegressionTests(unittest.TestCase):
    @patch("shisa_client.httpx.get")
    def test_authentication_error_does_not_get_misreported_as_empty_catalog(self, get: Mock):
        get.return_value = httpx.Response(
            401,
            text="invalid token",
            request=httpx.Request("GET", "https://api.shisa.ai/tts/voices"),
        )
        with self.assertRaisesRegex(ValueError, "authentication failed"):
            get_voice_catalog({"api_key": "invalid"})


if __name__ == "__main__":
    unittest.main()
