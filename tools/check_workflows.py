#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

USES = re.compile(r"(?m)^\s*(?:-\s*)?uses:\s*[^#\s]+@([^\s#]+)")


def main(root_value: str | Path | None = None) -> int:
    root = Path(root_value if root_value is not None else (sys.argv[1] if len(sys.argv) > 1 else ".")).resolve()
    workflow_dir = root / ".github" / "workflows"
    workflows = sorted([*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")])
    if {path.name for path in workflows} != {"ci.yml", "release.yml"}:
        raise SystemExit(f"unexpected workflow set: {[path.name for path in workflows]}")
    errors: list[str] = []
    for path in workflows:
        text = path.read_text(encoding="utf-8")
        if "permissions:" not in text:
            errors.append(f"{path.name}: missing explicit permissions")
        for reference in USES.findall(text):
            if not re.fullmatch(r"[0-9a-f]{40}", reference):
                errors.append(f"{path.name}: action is not pinned to a full SHA: {reference}")
        if re.search(r"curl\s+[^|\n]+\|\s*(?:sh|bash)", text, re.IGNORECASE):
            errors.append(f"{path.name}: curl-pipe-shell is prohibited")
        # Validate each multiline shell block with bash -n. This is intentionally
        # a narrow YAML block extractor for repository-owned workflows.
        lines = text.splitlines()
        index = 0
        while index < len(lines):
            match = re.match(r"^(\s*)run:\s*\|\s*$", lines[index])
            if not match:
                index += 1
                continue
            indent = len(match.group(1))
            block: list[str] = []
            index += 1
            while index < len(lines):
                line = lines[index]
                if line.strip() and len(line) - len(line.lstrip()) <= indent:
                    break
                block.append(line[indent + 2 :] if len(line) >= indent + 2 else "")
                index += 1
            script = "\n".join(block) + "\n"
            with tempfile.NamedTemporaryFile("w", suffix=".sh", encoding="utf-8") as handle:
                handle.write(script)
                handle.flush()
                result = subprocess.run(["bash", "-n", handle.name], text=True, capture_output=True)
            if result.returncode:
                errors.append(f"{path.name}: invalid embedded shell: {result.stderr.strip()}")
    release = (workflow_dir / "release.yml").read_text(encoding="utf-8")
    for token in ("release/v*", "Confirm candidate equals current main", "pyproject.toml", "RELEASE_PROVENANCE.json"):
        if token not in release:
            errors.append(f"release.yml: missing {token!r}")
    if "release/v0.1.0" in release:
        errors.append("release.yml: release branch must be version-driven")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"workflow check passed: {len(workflows)} workflow(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
