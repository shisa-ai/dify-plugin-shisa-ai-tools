#!/usr/bin/env python3
"""Validate a Dify plugin package before publication."""

from __future__ import annotations

import argparse
import json
import re
import tomllib
import zipfile
from pathlib import Path, PurePosixPath

import yaml

FORBIDDEN_PARTS = {
    ".git",
    ".github",
    ".venv",
    "artifacts",
    "dist",
    "docs",
    "scripts",
    "tests",
}
FORBIDDEN_NAMES = {".env", ".dev.vars", "uv.lock"}
REQUIRED_NAMES = {
    "LICENSE",
    "README.md",
    "SBOM.cdx.json",
    "manifest.yaml",
    "main.py",
    "requirements.txt",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    args = parser.parse_args()

    package = args.package
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]
    source_manifest = yaml.safe_load(Path("manifest.yaml").read_text(encoding="utf-8"))

    if package.suffix != ".difypkg" or not package.is_file():
        raise SystemExit(f"not a .difypkg file: {package}")

    with zipfile.ZipFile(package) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise SystemExit(f"corrupt archive member: {bad_member}")

        names = set(archive.namelist())
        missing = REQUIRED_NAMES - names
        if missing:
            raise SystemExit(f"missing required package files: {sorted(missing)}")

        for raw_name in names:
            path = PurePosixPath(raw_name)
            if path.is_absolute() or ".." in path.parts:
                raise SystemExit(f"unsafe package path: {raw_name}")
            if FORBIDDEN_PARTS.intersection(path.parts) or path.name in FORBIDDEN_NAMES:
                raise SystemExit(f"forbidden package member: {raw_name}")

        packaged_manifest = yaml.safe_load(archive.read("manifest.yaml"))
        if packaged_manifest["version"] != project["version"]:
            raise SystemExit("packaged manifest and project versions differ")
        if packaged_manifest != source_manifest:
            raise SystemExit("packaged manifest differs from source manifest")

        sbom = json.loads(archive.read("SBOM.cdx.json"))
        if sbom.get("bomFormat") != "CycloneDX":
            raise SystemExit("embedded SBOM is not CycloneDX")
        sbom_component = sbom.get("metadata", {}).get("component", {})
        if sbom_component.get("name") != project["name"] or sbom_component.get("version") != project["version"]:
            raise SystemExit("embedded SBOM does not describe this plugin version")

        requirements = archive.read("requirements.txt").decode("utf-8")
        requirement_starts = [
            line for line in requirements.splitlines() if line and not line[0].isspace()
        ]
        if not requirement_starts:
            raise SystemExit("requirements.txt is empty")
        for line in requirement_starts:
            entry = line.removesuffix("\\").rstrip()
            requirement = entry.split(" ; ", 1)[0]
            if not re.fullmatch(r"[A-Za-z0-9_.-]+==[^\s;]+", requirement):
                raise SystemExit(f"runtime requirement is not pinned: {line}")
        if "--hash=sha256:" not in requirements:
            raise SystemExit("requirements.txt does not contain hashes")

    print(f"validated {package} ({package.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
