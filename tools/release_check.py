#!/usr/bin/env python3
from __future__ import annotations

import compileall
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evidence_change_monitor.capture import capture_all
from evidence_change_monitor.config import load_registry
from evidence_change_monitor.integrity import verify_manifest
from evidence_change_monitor.storage import write_snapshot_set
from tools import check_docs, check_schema_parity, check_workflows, public_audit
from tools.generate_examples import check_generated



def main() -> int:
    if not all(
        compileall.compile_dir(ROOT / name, quiet=1)
        for name in ("src", "tools", "tests")
    ):
        raise SystemExit("Python compilation failed")

    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit("test suite failed")

    load_registry(ROOT / "examples/synthetic_public_monitor/registry.json", strict=True)
    check_generated()
    check_schema_parity.main()
    check_docs.main(ROOT)
    check_workflows.main(ROOT)
    public_audit.main(ROOT)

    registry = load_registry(ROOT / "examples/synthetic_public_monitor/registry.json", strict=True)
    snapshots = capture_all(
        registry,
        ROOT / "examples/synthetic_public_monitor/baseline",
        "2026-08-29T00:00:00Z",
    )
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / "capture"
        write_snapshot_set(target, snapshots)
        ok, errors = verify_manifest(target)
        if not ok:
            raise SystemExit("capture verification failed: " + "; ".join(errors))

    print("release gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
