#!/usr/bin/env python3
"""Generate a deterministic CycloneDX JSON SBOM from uv.lock."""

from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import tomllib
from uuid import NAMESPACE_URL, uuid5

parser = ArgumentParser()
parser.add_argument("--output", default="dist/sbom.cdx.json")
args = parser.parse_args()
lock_path = Path("uv.lock")
raw = lock_path.read_bytes()
lock = tomllib.loads(raw.decode("utf-8"))
packages = lock.get("package", [])
components = []
dependencies = []

for package in sorted(packages, key=lambda value: (value["name"], value["version"])):
    name = package["name"]
    version = package["version"]
    ref = f"pkg:pypi/{name}@{version}"
    hashes = []
    artifacts = []
    if package.get("sdist"):
        artifacts.append(package["sdist"])
    artifacts.extend(package.get("wheels", []))
    for artifact in artifacts:
        value = artifact.get("hash", "")
        if value.startswith("sha256:"):
            digest = value.split(":", 1)[1].upper()
            if digest not in {entry["content"] for entry in hashes}:
                hashes.append({"alg": "SHA-256", "content": digest})
    component = {
        "type": "library",
        "bom-ref": ref,
        "name": name,
        "version": version,
        "purl": ref,
    }
    if hashes:
        component["hashes"] = sorted(hashes, key=lambda value: value["content"])
    components.append(component)
    children = []
    for dependency in package.get("dependencies", []):
        dep_name = dependency["name"] if isinstance(dependency, dict) else dependency
        matches = [item for item in packages if item["name"] == dep_name]
        if matches:
            children.append(f"pkg:pypi/{dep_name}@{matches[0]['version']}")
    dependencies.append({"ref": ref, "dependsOn": sorted(set(children))})

bom = {
    "bomFormat": "CycloneDX",
    "specVersion": "1.5",
    "serialNumber": f"urn:uuid:{uuid5(NAMESPACE_URL, sha256(raw).hexdigest())}",
    "version": 1,
    "metadata": {"component": {"type": "application", "name": "Shisa AI Dify Tools plugin"}},
    "components": components,
    "dependencies": dependencies,
}
output = Path(args.output)
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(bom, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {output} with {len(components)} components")
