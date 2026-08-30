#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def main(root_value: str | Path | None = None) -> int:
    root = Path(root_value if root_value is not None else (sys.argv[1] if len(sys.argv) > 1 else ".")).resolve()
    errors: list[str] = []
    count = 0
    for path in sorted(root.rglob("*.md")):
        if any(part in {".git", "build", "dist"} for part in path.parts):
            continue
        count += 1
        text = path.read_text(encoding="utf-8")
        if not text.endswith("\n"):
            errors.append(f"{path.relative_to(root)}: missing final newline")
        for target in LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            clean = target.split("#", 1)[0]
            if not clean:
                continue
            destination = (path.parent / clean).resolve()
            try:
                destination.relative_to(root)
            except ValueError:
                errors.append(f"{path.relative_to(root)}: link escapes repository: {target}")
                continue
            if not destination.exists():
                errors.append(f"{path.relative_to(root)}: missing link target: {target}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"documentation check passed: {count} Markdown file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
