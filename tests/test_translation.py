import unittest
from unittest.mock import patch

import httpx

from shisa_client import translate_text


class TranslationClientTests(unittest.TestCase):
    def test_translation_uses_multipart_and_returns_only_content(self):
        response = httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "It is nice weather today."}}],
                "balance": {"free": 1000, "premium": 0},
            },
            request=httpx.Request("POST", "https://api.shisa.ai/translate/"),
        )
        with patch("shisa_client.httpx.post", return_value=response) as request:
            result = translate_text(
                {"api_key": "test-placeholder"},
                text="今日は良い天気です。",
                source_lang="ja",
                target_lang="en",
            )

        self.assertEqual(result, "It is nice weather today.")
        fields = request.call_args.kwargs["files"]
        self.assertEqual(fields["text"], (None, "今日は良い天気です。"))
        self.assertEqual(fields["source_lang"], (None, "ja"))
        self.assertEqual(fields["target_lang"], (None, "en"))
        self.assertEqual(fields["stream"], (None, "false"))

    def test_invalid_response_is_rejected(self):
        response = httpx.Response(
            200,
            json={"choices": []},
            request=httpx.Request("POST", "https://api.shisa.ai/translate/"),
        )
        with patch("shisa_client.httpx.post", return_value=response):
            with self.assertRaisesRegex(ValueError, "invalid translation response"):
                translate_text(
                    {"api_key": "test-placeholder"},
                    text="test",
                    source_lang="en",
                    target_lang="ja",
                )


if __name__ == "__main__":
    unittest.main()
