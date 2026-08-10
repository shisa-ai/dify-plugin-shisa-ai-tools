#!/usr/bin/env python3
"""Automated Dify E2E harness for the Shisa AI Tools release.

Runs against a live Dify instance started by the CI job (GitHub runner):

  setup+login -> upload+install plugin pkg -> import workflow DSL
  -> publish + create API key -> /workflows/run -> assert outputs.

Environment:
  DIFY_BASE_URL        e.g. http://localhost
  DIFY_ADMIN_EMAIL     admin account created by Dify INIT_* env
  DIFY_ADMIN_PASSWORD
  PKG_PATH             path to the built .difypkg
  DSL_PATH             path to the verified workflow .yml
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import httpx

SPEECH_TEXT = "シーサ・エーアイの音声認識と音声合成をテストします。"
TRANSLATION_TEXT = "Shisa AIの音声ツールをテストします。"


def _env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"{name} is required")
    return value


def _wait(what: str, cond, timeout: float = 360.0, interval: float = 3.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if cond():
                return
        except Exception:
            pass
        time.sleep(interval)
    raise SystemExit(f"timeout waiting for {what}")


def _task_done(client: httpx.Client, headers: dict[str, str], task_id: str) -> bool:
    response = client.get(
        f"/console/api/workspaces/current/plugin/tasks/{task_id}", headers=headers
    )
    response.raise_for_status()
    task = response.json()
    status = task.get("status")
    if status == "success":
        return True
    if status == "failed":
        raise SystemExit(f"plugin install task failed: {json.dumps(task, ensure_ascii=False)[:800]}")
    return False


def _plugin_installed(client: httpx.Client, headers: dict[str, str], identifier: str) -> bool:
    response = client.get(
        "/console/api/workspaces/current/plugin/list", headers=headers
    )
    response.raise_for_status()
    payload = response.json()
    plugins = payload if isinstance(payload, list) else payload.get("plugins", [])
    return any(identifier in str(plugin) for plugin in plugins)


def main() -> int:
    base = _env("DIFY_BASE_URL").rstrip("/")
    email = _env("DIFY_ADMIN_EMAIL")
    password = _env("DIFY_ADMIN_PASSWORD")
    pkg = Path(_env("PKG_PATH"))
    dsl = Path(_env("DSL_PATH"))
    if not pkg.is_file():
        raise SystemExit(f"package not found: {pkg}")
    if not dsl.is_file():
        raise SystemExit(f"dsl not found: {dsl}")

    client = httpx.Client(base_url=base, timeout=120.0)
    _wait("Dify API to be reachable", lambda: client.get("/console/api/setup").status_code < 500)

    # Setup the initial admin account (idempotent) and log in.
    client.post(
        "/console/api/setup",
        json={"email": email, "name": "admin", "password": password},
    )
    login = client.post(
        "/console/api/login",
        json={"email": email, "password": password, "remember_me": True},
    )
    login.raise_for_status()
    token = login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload the plugin package and install it.
    with pkg.open("rb") as handle:
        upload = client.post(
            "/console/api/workspaces/current/plugin/upload/pkg",
            headers=headers,
            files={"pkg": (pkg.name, handle, "application/octet-stream")},
        )
    upload.raise_for_status()
    upload_payload = upload.json()
    identifiers = upload_payload.get("plugin_unique_identifiers") or [
        item.get("plugin_unique_identifier")
        for item in upload_payload.get("installations", [])
        if item.get("plugin_unique_identifier")
    ]
    if not identifiers:
        raise SystemExit(
            f"could not read plugin identifiers from upload: {json.dumps(upload_payload)[:400]}"
        )

    install = client.post(
        "/console/api/workspaces/current/plugin/install/pkg",
        headers=headers,
        json={"plugin_unique_identifiers": identifiers},
    )
    install.raise_for_status()
    task_id = install.json().get("task_id")
    if task_id:
        _wait("plugin install", lambda: _task_done(client, headers, task_id))
    else:
        _wait("plugin install", lambda: _plugin_installed(client, headers, identifiers[0]))

    # Import the verified workflow DSL.
    imported = client.post(
        "/console/api/apps/imports",
        headers=headers,
        json={
            "mode": "yaml-content",
            "yaml_content": dsl.read_text(encoding="utf-8"),
            "name": "Shisa Smoke E2E",
        },
    )
    if imported.status_code == 202:
        import_id = imported.json().get("id")
        _wait(
            "dsl import confirm",
            lambda: client.post(
                f"/console/api/apps/imports/{import_id}/confirm", headers=headers
            ).status_code
            in (200, 400),
        )
        imported = client.post(
            f"/console/api/apps/imports/{import_id}/confirm", headers=headers
        )
    imported.raise_for_status()
    app_id = imported.json().get("app_id")
    if not app_id:
        raise SystemExit(f"no app_id from import: {json.dumps(imported.json())[:400]}")

    # Publish API access and create a service API key.
    client.post(f"/console/api/apps/{app_id}/api-enable", headers=headers)
    key_response = client.post(f"/console/api/apps/{app_id}/api-keys", headers=headers)
    key_response.raise_for_status()
    api_key = key_response.json().get("api_key")
    if not api_key:
        raise SystemExit(f"no api_key from create: {json.dumps(key_response.json())[:400]}")

    # Run the workflow through the public service API.
    run = client.post(
        "/v1/workflows/run",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "inputs": {
                "speech_text": SPEECH_TEXT,
                "translation_text": TRANSLATION_TEXT,
            },
            "response_mode": "blocking",
            "user": "shisa-e2e",
        },
    )
    run.raise_for_status()
    data = run.json().get("data", {})
    if data.get("status") != "succeeded":
        raise SystemExit(f"workflow run failed: {json.dumps(data, ensure_ascii=False)[:800]}")

    outputs = data.get("outputs", {})
    asr_full = str(outputs.get("asr_full_text", ""))
    asr_defaults = str(outputs.get("asr_defaults_text", ""))
    translation = str(outputs.get("translation", ""))
    if not asr_full or "シサAI" in asr_full:
        raise SystemExit(f"bad full-parameter ASR output: {asr_full!r}")
    if not asr_defaults:
        raise SystemExit("empty API-defaults ASR output")
    if not translation:
        raise SystemExit("empty translation output")

    report = {
        "status": "succeeded",
        "workflow_run_id": data.get("id"),
        "voice_count": outputs.get("voice_count"),
        "asr_full_text": asr_full,
        "asr_defaults_text": asr_defaults,
        "translation": translation,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"dify e2e failed: {error}", file=sys.stderr)
        raise SystemExit(1)
