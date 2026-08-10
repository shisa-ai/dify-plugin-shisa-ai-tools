#!/usr/bin/env python3
"""Automated Dify E2E harness for the Shisa AI Tools release.

Runs against a live Dify instance started by the CI job (GitHub runner):

  setup+login -> upload+install plugin pkg -> import workflow DSL
  -> publish + create API key -> /workflows/run -> assert outputs.

Environment:
  DIFY_BASE_URL        e.g. http://localhost
  DIFY_ADMIN_EMAIL     admin account email
  DIFY_ADMIN_PASSWORD  admin password (plaintext for /setup, Base64 for /login)
  DIFY_INIT_PASSWORD   optional; the INIT_PASSWORD gate for self-hosted Dify
  SHISA_API_KEY        Shisa AI API key used to configure the Tools plugin credentials
  PKG_PATH             path to the built .difypkg
  DSL_PATH             path to the verified workflow .yml
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
from pathlib import Path

import httpx


def _load_env_file(path: str = ".env.e2e") -> None:
    """Load credentials from a local env file into os.environ without
    overriding variables that are already set (e.g. GitHub Actions env)."""
    env_file = Path(path)
    if not env_file.is_file():
        return
    for raw in env_file.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file()

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

    password_b64 = base64.b64encode(password.encode("utf-8")).decode("ascii")
    init_password = os.environ.get("DIFY_INIT_PASSWORD", "").strip() or password

    # Self-hosted Dify gates setup with an INIT_PASSWORD (plaintext).
    init_status = client.get("/console/api/init").json()
    if init_status.get("status") == "not_started":
        init = client.post(
            "/console/api/init",
            json={"password": init_password},
        )
        if init.status_code >= 400 and init.status_code != 409:
            init.raise_for_status()

    # /setup stores the password as-is (plaintext); /login Base64-encodes it.
    setup_status = client.get("/console/api/setup").json()
    if setup_status.get("step") == "not_started":
        setup = client.post(
            "/console/api/setup",
            json={"email": email, "name": "admin", "password": password},
        )
        if setup.status_code >= 400 and setup.status_code != 409:
            setup.raise_for_status()

    login = client.post(
        "/console/api/login",
        json={"email": email, "password": password_b64, "remember_me": True},
    )
    if login.status_code != 200:
        raise SystemExit(f"login failed ({login.status_code}): {login.text[:300]}")

    # Console session is cookie-based; subsequent requests need the CSRF token.
    csrf = client.cookies.get("csrf_token")
    if not csrf:
        raise SystemExit("no csrf_token cookie after login")
    headers = {
        "X-CSRF-Token": csrf,
    }

    # Upload the plugin package and install it (skip if already installed).
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
    single = upload_payload.get("unique_identifier")
    if single:
        identifiers = [single]
    if not identifiers:
        raise SystemExit(
            f"could not read plugin identifiers from upload: {json.dumps(upload_payload)[:400]}"
        )

    if not _plugin_installed(client, headers, identifiers[0]):
        install = client.post(
            "/console/api/workspaces/current/plugin/install/pkg",
            headers=headers,
            json={"plugin_unique_identifiers": identifiers},
        )
        install.raise_for_status()
        install_payload = install.json()
        if not install_payload.get("all_installed"):
            # Some Dify versions return an async task; some install synchronously.
            # Wait on the plugin list rather than the task status, which is not
            # consistently populated across versions.
            _wait("plugin install", lambda: _plugin_installed(client, headers, identifiers[0]))

    # Structural mode (fork PRs, no secrets): verify install + DSL import +
    # publish. Real-API credential validation and the workflow run are skipped.
    structural = os.environ.get("STRUCTURAL", "").strip().lower() in ("1", "true", "yes")
    shisa_key = os.environ.get("SHISA_API_KEY", "").strip()
    if not shisa_key and not structural:
        raise SystemExit("SHISA_API_KEY is required to configure tool provider credentials")

    if not structural:
        tool_provider = f"{identifiers[0].split('@')[0].split(':')[0]}/{identifiers[0].split('/')[-1].split(':')[0]}"
        creds = client.post(
            f"/console/api/workspaces/current/tool-provider/builtin/{tool_provider}/add",
            headers=headers,
            json={
                "credentials": {
                    "api_key": shisa_key,
                    "api_base": "https://api.shisa.ai",
                },
                "name": "release-e2e",
                "type": "api-key",
            },
        )
        if creds.status_code >= 400 and creds.status_code != 409 and "already used" not in creds.text and "already exists" not in creds.text:
            creds.raise_for_status()

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

    # Publish the imported workflow so the service API can run it.
    publish = client.post(
        f"/console/api/apps/{app_id}/workflows/publish",
        headers=headers,
        json={"marked_name": "release-smoke", "marked_comment": "automated release e2e"},
    )
    if publish.status_code >= 400 and publish.status_code != 409:
        publish.raise_for_status()

    if structural:
        print(
            json.dumps(
                {
                    "status": "succeeded-structural",
                    "app_id": app_id,
                    "note": "install + DSL import + publish verified; real-API run skipped (fork PR, no secret)",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    # Publish API access and create a service API key.
    client.post(f"/console/api/apps/{app_id}/api-enable", headers=headers)
    key_response = client.post(f"/console/api/apps/{app_id}/api-keys", headers=headers)
    key_response.raise_for_status()
    api_key = key_response.json().get("api_key") or key_response.json().get("token")
    if not api_key:
        raise SystemExit(f"no api key from create: {json.dumps(key_response.json())[:400]}")

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
