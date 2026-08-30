from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "synthetic_public_monitor"


def registry() -> dict:
    return json.loads((EXAMPLE / "registry.json").read_text(encoding="utf-8"))


def cloned_registry() -> dict:
    return copy.deepcopy(registry())
