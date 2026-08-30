from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import EXAMPLE, ROOT


class CliTests(unittest.TestCase):
    def _run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        return subprocess.run(
            [sys.executable, "-m", "evidence_change_monitor", *args],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=check,
        )

    def test_version(self) -> None:
        result = self._run("--version")
        self.assertEqual(result.stdout.strip(), "0.1.0")

    def test_validate_registry(self) -> None:
        result = self._run("validate", str(EXAMPLE / "registry.json"), "--strict")
        self.assertTrue(json.loads(result.stdout)["ok"])

    def test_init_creates_starter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "monitor"
            self._run("init", str(target))
            self.assertTrue((target / "registry.json").is_file())
            self.assertTrue((target / "inputs" / "notice.txt").is_file())

    def test_capture_and_verify(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "capture"
            self._run(
                "capture",
                "--registry", str(EXAMPLE / "registry.json"),
                "--input-dir", str(EXAMPLE / "baseline"),
                "--output-dir", str(output),
                "--as-of", "2026-08-29T00:00:00Z",
            )
            result = self._run("verify", str(output))
            self.assertTrue(json.loads(result.stdout)["ok"])

    def test_run_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            self._run(
                "run",
                "--registry", str(EXAMPLE / "registry.json"),
                "--input-dir", str(EXAMPLE / "baseline"),
                "--state-dir", str(base / "state"),
                "--output-dir", str(base / "baseline"),
                "--as-of", "2026-08-29T00:00:00Z",
                "--commit-state",
            )
            self._run(
                "run",
                "--registry", str(EXAMPLE / "registry.json"),
                "--input-dir", str(EXAMPLE / "current"),
                "--state-dir", str(base / "state"),
                "--output-dir", str(base / "current"),
                "--as-of", "2026-08-30T08:00:00Z",
                "--commit-state",
            )
            output = base / "rerendered.html"
            self._run(
                "report",
                str(base / "current" / "run.json"),
                "--format", "html",
                "--output", str(output),
            )
            self.assertIn("Evidence Change Report", output.read_text(encoding="utf-8"))


class PublicationTests(unittest.TestCase):
    def test_generated_example_is_current(self) -> None:
        subprocess.run(
            [sys.executable, "tools/generate_examples.py", "--check"],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            check=True,
        )

    def test_generated_example_manifest_verifies(self) -> None:
        from evidence_change_monitor.integrity import verify_manifest

        ok, errors = verify_manifest(EXAMPLE / "generated")
        self.assertTrue(ok, errors)

    def test_schema_parity(self) -> None:
        subprocess.run(
            [sys.executable, "tools/check_schema_parity.py"],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            check=True,
        )

    def test_docs_check(self) -> None:
        subprocess.run([sys.executable, "tools/check_docs.py", "."], cwd=ROOT, check=True)

    def test_workflow_check(self) -> None:
        subprocess.run([sys.executable, "tools/check_workflows.py", "."], cwd=ROOT, check=True)

    def test_public_audit_passes_repository(self) -> None:
        subprocess.run([sys.executable, "tools/public_audit.py", "."], cwd=ROOT, check=True)

    def test_release_workflow_is_version_driven(self) -> None:
        text = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        self.assertIn("release/v*", text)
        self.assertIn("pyproject.toml", text)
        self.assertIn("Confirm candidate equals current main", text)
        self.assertIn("RELEASE_PROVENANCE.json", text)
        self.assertNotIn("release/v0.1.0", text)


if __name__ == "__main__":
    unittest.main()
