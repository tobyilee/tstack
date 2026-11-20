"""GitHub에서 설치하는 테스트. Spec 01의 AC-1.8. ADR-0004의 규칙 10.

환경 변수 `TSTACK_REMOTE`가 `1`일 때만 돈다. push의 전에는 GitHub에 그 커밋이 없다.
이 테스트만 "설치한 사본"을 본다. 로컬 경로의 설치는 복사하지 않는다.
"""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import claude_cli
import support

ROOT = support.ROOT
REPOSITORY = "tobyilee/tstack"
PLUGINS = ("tstack", "explain-diff")


def tracked_files(plugin):
    listed = subprocess.run(["git", "ls-files", "plugins/%s" % plugin], cwd=str(ROOT), capture_output=True, text=True).stdout
    prefix = "plugins/%s/" % plugin
    return sorted(line[len(prefix):] for line in listed.splitlines())


def copied_files(config, plugin):
    """설치한 사본의 파일의 목록. CLI가 만드는 표지의 파일(`.in_use`)은 뺀다."""
    home = Path(config) / "plugins" / "cache" / "tstack" / plugin
    versions = sorted(d for d in home.iterdir() if d.is_dir()) if home.is_dir() else []
    if len(versions) != 1:
        return None
    return sorted(p.relative_to(versions[0]).as_posix() for p in versions[0].rglob("*") if p.is_file() and p.name != ".in_use")


class RemoteInstall(unittest.TestCase):
    def setUp(self):
        if not support.remote_enabled(os.environ):
            self.skipTest("TSTACK_REMOTE가 1이 아니다. GitHub에서 설치하는 테스트는 push의 뒤에 돈다 (ADR-0004 규칙 10)")
        claude_cli.require_cli(self)

    def test_ac1_8_github_marketplace_installs_both_plugins(self):
        with tempfile.TemporaryDirectory() as config:
            added = claude_cli.run_claude(["plugin", "marketplace", "add", REPOSITORY], config)
            self.assertEqual(0, added.returncode, "AC-1.8: GitHub의 %s를 마켓플레이스로 등록해야 한다:\n%s" % (REPOSITORY, (added.stdout + added.stderr)[-600:]))
            for name in PLUGINS:
                done = claude_cli.run_claude(["plugin", "install", "%s@tstack" % name], config)
                self.assertEqual(0, done.returncode, "AC-1.8: %s@tstack의 설치가 성공해야 한다:\n%s" % (name, (done.stdout + done.stderr)[-600:]))
                self.assertEqual(
                    tracked_files(name), copied_files(config, name),
                    "AC-1.8: 설치한 사본의 파일의 목록이 plugins/%s의 git ls-files와 같아야 한다" % name,
                )


if __name__ == "__main__":
    unittest.main()
