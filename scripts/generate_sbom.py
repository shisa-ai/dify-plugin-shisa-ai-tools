#!/usr/bin/env python3
"""Generate a deterministic CycloneDX JSON SBOM for runtime dependencies."""

from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import tomllib
from uuid import NAMESPACE_URL, uuid5

parser = ArgumentParser()
parser.add_argument("--output", default="dist/sbom.cdx.json")
args = parser.parse_args()

lock = tomllib.loads(Path("uv.lock").read_text(encoding="utf-8"))
project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]
packages = lock.get("package", [])
by_name = {package["name"]: package for package in packages}
root = next((package for package in packages if package.get("source", {}).get("virtual") == "."), None)
if root is None:
    raise SystemExit("uv.lock does not contain the project root")

# Follow only the root's production dependency graph. Development tooling must
# not appear in the SBOM attached to the installable Dify package.
pending = [dependency["name"] for dependency in root.get("dependencies", [])]
runtime_names: set[str] = set()
while pending:
    name = pending.pop()
    if name in runtime_names:
        continue
    package = by_name.get(name)
    if package is None:
        raise SystemExit(f"locked runtime dependency is missing: {name}")
    runtime_names.add(name)
    pending.extend(
        dependency["name"] if isinstance(dependency, dict) else dependency
        for dependency in package.get("dependencies", [])
    )

runtime_packages = sorted(
    (by_name[name] for name in runtime_names),
    key=lambda value: (value["name"], value["version"]),
)
components = []
dependencies = []
for package in runtime_packages:
    name = package["name"]
    version = package["version"]
    ref = f"pkg:pypi/{name}@{version}"
    hashes = []
    artifacts = ([package["sdist"]] if package.get("sdist") else []) + package.get("wheels", [])
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
        if dep_name in runtime_names:
            child = by_name[dep_name]
            children.append(f"pkg:pypi/{dep_name}@{child['version']}")
    dependencies.append({"ref": ref, "dependsOn": sorted(set(children))})

root_ref = f"pkg:pypi/{project['name']}@{project['version']}"
root_dependencies = [
    f"pkg:pypi/{name}@{by_name[name]['version']}"
    for name in sorted(dependency["name"] for dependency in root.get("dependencies", []))
]
dependencies.insert(0, {"ref": root_ref, "dependsOn": root_dependencies})
canonical = json.dumps({"components": components, "dependencies": dependencies}, sort_keys=True)
bom = {
    "bomFormat": "CycloneDX",
    "specVersion": "1.5",
    "serialNumber": f"urn:uuid:{uuid5(NAMESPACE_URL, sha256(canonical.encode()).hexdigest())}",
    "version": 1,
    "metadata": {
        "component": {
            "type": "application",
            "bom-ref": root_ref,
            "name": project["name"],
            "version": project["version"],
            "purl": root_ref,
        }
    },
    "components": components,
    "dependencies": dependencies,
}
output = Path(args.output)
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(bom, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {output} with {len(components)} runtime components")
