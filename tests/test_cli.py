"""실제의 CLI를 부르는 검사. Spec 01의 AC-1.4, AC-1.5, AC-1.10. ADR-0004의 규칙 1, 4, 6, 7.

CLI는 격리된 설정 폴더에서만 돈다 (`claude_cli.run_claude`). 사용자의 설정 폴더는 바뀌지 않는다.
CLI가 없으면 테스트를 건너뛴다. CI에서는 건너뛰지 않고 실패한다 (ADR-0004 규칙 7).
"""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import claude_cli
import support

ROOT = support.ROOT
PLUGINS = ("tstack", "explain-diff")


def user_plugin_files():
    """사용자의 설정 폴더의 플러그인의 기록의 해시. 검사의 전과 후를 비교한다."""
    folder = Path.home() / ".claude" / "plugins"
    names = ("known_marketplaces.json", "installed_plugins.json")
    return {name: hashlib.sha256((folder / name).read_bytes()).hexdigest() for name in names if (folder / name).is_file()}


class Validate(unittest.TestCase):
    def setUp(self):
        claude_cli.require_cli(self)

    def validate(self, target):
        with tempfile.TemporaryDirectory() as config:
            return claude_cli.run_claude(["plugin", "validate", "--strict", str(target)], config)

    def test_ac1_4_strict_validation_passes_at_the_repository_root(self):
        result = self.validate(ROOT)
        self.assertEqual(0, result.returncode, "AC-1.4: validate --strict가 저장소의 뿌리에서 통과해야 한다:\n%s" % (result.stdout + result.stderr)[-600:])

    def test_ac1_5_strict_validation_passes_for_each_plugin_folder(self):
        for name in PLUGINS:
            result = self.validate(ROOT / "plugins" / name)
            self.assertEqual(0, result.returncode, "AC-1.5: validate --strict가 plugins/%s에서 통과해야 한다:\n%s" % (name, (result.stdout + result.stderr)[-600:]))
            self.assertIn("%s:" % name, result.stdout, "AC-1.5: validate가 플러그인 %s의 부품을 말해야 한다" % name)


class LocalInstall(unittest.TestCase):
    """작업 사본의 경로를 마켓플레이스로 등록하고 플러그인 2개를 설치한다. 한 번만 한다."""

    @classmethod
    def setUpClass(cls):
        cls.results = None
        if not claude_cli.available():
            return
        cls.before = user_plugin_files()
        with tempfile.TemporaryDirectory() as config:
            cls.results = {"add": claude_cli.run_claude(["plugin", "marketplace", "add", str(ROOT)], config)}
            for name in PLUGINS:
                cls.results[name] = claude_cli.run_claude(["plugin", "install", "%s@tstack" % name], config)
            cls.results["list"] = claude_cli.run_claude(["plugin", "list"], config)
        cls.after = user_plugin_files()

    def setUp(self):
        claude_cli.require_cli(self)

    def test_ac1_10_local_marketplace_installs_both_plugins(self):
        for step in ("add",) + PLUGINS:
            result = self.results[step]
            self.assertEqual(0, result.returncode, "AC-1.10: 로컬 경로의 마켓플레이스에서 '%s'가 성공해야 한다:\n%s" % (step, (result.stdout + result.stderr)[-600:]))
        listed = self.results["list"].stdout
        for name in PLUGINS:
            self.assertIn("%s@tstack" % name, listed, "AC-1.10: 설치한 뒤의 목록에 %s@tstack이 있어야 한다" % name)

    def test_adr0004_6_install_does_not_touch_the_user_config_folder(self):
        self.assertEqual(self.before, self.after, "ADR-0004 규칙 6: 검사의 뒤에 사용자의 설정 폴더의 플러그인의 기록이 바뀌었다")


class MissingCli(unittest.TestCase):
    def test_adr0004_7_missing_cli_fails_in_ci_and_skips_elsewhere(self):
        self.assertEqual("fail", claude_cli.missing_cli_action({"CI": "true"}), "ADR-0004 규칙 7: CI에서는 건너뛰지 않고 실패한다")
        for env in ({}, {"CI": "false"}, {"CI": ""}):
            self.assertEqual("skip", claude_cli.missing_cli_action(env), "ADR-0004 규칙 7: CI가 아니면 건너뛴다: %r" % (env,))

    def test_adr0004_7_require_cli_raises_the_right_exception(self):
        with mock.patch.object(claude_cli, "available", return_value=False):
            with mock.patch.dict("os.environ", {"CI": "true"}):
                with self.assertRaises(AssertionError, msg="ADR-0004 규칙 7: CI에서 CLI가 없으면 테스트가 실패해야 한다") as caught:
                    claude_cli.require_cli(self)
                self.assertIn("ADR-0004 규칙 7", str(caught.exception))
            with mock.patch.dict("os.environ", {"CI": ""}):
                with self.assertRaises(unittest.SkipTest, msg="ADR-0004 규칙 7: CI가 아니면 테스트를 건너뛰어야 한다"):
                    claude_cli.require_cli(self)
        with mock.patch.object(claude_cli, "available", return_value=True):
            self.assertIsNone(claude_cli.require_cli(self), "ADR-0004 규칙 7: CLI가 있으면 아무 일도 하지 않는다")


class TestShape(unittest.TestCase):
    def test_adr0004_1_tests_are_unittest_test_cases(self):
        found = support.tests_outside_testcase(ROOT)
        self.assertEqual([], found, "ADR-0004 규칙 1: unittest.TestCase의 메서드가 아닌 테스트: %s" % found)

    def test_adr0004_4_failure_messages_name_the_id(self):
        found = support.tests_without_id_message(ROOT)
        self.assertEqual([], found, "ADR-0004 규칙 4: 실패의 글에 자기의 ID가 없는 테스트 %d개: %s" % (len(found), found[:8]))

    def test_adr0004_1_checker_finds_a_bare_function_and_a_plain_class(self):
        source = (
            "import unittest\n"
            "def test_ac9_1_bare(): pass\n"
            "class Plain:\n    def test_ac9_2_plain(self): pass\n"
            "class Good(unittest.TestCase):\n    def test_ac9_3_good(self): self.fail('AC-9.3: x')\n"
            "class Sub(Good):\n    def test_r9_sub(self): self.fail('R9: x')\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "tests").mkdir()
            (Path(tmp) / "tests" / "test_x.py").write_text(source, encoding="utf-8")
            found = support.tests_outside_testcase(Path(tmp))
        self.assertEqual(
            [("tests/test_x.py", "test_ac9_1_bare"), ("tests/test_x.py", "test_ac9_2_plain")], found,
            "ADR-0004 규칙 1: 같은 파일의 TestCase를 물려받은 클래스도 TestCase다",
        )

    def test_adr0004_4_checker_finds_a_test_without_its_id(self):
        source = (
            "import unittest\n"
            "class T(unittest.TestCase):\n"
            "    def test_ac9_10_ok(self): self.assertTrue(True, 'AC-9.10: 글')\n"
            "    def test_ac9_1_wrong_id(self): self.assertTrue(True, 'AC-9.10: 다른 ID')\n"
            "    def test_r9_no_message(self): self.assertTrue(True)\n"
            "    def test_adr9999_3_ok(self): self.check('ADR-9999 규칙 3:')\n"
            "    def test_adr9999_4_wrong(self): self.check('ADR-9999 규칙 40:')\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "tests").mkdir()
            (Path(tmp) / "tests" / "test_x.py").write_text(source, encoding="utf-8")
            found = support.tests_without_id_message(Path(tmp))
        self.assertEqual(
            [
                ("tests/test_x.py", "test_ac9_1_wrong_id", "AC-9.1"),
                ("tests/test_x.py", "test_r9_no_message", "R9"),
                ("tests/test_x.py", "test_adr9999_4_wrong", "ADR-9999 규칙 4"),
            ],
            found,
            "ADR-0004 규칙 4: AC-9.10은 AC-9.1이 아니다. 규칙 40은 규칙 4가 아니다",
        )


if __name__ == "__main__":
    unittest.main()
