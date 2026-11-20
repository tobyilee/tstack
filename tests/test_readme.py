"""저장소의 뿌리의 README를 검사한다. Spec 01의 AC-6.3 ~ AC-6.6.

README는 영어의 짧은 절과 한국어의 본문을 가진다. 모르는 사람이 뿌리에서 설치하는 방법을 찾는다.
"""
import tempfile
import unittest
from pathlib import Path

import support

ROOT = support.ROOT
COMMANDS = "/plugin marketplace add tobyilee/tstack\n/plugin install tstack@tstack\n/plugin install explain-diff@tstack\n"
LOCAL = support.ROOT_LOCAL_COMMAND + "\n"


def only(problems, prefix):
    return [p for p in problems if p.startswith(prefix)]


def problems_of(text):
    with tempfile.TemporaryDirectory() as tmp:
        if text is not None:
            (Path(tmp) / "README.md").write_text(text, encoding="utf-8")
        return support.readme_problems(Path(tmp))


class RootReadme(unittest.TestCase):
    def check(self, prefix):
        found = only(support.readme_problems(ROOT), prefix)
        self.assertEqual([], found, "%s 뿌리의 README가 요구를 어긴다: %s" % (prefix, found))

    def test_ac6_3_readme_has_an_english_section(self):
        self.check("AC-6.3:")

    def test_ac6_4_english_section_gives_the_three_install_commands(self):
        self.check("AC-6.4:")

    def test_ac6_5_korean_body_gives_the_three_install_commands(self):
        self.check("AC-6.5:")

    def test_ac6_6_korean_body_gives_the_plugin_dir_command(self):
        self.check("AC-6.6:")

    def test_ac6_3_checker_accepts_a_good_readme_and_finds_a_missing_section(self):
        good = "# tstack\n\n## English\n\n" + COMMANDS + "\n## 설치\n\n" + COMMANDS + "\n## 로컬\n\n" + LOCAL
        self.assertEqual([], problems_of(good), "AC-6.3: 맞는 README에는 문제가 없다")
        self.assertEqual(
            ["AC-6.3: 뿌리의 README.md에 머리가 `## English`인 절이 없다"],
            only(problems_of(good.replace("## English", "## In English")), "AC-6.3:"),
        )
        self.assertEqual(["AC-6.3: 저장소의 뿌리에 README.md가 없다"], problems_of(None))

    def test_ac6_4_checker_finds_commands_missing_from_one_part(self):
        only_korean = "# tstack\n\n## English\n\nInstall it.\n\n## 설치\n\n" + COMMANDS + LOCAL
        self.assertEqual(
            [
                "AC-6.4: `## English`의 절에 설치 명령이 없다: /plugin install explain-diff@tstack",
                "AC-6.4: `## English`의 절에 설치 명령이 없다: /plugin install tstack@tstack",
                "AC-6.4: `## English`의 절에 설치 명령이 없다: /plugin marketplace add tobyilee/tstack",
            ],
            problems_of(only_korean),
            "AC-6.4: 한국어의 본문의 명령은 영어의 절의 명령으로 세지 않는다",
        )

    def test_ac6_5_checker_finds_commands_only_in_the_english_section(self):
        only_english = "# tstack\n\n## English\n\n" + COMMANDS + LOCAL + "\n## 설치\n\n위의 절을 본다.\n"
        self.assertEqual(
            [
                "AC-6.5: 한국어의 본문에 설치 명령이 없다: /plugin install explain-diff@tstack",
                "AC-6.5: 한국어의 본문에 설치 명령이 없다: /plugin install tstack@tstack",
                "AC-6.5: 한국어의 본문에 설치 명령이 없다: /plugin marketplace add tobyilee/tstack",
                "AC-6.6: 한국어의 본문에 명령이 없다: " + support.ROOT_LOCAL_COMMAND,
            ],
            problems_of(only_english),
            "AC-6.5: 영어의 절의 명령은 한국어의 본문의 명령으로 세지 않는다. AC-6.6도 같다",
        )


if __name__ == "__main__":
    unittest.main()
