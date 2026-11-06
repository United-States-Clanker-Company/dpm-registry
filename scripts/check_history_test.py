#!/usr/bin/env python3

import pathlib
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).with_name("check_history.py")
MANIFEST = """schema = 1
name = "tool"
version = "1.0.0"
dependencies = []
yanked = false

[[artifacts]]
os = "darwin"
arch = "arm64"
url = "https://example.com/tool-1.0.0.tar.gz"
sha256 = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

[install]
bins = ["tool"]
"""


class HistoryPolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp)
        subprocess.run(["git", "init", "-q"], cwd=self.temp, check=True)
        path = self.temp / "packages/tool/versions/1.0.0/dpm.toml"
        path.parent.mkdir(parents=True)
        path.write_text(MANIFEST)
        subprocess.run(["git", "add", "."], cwd=self.temp, check=True)
        subprocess.run(
            ["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", "commit", "-q", "-m", "base"],
            cwd=self.temp,
            check=True,
        )

    def check(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run([str(SCRIPT), "HEAD"], cwd=self.temp, text=True, capture_output=True)

    def manifest(self) -> pathlib.Path:
        return self.temp / "packages/tool/versions/1.0.0/dpm.toml"

    def test_unchanged_version_is_allowed(self) -> None:
        self.assertEqual(self.check().returncode, 0)

    def test_yank_with_reason_is_allowed(self) -> None:
        self.manifest().write_text(MANIFEST.replace("yanked = false", 'yanked = true\nyank_reason = "security issue"'))
        self.assertEqual(self.check().returncode, 0)

    def test_rewrite_is_rejected(self) -> None:
        self.manifest().write_text(MANIFEST.replace("a" * 64, "b" * 64))
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("published version rewritten", result.stderr)

    def test_deletion_is_rejected(self) -> None:
        self.manifest().unlink()
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("published version deleted", result.stderr)


if __name__ == "__main__":
    unittest.main()
