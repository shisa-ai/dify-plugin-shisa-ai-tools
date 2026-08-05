#!/usr/bin/env python3
"""Fail CI on mutable or high-risk GitHub Actions workflow patterns."""

from pathlib import Path
import re
import sys

SHA_ACTION = re.compile(r"^\s*-?\s*uses:\s*[^\s@]+@[0-9a-f]{40}(?:\s+#.*)?$")
errors: list[str] = []

for path in sorted(Path(".github/workflows").glob("*.y*ml")):
    text = path.read_text(encoding="utf-8")
    for forbidden in ("pull_request_target:", "workflow_run:"):
        if forbidden in text:
            errors.append(f"{path}: forbidden trigger {forbidden[:-1]}")
    for number, line in enumerate(text.splitlines(), 1):
        if "uses:" in line and not SHA_ACTION.match(line):
            errors.append(f"{path}:{number}: action is not pinned to a full commit SHA")
    if path.name == "release.yml":
        for forbidden in ("pull_request:", "workflow_dispatch:", "schedule:"):
            if forbidden in text:
                errors.append(f"{path}: release workflow must be tag-only ({forbidden[:-1]} found)")
        for required in ('tags:', 'environment: release', 'DIFY_CLI_SHA256:', 'attest-build-provenance@'):
            if required not in text:
                errors.append(f"{path}: missing release control {required}")

if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)
print("GitHub Actions workflow policy passed")
