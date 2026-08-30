#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

TEXT_SUFFIXES = {".py", ".md", ".json", ".yml", ".yaml", ".toml", ".txt", ".csv", ".html", ".xml", ".cff"}
SKIP_PARTS = {".git", "build", "dist", "__pycache__"}

PATTERNS = {
    "private-key": re.compile("BEGIN " + "PRIVATE KEY"),
    "github-token": re.compile("gh" + "p_[A-Za-z0-9]{30,}"),
    "aws-access-key": re.compile("AK" + "IA[0-9A-Z]{16}"),
    "slack-webhook": re.compile("hooks\\.slack\\.com/services/"),
    "feishu-webhook": re.compile("open\\.feishu\\.cn/open-apis/bot/v2/hook/"),
    "personal-email": re.compile(r"\b[A-Za-z0-9._%+-]+@(?!example\.invalid\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "windows-user-path": re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+"),
    "mac-user-path": re.compile("/" + "Users" + "/" + r"[^/\s]+"),
    "china-mobile": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "private-ip": re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"),
}


def main(root_value: str | Path | None = None) -> int:
    root = Path(root_value if root_value is not None else (sys.argv[1] if len(sys.argv) > 1 else ".")).resolve()
    errors: list[str] = []
    scanned = 0
    for forbidden in (".bootstrap", ".payload", ".drf-bootstrap"):
        if any(path.is_dir() for path in root.rglob(forbidden)):
            errors.append(f"forbidden transport directory: {forbidden}")
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink() or any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"LICENSE", "AGENTS.md"}:
            continue
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        for name, pattern in PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{path.relative_to(root)}: matched {name}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"public audit passed: {scanned} text file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
