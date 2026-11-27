"""Check vendored files against the pinned manifest. No network access."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def verify_manifest(root: Path, manifest_path: Path) -> list[str]:
    if not manifest_path.is_file():
        return ["manifest missing"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["manifest is not valid JSON"]

    errors: list[str] = []
    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        return ["manifest sources missing"]

    for source in sources:
        name = source.get("name", "<unnamed>")
        commit = source.get("commit", "")
        if not isinstance(commit, str) or len(commit) != 40:
            errors.append(f"{name} commit is not a 40-character SHA")
        license_path = root / source.get("license_path", "")
        if not license_path.is_file():
            errors.append(f"{name} license file missing")
        else:
            license_text = license_path.read_text(encoding="utf-8")
            if "MIT License" not in license_text or "Copyright" not in license_text:
                errors.append(f"{name} license is not the expected MIT notice")
        for item in source.get("files", []):
            vendor = root / item["vendor_path"]
            if not vendor.is_file():
                errors.append(f"missing vendored file: {item['vendor_path']}")
                continue
            blob = vendor.read_bytes()
            digest = hashlib.sha256(blob).hexdigest()
            if digest != item.get("sha256"):
                errors.append(f"sha256 mismatch: {item['vendor_path']}")
            git_blob = hashlib.sha1(f"blob {len(blob)}\0".encode() + blob).hexdigest()
            if git_blob != item.get("git_blob_sha1"):
                errors.append(f"git blob mismatch: {item['vendor_path']}")
    return errors
