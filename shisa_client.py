from typing import Any

import httpx


def parse_hotwords(value: Any) -> list[str]:
    """Accept a JSON array, Python string list, or comma/newline-separated text."""
    import json

    if value is None or value == "":
        return []
    if isinstance(value, list):
        if not all(isinstance(item, str) for item in value):
            raise ValueError("Hotwords must contain only strings")
        hotwords = [item.strip() for item in value if item.strip()]
    else:
        raw = str(value).strip()
        if not raw:
            return []
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as error:
                raise ValueError(
                    "Hotwords must be valid JSON or a comma/newline-separated list"
                ) from error
            if not isinstance(parsed, list) or not all(
                isinstance(item, str) for item in parsed
            ):
                raise ValueError("Hotwords JSON must be an array of strings")
            hotwords = [item.strip() for item in parsed if item.strip()]
        else:
            hotwords = [
                item.strip()
                for line in raw.splitlines()
                for item in line.split(",")
                if item.strip()
            ]
    if not hotwords:
        raise ValueError("Hotwords must contain at least one word or phrase")
    return hotwords


def api_base(credentials: dict[str, Any]) -> str:
    return str(credentials.get("api_base") or "https://api.shisa.ai").rstrip("/")


def headers(credentials: dict[str, Any]) -> dict[str, str]:
    api_key = str(credentials.get("api_key") or "").strip()
    if not api_key:
        raise ValueError("Shisa AI API key is required")
    return {"Authorization": f"Bearer {api_key}"}


def raise_for_status(response: httpx.Response) -> None:
    if response.status_code < 400:
        return
    message = response.text.strip() or f"HTTP {response.status_code}"
    if response.status_code in (401, 403):
        raise ValueError(f"Shisa AI authentication failed: {message}")
    if response.status_code == 429:
        raise ValueError(f"Shisa AI rate limit exceeded: {message}")
    raise ValueError(f"Shisa AI request failed ({response.status_code}): {message}")


def get_voice_catalog(credentials: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        response = httpx.get(
            f"{api_base(credentials)}/tts/voices",
            headers=headers(credentials),
            timeout=30.0,
        )
    except (httpx.ConnectError, httpx.TimeoutException) as error:
        raise ValueError(f"Could not connect to Shisa AI: {error}") from error
    raise_for_status(response)
    try:
        payload = response.json()
    except ValueError as error:
        raise ValueError("Shisa AI returned an invalid voice catalogue") from error

    if isinstance(payload, list):
        voices = payload
    elif isinstance(payload, dict):
        voices = payload.get("voices", payload.get("data", []))
    else:
        voices = []
    if not isinstance(voices, list):
        voices = []

    result = [voice for voice in voices if isinstance(voice, dict) and voice.get("id")]
    if not result:
        raise ValueError("Shisa AI returned an empty voice catalogue")
    return result


def voice_label(voice: dict[str, Any]) -> str:
    return str(
        voice.get("displayName")
        or voice.get("name")
        or voice.get("description")
        or voice.get("id")
        or "Unknown voice"
    )


def resolve_voice(voices: list[dict[str, Any]], query: str) -> dict[str, Any]:
    """Resolve a voice UUID or human-readable API name/description."""
    value = query.strip().casefold()
    if not value:
        raise ValueError("Voice name, description, or ID is required")

    for voice in voices:
        if str(voice.get("id", "")).casefold() == value:
            return voice

    label_fields = ("displayName", "name", "description")
    exact = [
        voice
        for voice in voices
        if any(str(voice.get(field, "")).strip().casefold() == value for field in label_fields)
    ]
    if len(exact) == 1:
        return exact[0]

    partial = [
        voice
        for voice in voices
        if any(value in str(voice.get(field, "")).casefold() for field in label_fields)
    ]
    if len(partial) == 1:
        return partial[0]
    if len(partial) > 1:
        matches = ", ".join(voice_label(voice) for voice in partial[:10])
        raise ValueError(f"Voice description is ambiguous; matching voices: {matches}")
    raise ValueError(f"Shisa AI voice not found: {query}")


def translate_text(
    credentials: dict[str, Any], text: str, source_lang: str, target_lang: str
) -> str:
    """Return a completed Shisa Translation response as plain text."""
    try:
        response = httpx.post(
            f"{api_base(credentials)}/translate/",
            headers=headers(credentials),
            files={
                "text": (None, text),
                "source_lang": (None, source_lang),
                "target_lang": (None, target_lang),
                "stream": (None, "false"),
            },
            timeout=300.0,
        )
    except (httpx.ConnectError, httpx.TimeoutException) as error:
        raise ValueError(f"Could not connect to Shisa AI: {error}") from error
    raise_for_status(response)
    try:
        payload = response.json()
        translation = payload["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as error:
        raise ValueError("Shisa AI returned an invalid translation response") from error
    if not isinstance(translation, str) or not translation.strip():
        raise ValueError("Shisa AI returned an empty translation")
    return translation


def transcribe_audio(
    credentials: dict[str, Any],
    audio: bytes,
    *,
    language: str | None = None,
    hotwords: list[str] | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    frequency_penalty: float | None = None,
    repetition_penalty: float | None = None,
    vad: int | None = None,
) -> dict[str, Any]:
    """Transcribe audio using only explicitly supplied optional ASR parameters."""
    import base64

    if not audio:
        raise ValueError("Audio file must not be empty")
    payload: dict[str, Any] = {
        "audio": base64.b64encode(audio).decode("ascii")
    }
    optional = {
        "language": language.strip() if language else None,
        "hotwords": hotwords or None,
        "temperature": temperature,
        "top_p": top_p,
        "frequency_penalty": frequency_penalty,
        "repetition_penalty": repetition_penalty,
        "vad": vad,
    }
    payload.update({key: value for key, value in optional.items() if value is not None})
    try:
        response = httpx.post(
            f"{api_base(credentials)}/asr/srt/audio_llm",
            headers=headers(credentials),
            json=payload,
            timeout=300.0,
        )
    except (httpx.ConnectError, httpx.TimeoutException) as error:
        raise ValueError(f"Could not connect to Shisa AI: {error}") from error
    raise_for_status(response)
    try:
        result = response.json()
    except ValueError as error:
        raise ValueError("Shisa AI returned an invalid ASR response") from error
    if not isinstance(result, dict) or not isinstance(result.get("text"), str):
        raise ValueError("Shisa AI returned an invalid ASR response")
    return result


def generate_speech(
    credentials: dict[str, Any], text: str, voice_id: str, audio_format: str
) -> bytes:
    try:
        response = httpx.post(
            f"{api_base(credentials)}/tts",
            headers=headers(credentials),
            json={
                "text": text,
                "voice_id": voice_id,
                "format": audio_format,
                "stream": False,
            },
            timeout=300.0,
        )
    except (httpx.ConnectError, httpx.TimeoutException) as error:
        raise ValueError(f"Could not connect to Shisa AI: {error}") from error
    raise_for_status(response)
    if not response.content:
        raise ValueError("Shisa AI returned no audio data")
    return response.content
