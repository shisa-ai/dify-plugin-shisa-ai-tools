import base64
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import yaml

from shisa_client import parse_hotwords, transcribe_audio


class ASRClientTests(unittest.TestCase):
    def test_tool_exposes_every_documented_graph_parameter(self):
        descriptor = yaml.safe_load(
            Path("tools/transcribe_audio.yaml").read_text(encoding="utf-8")
        )
        parameters = {parameter["name"] for parameter in descriptor["parameters"]}
        self.assertEqual(
            parameters,
            {
                "audio",
                "language",
                "hotwords",
                "temperature",
                "top_p",
                "frequency_penalty",
                "repetition_penalty",
                "vad",
            },
        )

    def test_parse_hotwords_accepts_supported_input_forms(self):
        self.assertEqual(parse_hotwords('["Shisa AI", "Dify"]'), ["Shisa AI", "Dify"])
        self.assertEqual(
            parse_hotwords("Shisa AI\nDify,Shisa ASR"),
            ["Shisa AI", "Dify", "Shisa ASR"],
        )
        self.assertEqual(parse_hotwords(["Shisa AI", " Dify "]), ["Shisa AI", "Dify"])

    def test_parse_hotwords_rejects_non_string_array_items(self):
        with self.assertRaises(ValueError):
            parse_hotwords('["Shisa AI", 2]')

    @patch("shisa_client.httpx.post")
    def test_minimal_request_omits_all_optional_parameters(self, post: Mock):
        response = Mock(status_code=200)
        response.json.return_value = {
            "text": "hello",
            "language": "en",
            "confidence": 0.98,
        }
        post.return_value = response

        result = transcribe_audio({"api_key": "test"}, b"audio")

        self.assertEqual(result["text"], "hello")
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload, {"audio": base64.b64encode(b"audio").decode("ascii")})

    @patch("shisa_client.httpx.post")
    def test_request_sends_all_explicit_graph_parameters(self, post: Mock):
        response = Mock(status_code=200)
        response.json.return_value = {
            "text": "Shisa AI",
            "language": "ja",
            "confidence": 0.99,
        }
        post.return_value = response

        result = transcribe_audio(
            {"api_key": "test", "api_base": "https://api.shisa.ai/"},
            b"audio",
            language="ja",
            hotwords=["Shisa AI", "Dify"],
            temperature=0.0,
            top_p=0.85,
            frequency_penalty=0.5,
            repetition_penalty=1.05,
            vad=1,
        )

        self.assertEqual(result["confidence"], 0.99)
        self.assertEqual(
            post.call_args.kwargs["json"],
            {
                "audio": base64.b64encode(b"audio").decode("ascii"),
                "language": "ja",
                "hotwords": ["Shisa AI", "Dify"],
                "temperature": 0.0,
                "top_p": 0.85,
                "frequency_penalty": 0.5,
                "repetition_penalty": 1.05,
                "vad": 1,
            },
        )


if __name__ == "__main__":
    unittest.main()
