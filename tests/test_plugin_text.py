"""플러그인의 글을 검사한다. Spec 01의 AC-2.1, AC-2.2, AC-2.8, AC-2.10 ~ AC-2.16.

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

    def test_ac2_15_script_paths_in_python_commands_exist(self):
        self.check("AC-2.15:")

    def test_ac2_16_code_blocks_have_at_most_one_slash_command(self):
        self.check("AC-2.16:")

    def test_ac2_16_checker_finds_two_slash_commands_in_one_code_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = good_tree(tmp)
            write(root, "plugins/tstack/notes.md", (
                "```text\n%s\n%s\n```\n"                       # 1 ~ 4번 줄: 슬래시 명령 2줄이 한 블록에 있다
                "```text\n%s\n```\n"                            # 5 ~ 7번 줄: 블록 하나에 명령 하나다
                "```text\n%s\n```\n"
                "%s\n%s\n"                                       # 블록의 밖의 줄은 세지 않는다
                "```bash\ncl" "aude plugin marketplace update tstack\ncl" "aude plugin update tstack@tstack\n```\n"
                "  ```text\n  /plugin install a@b\n  /plugin install c@d\n  /plugin install e@f\n  ```\n"
            ) % (ADD, INSTALL, ADD, INSTALL, ADD, INSTALL))
            found = support.text_problems(root)
        self.assertEqual(
            [
                "AC-2.16: 코드 블록 하나에 슬래시 명령의 줄이 2개다: plugins/tstack/notes.md:1",
                "AC-2.16: 코드 블록 하나에 슬래시 명령의 줄이 3개다: plugins/tstack/notes.md:17",
            ],
            found,
            "AC-2.16: 셸의 명령의 블록과 블록의 밖의 줄은 세지 않는다. 들여 쓴 블록은 센다",
        )

    def test_ac2_14_checker_finds_other_forms_of_the_source_repository_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = good_tree(tmp)
            write(root, "plugins/tstack/notes.md", (
                "git@github.com:tobyilee/trealworld.git\n"
                "http://github.com/tobyilee/trealworld/blob/%s/a.md\n"
                "https://www.github.com/tobyilee/trealworld\n"
                "https://raw.githubusercontent.com/tobyilee/trealworld/%s/a.md\n"
                "ssh://git@github.com/tobyilee/trealworld.git\n"
                "https://github.com/tobyilee/trealworld/blob/%s/a.md\n"
                "글의 안의 이름 tobyilee/trealworld와 https://github.com/tobyilee/tstack은 출처 저장소의 URL이 아니다.\n"
            ) % (COMMIT, COMMIT, COMMIT))
            found = support.text_problems(root)
        self.assertEqual(
            [
                "AC-2.14: 출처 저장소의 URL이 고정 URL이 아니다: plugins/tstack/notes.md:1 (git@github.com:tobyilee/trealworld.git)",
                "AC-2.14: 출처 저장소의 URL이 고정 URL이 아니다: plugins/tstack/notes.md:2 (http://github.com/tobyilee/trealworld/blob/%s/a.md)" % COMMIT,
                "AC-2.14: 출처 저장소의 URL이 고정 URL이 아니다: plugins/tstack/notes.md:3 (https://www.github.com/tobyilee/trealworld)",
                "AC-2.14: 출처 저장소의 URL이 고정 URL이 아니다: plugins/tstack/notes.md:4 (https://raw.githubusercontent.com/tobyilee/trealworld/%s/a.md)" % COMMIT,
                "AC-2.14: 출처 저장소의 URL이 고정 URL이 아니다: plugins/tstack/notes.md:5 (ssh://git@github.com/tobyilee/trealworld.git)",
            ],
            found,
            "AC-2.14: 고정 URL은 https://github.com/tobyilee/trealworld/로 시작하고 출처 커밋의 해시를 가진다. 6번 줄만 고정 URL이다",
        )

    def test_ac2_15_checker_finds_a_command_with_a_missing_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = good_tree(tmp)
            write(root, "plugins/tstack/skills/t-mode/scripts/check.py", "")
            write(root, "plugins/tstack/notes.md", (
                "```bash\n"
                "python3 plugins/tstack/skills/t-mode/scripts/check.py trace\n"
                "python3 tstack/skills/t-mode/scripts/check.py trace\n"
                "    python3 skills/t-mode/scripts/check.py self\n"
                "```\n"
                "글의 안의 `python3 nowhere.py`는 명령의 줄이 아니다.\n"
                "python3 -m unittest discover -s tests\n"
            ))
            found = support.text_problems(root)
        self.assertEqual(
            [
                "AC-2.15: `python3`의 명령의 줄의 스크립트가 저장소의 뿌리에서 없다: plugins/tstack/notes.md:3 (tstack/skills/t-mode/scripts/check.py)",
                "AC-2.15: `python3`의 명령의 줄의 스크립트가 저장소의 뿌리에서 없다: plugins/tstack/notes.md:4 (skills/t-mode/scripts/check.py)",
            ],
            found,
            "AC-2.15: 코드 블록의 안의 줄도 본다. 옵션(-m)으로 시작하는 줄은 스크립트의 경로가 없다. 보지 않는다",
        )

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
