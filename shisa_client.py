from typing import Any

import httpx


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
