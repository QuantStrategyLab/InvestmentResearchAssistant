"""Obvious secret and private-path checks.

A clean result is not evidence that the tree has no personal data, no
prompt injection, or no credential a scanner does not recognize.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

_PATTERNS = (
    ("aws_access_key_id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("github_pat", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
)

_PRIVATE_MARKERS = (
    "watchlists/",
    "holdings/",
    "decision-logs/",
    "preferences/",
)


def find_obvious_secrets(text: str) -> list[str]:
    return [name for name, pattern in _PATTERNS if pattern.search(text)]


def private_path_findings(relative_paths: list[str]) -> list[str]:
    findings: list[str] = []
    for relative in relative_paths:
        normalized = relative.replace("\\", "/")
        if normalized.startswith("./"):
            normalized = normalized[2:]
        name = Path(normalized).name
        if name == ".env" or normalized == ".env" or name.endswith(".pem") or name.endswith(".key"):
            findings.append(f"private path: {relative}")
            continue
        if any(marker in f"{normalized}/" or normalized.startswith(marker) for marker in _PRIVATE_MARKERS):
            findings.append(f"private path: {relative}")
    return findings


def scan_tracked_text(root: Path) -> list[str]:
    """Scan git-tracked files plus non-ignored untracked files.

    Ignored paths are not scanned. That is a limitation, not a guarantee.
    """
    tracked = _git_lines(root, ["git", "ls-files", "-z"])
    untracked = _git_lines(root, ["git", "ls-files", "-z", "--others", "--exclude-standard"])
    relative_paths = tracked + untracked
    findings = private_path_findings(relative_paths)
    for relative in relative_paths:
        path = root / relative
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(f"undecoded file: {relative}")
            continue
        for name in find_obvious_secrets(text):
            findings.append(f"{relative}: {name}")
    return findings


def _git_lines(root: Path, command: list[str]) -> list[str]:
    result = subprocess.run(command, cwd=root, check=True, capture_output=True)
    raw = result.stdout.decode("utf-8")
    return [line for line in raw.split("\0") if line]
