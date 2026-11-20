"""라이선스와 README를 검사한다. Spec 01의 AC-2.4, AC-2.5, AC-6.1, AC-6.2. Domain 01의 R6.

`support.license_problems`가 문제의 글을 준다. 글은 ID로 시작한다.
"""
import tempfile
import unittest
from pathlib import Path

import support

ROOT = support.ROOT
MIT = "MIT License\n\nCopyright (c) 2026 Toby Lee\n\nPermission is hereby granted ...\n"


def write(folder, name, text=""):
    path = Path(folder) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def only(problems, prefix):
    return [p for p in problems if p.startswith(prefix)]


def good_tree(tmp):
    write(tmp, "LICENSE", MIT)
    for name in ("tstack", "explain-diff"):
        write(tmp, "plugins/%s/LICENSE" % name, MIT)
        write(tmp, "plugins/%s/README.md" % name, "# %s\n" % name)
    return Path(tmp)


class LicenseAndReadme(unittest.TestCase):
    def check(self, prefix):
        found = only(support.license_problems(ROOT), prefix)
        self.assertEqual([], found, "%s 요구를 어긴다: %s" % (prefix, found))

    def test_ac2_4_plugin_folders_have_a_readme(self):
        self.check("AC-2.4:")

    def test_ac2_5_plugin_folders_have_a_license(self):
        self.check("AC-2.5:")

    def test_ac6_1_root_has_an_mit_license(self):
        self.check("AC-6.1:")

    def test_ac6_2_license_has_the_copyright_line(self):
        self.check("AC-6.2:")

    def test_r6_the_three_license_files_are_the_same(self):
        self.check("R6:")

    def test_r6_checker_accepts_a_good_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual([], support.license_problems(good_tree(tmp)), "R6: 맞는 폴더에는 문제가 없다")

    def test_ac6_1_checker_finds_every_license_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = good_tree(tmp)
            (root / "plugins/tstack/README.md").unlink()
            (root / "plugins/explain-diff/LICENSE").unlink()
            write(root, "plugins/tstack/LICENSE", MIT.replace("2026 Toby Lee", "2026 Someone"))
            found = support.license_problems(root)
            write(root, "LICENSE", "Apache License\nVersion 2.0\n")
            apache = only(support.license_problems(root), "AC-6.")
            (root / "LICENSE").unlink()
            missing = only(support.license_problems(root), "AC-6.")
        self.assertEqual(
            [
                "AC-2.4: 플러그인의 폴더에 README.md가 없다: plugins/tstack",
                "AC-2.5: 플러그인의 폴더에 LICENSE가 없다: plugins/explain-diff",
                "R6: LICENSE의 내용이 저장소의 뿌리의 것과 다르다: plugins/tstack/LICENSE",
            ],
            found,
        )
        self.assertEqual(
            [
                "AC-6.1: 뿌리의 LICENSE의 첫 줄이 MIT License가 아니다: Apache License",
                "AC-6.2: 뿌리의 LICENSE에 저작권의 줄이 없다: Copyright (c) 2026 Toby Lee",
            ],
            apache,
        )
        self.assertEqual(["AC-6.1: 저장소의 뿌리에 LICENSE가 없다"], missing)


if __name__ == "__main__":
    unittest.main()
