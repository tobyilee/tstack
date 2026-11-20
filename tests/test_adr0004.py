"""ADR-0004(검증의 방법)의 규칙을 검사한다.

규칙마다 테스트가 둘이다. 하나는 이 저장소를 본다. 다른 하나는 규칙을 어긴
임시의 폴더를 만들고, 검사가 그 위반을 찾는지 본다.
"""
import os
import tempfile
import unittest
from pathlib import Path

import claude_cli
import support

ROOT = support.ROOT


def write(folder, name, text):
    path = Path(folder) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class Rule2StandardLibraryOnly(unittest.TestCase):
    def test_adr0004_2_checks_import_only_the_standard_library(self):
        found = support.non_stdlib_imports(ROOT)
        self.assertEqual([], found, "ADR-0004 규칙 2: 표준 라이브러리가 아닌 패키지를 가져온다: %s" % found)

    def test_adr0004_2_checker_finds_a_third_party_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "tests/test_x.py", "import json\nimport no_such_package_xyz\nfrom . import sibling\n")
            write(tmp, "scripts/tool.py", "import os\nimport helper\n")
            write(tmp, "scripts/helper.py", "")
            found = support.non_stdlib_imports(Path(tmp))
        self.assertEqual(
            [("tests/test_x.py", "no_such_package_xyz")], found,
            "ADR-0004 규칙 2: 검사가 없는 패키지 1개만 찾아야 한다. 표준 라이브러리, 상대 import, 이웃의 모듈은 허용이다",
        )


class Rule3TestNames(unittest.TestCase):
    def test_adr0004_3_test_names_start_with_an_id_token(self):
        found = support.badly_named_tests(ROOT)
        self.assertEqual([], found, "ADR-0004 규칙 3: 이름이 ID의 표지로 시작하지 않는 테스트: %s" % found)

    def test_adr0004_3_checker_finds_a_name_without_an_id(self):
        source = (
            "import unittest\n"
            "class T(unittest.TestCase):\n"
            "    def test_ac99_10_ok(self): pass\n"
            "    def test_r99_ok(self): pass\n"
            "    def test_adr9999_3_ok(self): pass\n"
            "    def test_marketplace_exists(self): pass\n"
            "    def test_ac1_bad(self): pass\n"
            "    def helper(self): pass\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "tests/test_x.py", source)
            found = support.badly_named_tests(Path(tmp))
        self.assertEqual(
            [("tests/test_x.py", "test_marketplace_exists"), ("tests/test_x.py", "test_ac1_bad")], found,
            "ADR-0004 규칙 3: 검사가 ID가 없는 이름 2개만 찾아야 한다",
        )


class Rule5IsolatedConfigFolder(unittest.TestCase):
    def test_adr0004_5_only_the_helper_names_the_cli(self):
        found = support.direct_cli_calls(ROOT)
        self.assertEqual([], found, "ADR-0004 규칙 5: 도우미(tests/claude_cli.py)의 밖에서 CLI를 부른다: %s" % found)

    def test_adr0004_5_checker_finds_a_direct_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "tests/test_x.py", 'import subprocess\nsubprocess.run(["claude", "plugin", "list"])\n')
            write(tmp, "tests/claude_cli.py", 'CLAUDE = "claude"\n')
            write(tmp, "scripts/tool.py", 'import os\nos.system("claude plugin list")\n')
            found = support.direct_cli_calls(Path(tmp))
        self.assertEqual(
            ["scripts/tool.py", "tests/test_x.py"], found,
            "ADR-0004 규칙 5: 검사가 직접 부르는 파일 2개만 찾아야 한다. 도우미는 허용이다",
        )

    def test_adr0004_5_helper_sets_the_config_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = claude_cli.isolated_env(tmp, base_env={"PATH": "/usr/bin"})
            self.assertEqual(
                str(Path(tmp).resolve()), env.get("CLAUDE_CONFIG_DIR"),
                "ADR-0004 규칙 5: 도우미가 CLAUDE_CONFIG_DIR에 격리된 설정 폴더를 넣어야 한다",
            )
            self.assertEqual("/usr/bin", env.get("PATH"), "ADR-0004 규칙 5: 도우미가 다른 환경 변수를 남겨야 한다")

    def test_adr0004_5_helper_refuses_a_missing_config_folder(self):
        with self.assertRaises(ValueError, msg="ADR-0004 규칙 5: 설정 폴더가 없는 호출을 거부해야 한다") as caught:
            claude_cli.isolated_env(None, base_env={})
        self.assertIn("ADR-0004 규칙 5", str(caught.exception))


class Rule6UserConfigFolderUntouched(unittest.TestCase):
    def test_adr0004_6_helper_refuses_the_user_config_folder(self):
        user_dir = Path.home() / ".claude"
        for target in (user_dir, user_dir / "plugins"):
            with self.assertRaises(ValueError, msg="ADR-0004 규칙 6: %s 를 거부해야 한다" % target) as caught:
                claude_cli.isolated_env(target, base_env={})
            self.assertIn("ADR-0004 규칙 6", str(caught.exception))

    def test_adr0004_6_helper_refuses_the_ambient_config_folder(self):
        with tempfile.TemporaryDirectory() as ambient, tempfile.TemporaryDirectory() as other:
            base = {"CLAUDE_CONFIG_DIR": ambient}
            with self.assertRaises(ValueError, msg="ADR-0004 규칙 6: 이미 쓰고 있는 설정 폴더를 거부해야 한다"):
                claude_cli.isolated_env(ambient, base_env=base)
            env = claude_cli.isolated_env(other, base_env=base)
            self.assertEqual(
                str(Path(other).resolve()), env["CLAUDE_CONFIG_DIR"],
                "ADR-0004 규칙 6: 다른 임시 폴더는 허용이다. 이미 있던 값을 덮어써야 한다",
            )

    def test_adr0004_6_helper_does_not_change_the_callers_environment(self):
        before = os.environ.get("CLAUDE_CONFIG_DIR")
        with tempfile.TemporaryDirectory() as tmp:
            claude_cli.isolated_env(tmp)
        self.assertEqual(
            before, os.environ.get("CLAUDE_CONFIG_DIR"),
            "ADR-0004 규칙 6: 도우미가 이 프로세스의 환경 변수를 바꾸면 안 된다",
        )


class Rule11NoEvalRuns(unittest.TestCase):
    def test_adr0004_11_checks_do_not_run_evals(self):
        found = support.eval_runs(ROOT)
        self.assertEqual([], found, "ADR-0004 규칙 11: 검사가 플러그인의 eval을 돌린다: %s" % found)

    def test_adr0004_11_checker_finds_an_eval_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "tests/test_x.py", 'ARGS = ["plugin", "eval", "plugins/explain-diff"]\n')
            write(tmp, "tests/test_ok.py", 'ARGS = ["plugin", "validate", "--strict"]\nNOTE = "eval 사례의 폴더"\n')
            write(tmp, "scripts/tool.py", 'CMD = "claude plugin  ' + 'eval ."\n')
            write(tmp, ".github/workflows/check.yml", "steps:\n  - run: claude plugin " + "eval plugins/explain-diff\n")
            write(tmp, ".github/workflows/ok.yml", "steps:\n  - run: claude plugin validate --strict .\n")
            found = support.eval_runs(Path(tmp))
        self.assertEqual(
            [".github/workflows/check.yml", "scripts/tool.py", "tests/test_x.py"], found,
            "ADR-0004 규칙 11: 검사가 eval을 돌리는 파일 3개만 찾아야 한다",
        )


class Rule13Python39(unittest.TestCase):
    def test_adr0004_13_code_parses_as_python_3_9(self):
        found = support.not_python39(ROOT)
        self.assertEqual([], found, "ADR-0004 규칙 13: Python 3.9의 문법이 아닌 파일: %s" % found)

    def test_adr0004_13_checker_finds_newer_syntax(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "tests/test_new.py", "def f(x):\n    match x:\n        case 1:\n            return 1\n")
            write(tmp, "scripts/old.py", "def f(x):\n    return {**x}\n")
            found = support.not_python39(Path(tmp))
        self.assertEqual(
            ["tests/test_new.py"], found,
            "ADR-0004 규칙 13: 검사가 3.10의 문법(match)을 쓴 파일 1개만 찾아야 한다",
        )


class Rule15EveryAdrRuleIsCovered(unittest.TestCase):
    def test_adr0004_15_every_adr_rule_has_a_test_or_an_exemption(self):
        missing = support.adr_rules_without_tests(ROOT)
        self.assertEqual(
            [], missing,
            "ADR-0004 규칙 15: 테스트가 없고 '테스트가 없는 규칙'의 표에도 없는 ADR의 규칙 %d개: %s"
            % (len(missing), ", ".join(missing)),
        )

    def test_adr0004_15_checker_finds_a_rule_without_a_test(self):
        adr1 = (
            "# ADR-0001. 하나\n\n## 결정\n\n| # | 규칙 | 출처 |\n|---|---|---|\n"
            "| 1 | 첫째 | AI |\n| 2 | 둘째 | AI |\n| 3 | 셋째 | AI |\n\n"
            "### 다른 표\n\n| 1 | 규칙이 아니다 | x |\n\n## 결과\n"
        )
        adr2 = (
            "# ADR-0002. 둘\n\n## 결정\n\n| # | 규칙 | 출처 |\n|---|---|---|\n| 1 | 하나뿐 | AI |\n\n"
            "### 테스트가 없는 규칙\n\n| 규칙 | 증거 |\n|---|---|\n| ADR-0001의 규칙 3 (사람이 본다) | 일지 |\n\n## 결과\n"
        )
        tests = "class T:\n    def test_adr0001_1_first(self): pass\n    def test_adr0001_10_other(self): pass\n"
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "docs/adr/0001-one.md", adr1)
            write(tmp, "docs/adr/0002-two.md", adr2)
            write(tmp, "tests/test_x.py", tests)
            missing = support.adr_rules_without_tests(Path(tmp))
        self.assertEqual(
            ["ADR-0001 규칙 2", "ADR-0002 규칙 1"], missing,
            "ADR-0004 규칙 15: 규칙 1은 테스트가 있고, 규칙 3은 표에 있다. `adr0001_10_`은 규칙 1의 표지가 아니다",
        )


if __name__ == "__main__":
    unittest.main()
