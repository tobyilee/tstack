"""플러그인의 글을 검사한다. Spec 01의 AC-2.1, AC-2.2, AC-2.8, AC-2.10 ~ AC-2.14.

설치는 플러그인의 폴더만 복사한다. 그래서 글이 폴더의 밖이나 출처 저장소의 옛 자리를 가리키면 안 된다.
`support.text_problems`가 문제의 글을 준다. 글은 ID로 시작하고 파일과 줄의 번호를 가진다.
"""
import tempfile
import unittest
from pathlib import Path

import support

ROOT = support.ROOT
COMMIT = "68fc5e24b76724b37dc9cc7e974121ea347c08ed"
ADD = "/plugin marketplace add tobyilee/tstack"
INSTALL = "/plugin install tstack@tstack"
GOOD = "# 글\n\n%s\n%s\n\n`claude --plugin-dir ./plugins/tstack`\n" % (ADD, INSTALL)


def write(folder, name, text=""):
    path = Path(folder) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def only(problems, prefix):
    return [p for p in problems if p.startswith(prefix)]


def good_tree(tmp):
    write(tmp, "plugins/tstack/README.md", GOOD + "\n[가이드](GUIDE.md) [스킬](skills/t-mode/SKILL.md#top) [밖](https://example.com/x)\n")
    write(tmp, "plugins/tstack/GUIDE.md", GOOD + "\n출처: https://github.com/tobyilee/trealworld/blob/%s/like-pstack.md\n" % COMMIT)
    write(tmp, "plugins/tstack/skills/t-mode/SKILL.md", "# t-mode\n")
    write(tmp, "plugins/explain-diff/README.md", "# explain-diff\n")
    return Path(tmp)


class PluginText(unittest.TestCase):
    def check(self, prefix):
        found = only(support.text_problems(ROOT), prefix)
        self.assertEqual([], found, "%s 플러그인의 글이 요구를 어긴다 (%d곳): %s" % (prefix, len(found), found[:6]))

    def test_ac2_1_relative_links_stay_inside_the_plugin_folder(self):
        self.check("AC-2.1:")

    def test_ac2_2_relative_links_point_to_existing_files(self):
        self.check("AC-2.2:")

    def test_ac2_8_install_lines_do_not_name_trealworld(self):
        self.check("AC-2.8:")

    def test_ac2_10_guide_does_not_say_this_project(self):
        self.check("AC-2.10:")

    def test_ac2_11_guide_and_readme_give_the_two_install_commands(self):
        self.check("AC-2.11:")

    def test_ac2_12_guide_and_readme_give_the_plugin_dir_command(self):
        self.check("AC-2.12:")

    def test_ac2_13_plugin_dir_command_lines_have_the_plugin_path(self):
        self.check("AC-2.13:")

    def test_ac2_14_source_repository_urls_are_pinned(self):
        self.check("AC-2.14:")

    def test_ac2_2_checker_accepts_a_good_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual([], support.text_problems(good_tree(tmp)), "AC-2.2: 맞는 글에는 문제가 없다")

    def test_ac2_1_checker_finds_links_that_leave_the_folder_or_break(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = good_tree(tmp)
            write(root, "plugins/tstack/skills/t-mode/notes.md", (
                "[위](../../../../README.md)\n"
                "[이웃의 플러그인](../../../explain-diff/README.md)\n"
                "[없다](missing.md)\n"
                "```text\n[코드의 안](nowhere.md)\n```\n"
                "`[글의 안의 코드](nowhere.md)`\n"
                "[닻](#section) [메일](mailto:a@example.com)\n"
            ))
            found = support.text_problems(root)
        self.assertEqual(
            [
                "AC-2.1: 상대 링크가 플러그인의 폴더의 밖을 가리킨다: plugins/tstack/skills/t-mode/notes.md:1 (../../../../README.md)",
                "AC-2.1: 상대 링크가 플러그인의 폴더의 밖을 가리킨다: plugins/tstack/skills/t-mode/notes.md:2 (../../../explain-diff/README.md)",
                "AC-2.2: 상대 링크가 없는 파일을 가리킨다: plugins/tstack/skills/t-mode/notes.md:3 (missing.md)",
            ],
            found,
            "AC-2.1: 이웃의 플러그인도 폴더의 밖이다. 코드의 안의 링크, 닻, 메일은 보지 않는다",
        )

    def test_ac2_8_checker_finds_old_install_lines_and_old_wording(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = good_tree(tmp)
            write(root, "plugins/tstack/GUIDE.md", (
                "# 가이드\n"
                "/plugin install tstack --marketplace tobyilee/trealworld\n"
                "claude plugin marketplace add tobyilee/trealworld\n"
                "tstack은 이 프로젝트(trealworld)의 일지에서 나왔다.\n"
                "`claude --plugin-dir ./tstack`으로 시작한다.\n"
                "플래그 `--plugin-dir`는 설치하지 않는다.\n"
                "근거: https://github.com/tobyilee/trealworld/blob/main/like-pstack.md\n"
                "저장소: https://github.com/tobyilee/trealworld\n"
            ))
            found = support.text_problems(root)
        self.assertEqual(
            [
                "AC-2.10: 가이드가 글자 `이 프로젝트`를 가진다: plugins/tstack/GUIDE.md:4",
                "AC-2.11: 설치 명령이 없다: plugins/tstack/GUIDE.md (/plugin install tstack@tstack)",
                "AC-2.11: 설치 명령이 없다: plugins/tstack/GUIDE.md (/plugin marketplace add tobyilee/tstack)",
                "AC-2.13: `--plugin-dir`의 명령의 줄에 경로 plugins/<플러그인의 이름>이 없다: plugins/tstack/GUIDE.md:5",
                "AC-2.14: 출처 저장소의 URL이 고정 URL이 아니다: plugins/tstack/GUIDE.md:7 (https://github.com/tobyilee/trealworld/blob/main/like-pstack.md)",
                "AC-2.14: 출처 저장소의 URL이 고정 URL이 아니다: plugins/tstack/GUIDE.md:8 (https://github.com/tobyilee/trealworld)",
                "AC-2.8: 설치 명령의 줄이 글자 trealworld를 가진다: plugins/tstack/GUIDE.md:2",
                "AC-2.8: 설치 명령의 줄이 글자 trealworld를 가진다: plugins/tstack/GUIDE.md:3",
            ],
            found,
            "AC-2.13: 플래그의 이름만 말하는 6번 줄은 명령의 줄이 아니다",
        )

    def test_ac2_12_checker_finds_a_missing_plugin_dir_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = good_tree(tmp)
            write(root, "plugins/tstack/README.md", "# tstack\n%s\n%s\n" % (ADD, INSTALL))
            found = support.text_problems(root)
        self.assertEqual(["AC-2.12: `claude --plugin-dir`의 명령이 없다: plugins/tstack/README.md"], found)


if __name__ == "__main__":
    unittest.main()
