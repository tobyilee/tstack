"""저장소의 구조와 옮긴 파일을 검사한다. ADR-0001, Spec 01의 AC-2.7 · AC-2.9 · AC-3.2, Domain 01의 R7 · R8.

테스트마다 둘이다: 이 저장소를 본다, 그리고 규칙을 어긴 임시의 폴더에서 검사가 문제를 찾는지 본다.
"""
import tempfile
import unittest
from pathlib import Path

import support

import provenance  # scripts/provenance.py

ROOT = support.ROOT
CASES = ["rename-guard-refactor", "retry-backoff", "zen-garden-isometric"]


def write(folder, name, text=""):
    path = Path(folder) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return path


def only(problems, prefix):
    return [p for p in problems if p.startswith(prefix)]


def good_tree(tmp):
    """ADR-0001의 구조를 지키는 가장 작은 폴더."""
    write(tmp, "plugins/tstack/.claude-plugin/plugin.json", "{}")
    write(tmp, "plugins/tstack/GUIDE.md", "# 가이드")
    write(tmp, "plugins/tstack/skills/t-mode/scripts/tstack-check.py", "")
    write(tmp, "plugins/explain-diff/skills/explain-diff/SKILL.md", "")
    write(tmp, "plugins/explain-diff/evals/case-a/prompt.md", "p")
    write(tmp, "plugins/explain-diff/evals/case-a/graders/01.md", "g")
    write(tmp, "docs/spec/01.md", "")
    write(tmp, "tests/test_x.py", "")
    return Path(tmp)


class Adr0001Layout(unittest.TestCase):
    """ADR-0001의 규칙 1 ~ 5. `support.layout_problems`가 규칙마다 문제의 글을 준다."""

    def check_rule(self, number):
        prefix = "ADR-0001 규칙 %d:" % number
        found = only(support.layout_problems(ROOT), prefix)
        self.assertEqual([], found, "%s 이 저장소의 구조가 규칙을 어긴다: %s" % (prefix, found))

    def test_adr0001_1_plugin_folders_are_under_plugins(self):
        self.check_rule(1)

    def test_adr0001_2_repository_folders_are_outside_plugins(self):
        self.check_rule(2)

    def test_adr0001_3_evals_are_in_the_explain_diff_plugin_folder(self):
        self.check_rule(3)

    def test_adr0001_4_guide_is_in_the_tstack_plugin_folder(self):
        self.check_rule(4)

    def test_adr0001_5_root_has_no_skills_or_agents(self):
        self.check_rule(5)

    def test_adr0001_1_checker_accepts_a_good_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual([], support.layout_problems(good_tree(tmp)), "ADR-0001: 구조를 지키는 폴더에는 문제가 없다")

    def test_adr0001_1_checker_finds_a_missing_folder_and_a_stray_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "plugins/tstack/.claude-plugin/plugin.json", "{}")
            write(tmp, "tstack/.claude-plugin/plugin.json", "{}")
            found = only(support.layout_problems(Path(tmp)), "ADR-0001 규칙 1:")
        self.assertEqual(
            [
                "ADR-0001 규칙 1: 플러그인 매니페스트가 plugins/<이름>/의 밖에 있다: tstack/.claude-plugin/plugin.json",
                "ADR-0001 규칙 1: 플러그인의 폴더가 없다: plugins/explain-diff",
            ],
            found,
            "ADR-0001 규칙 1: 검사는 문제의 글을 정렬해서 준다",
        )

    def test_adr0001_2_checker_finds_repository_folders_inside_plugins(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = good_tree(tmp)
            write(root, "plugins/tstack/docs/note.md")
            write(root, "plugins/explain-diff/provenance.json", "{}")
            write(root, "plugins/tests/test_y.py")
            found = only(support.layout_problems(root), "ADR-0001 규칙 2:")
        self.assertEqual(
            [
                "ADR-0001 규칙 2: 플러그인의 폴더가 아닌 것이 plugins/의 안에 있다: plugins/explain-diff/provenance.json",
                "ADR-0001 규칙 2: 플러그인의 폴더가 아닌 것이 plugins/의 안에 있다: plugins/tests",
                "ADR-0001 규칙 2: 플러그인의 폴더가 아닌 것이 plugins/의 안에 있다: plugins/tstack/docs",
            ],
            found,
            "ADR-0001 규칙 2: 스킬의 안의 scripts/(plugins/tstack/skills/t-mode/scripts)는 허용이다",
        )

    def test_adr0001_3_checker_finds_evals_in_the_skill_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "plugins/tstack/.claude-plugin/plugin.json", "{}")
            write(tmp, "plugins/tstack/GUIDE.md")
            write(tmp, "plugins/explain-diff/skills/explain-diff/evals/case-a/prompt.md")
            found = only(support.layout_problems(Path(tmp)), "ADR-0001 규칙 3:")
        self.assertEqual(
            [
                "ADR-0001 규칙 3: eval 사례의 폴더가 없다: plugins/explain-diff/evals",
                "ADR-0001 규칙 3: evals/가 다른 자리에 있다: plugins/explain-diff/skills/explain-diff/evals",
            ],
            found,
        )

    def test_adr0001_4_checker_finds_a_guide_outside_the_plugin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = good_tree(tmp)
            (root / "plugins/tstack/GUIDE.md").unlink()
            write(root, "tstack-guide.md", "# 가이드")
            found = only(support.layout_problems(root), "ADR-0001 규칙 4:")
        self.assertEqual(
            [
                "ADR-0001 규칙 4: 가이드가 없다: plugins/tstack/GUIDE.md",
                "ADR-0001 규칙 4: 가이드가 옛 이름으로 있다: tstack-guide.md",
            ],
            found,
        )

    def test_adr0001_5_checker_finds_skills_at_the_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = good_tree(tmp)
            write(root, "skills/t-mode/SKILL.md")
            write(root, "agents/t-reviewer.md")
            found = only(support.layout_problems(root), "ADR-0001 규칙 5:")
        self.assertEqual(
            [
                "ADR-0001 규칙 5: 저장소의 뿌리에 부품의 폴더가 있다: agents",
                "ADR-0001 규칙 5: 저장소의 뿌리에 부품의 폴더가 있다: skills",
            ],
            found,
        )


class Ac2_7Guide(unittest.TestCase):
    def test_ac2_7_tstack_plugin_folder_has_the_guide(self):
        self.assertTrue((ROOT / "plugins/tstack/GUIDE.md").is_file(), "AC-2.7: plugins/tstack/GUIDE.md가 없다")


class EvalCases(unittest.TestCase):
    def test_ac2_9_three_eval_cases_are_in_the_plugin_evals_folder(self):
        self.assertEqual(
            CASES, support.eval_cases(ROOT),
            "AC-2.9: plugins/explain-diff/evals/의 아래에 eval 사례 3개의 폴더가 있어야 한다",
        )

    def test_r7_eval_cases_have_a_prompt(self):
        found = only(support.eval_case_problems(ROOT), "R7:")
        self.assertEqual([], found, "R7: prompt.md가 없는 eval 사례: %s" % found)

    def test_r8_eval_cases_have_a_grader(self):
        found = only(support.eval_case_problems(ROOT), "R8:")
        self.assertEqual([], found, "R8: graders/의 .md가 없는 eval 사례: %s" % found)

    def test_r7_checker_finds_a_case_without_a_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = good_tree(tmp)
            write(root, "plugins/explain-diff/evals/case-b/graders/01.md", "g")
            write(root, "plugins/explain-diff/evals/case-b/case.yaml", "name: case-b")
            found = support.eval_case_problems(root)
            cases = support.eval_cases(root)
        self.assertEqual(["case-a", "case-b"], cases, "AC-2.9: 검사가 사례의 폴더 2개를 찾아야 한다")
        self.assertEqual(["R7: eval 사례에 prompt.md가 없다: case-b"], found)

    def test_r8_checker_finds_a_case_without_a_grader(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = good_tree(tmp)
            write(root, "plugins/explain-diff/evals/case-b/prompt.md", "p")
            write(root, "plugins/explain-diff/evals/case-b/graders/notes.txt", "글이 아니다")
            write(root, "plugins/explain-diff/evals/case-c/prompt.md", "p")
            found = support.eval_case_problems(root)
        self.assertEqual(
            [
                "R8: eval 사례의 graders/에 .md 파일이 없다: case-b",
                "R8: eval 사례의 graders/에 .md 파일이 없다: case-c",
            ],
            found,
            "R8: graders/가 없는 사례와, graders/에 .md가 없는 사례를 둘 다 찾아야 한다",
        )


class MovedContent(unittest.TestCase):
    def test_ac3_2_moved_files_have_the_source_content(self):
        found = only(provenance.content_problems(provenance.load(ROOT), ROOT), "AC-3.2:")
        self.assertEqual([], found, "AC-3.2: 출처와 내용이 다르거나 없는 옮긴 파일 %d개: %s" % (len(found), found[:5]))

    def test_adr0002_5_unchanged_files_have_no_reason(self):
        found = only(provenance.content_problems(provenance.load(ROOT), ROOT), "ADR-0002 규칙 5:")
        self.assertEqual([], found, "ADR-0002 규칙 5: 내용이 출처와 같은데 바꾼 이유가 있는 항목: %s" % found)

    def test_adr0002_6_blob_hash_is_computed_from_the_content(self):
        self.assertEqual(
            "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391", provenance.git_blob_hash(b""),
            "ADR-0002 규칙 6: 빈 내용의 git blob 해시가 git의 값과 달라야 하지 않는다",
        )
        self.assertEqual(
            "ce013625030ba8dba906f756967f9e9ca394464a", provenance.git_blob_hash(b"hello\n"),
            "ADR-0002 규칙 6: `echo hello | git hash-object --stdin`의 값과 같아야 한다",
        )

    def test_ac3_2_checker_finds_changed_and_missing_content(self):
        same, edited = b"same\n", b"edited\n"
        record = {
            "source": {},
            "files": [
                {"from": "a", "to": "moved/a.md", "blob": provenance.git_blob_hash(same), "changed": None},
                {"from": "b", "to": "moved/b.md", "blob": provenance.git_blob_hash(b"original\n"), "changed": None},
                {"from": "c", "to": "moved/c.md", "blob": provenance.git_blob_hash(b"original\n"), "changed": "고쳤다"},
                {"from": "d", "to": "moved/d.md", "blob": provenance.git_blob_hash(same), "changed": "고쳤다고 적었다"},
                {"from": "e", "to": "moved/e.md", "blob": provenance.git_blob_hash(same), "changed": None},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            for name, data in (("a", same), ("b", edited), ("c", edited), ("d", same)):
                write(tmp, "moved/%s.md" % name, data.decode("utf-8"))
            found = provenance.content_problems(record, Path(tmp))
        self.assertEqual(
            [
                "AC-3.2: 내용이 출처와 다른데 바꾼 이유가 없다: moved/b.md",
                "ADR-0002 규칙 5: 내용이 출처와 같은데 바꾼 이유가 있다: moved/d.md",
                "AC-3.2: 옮긴 파일이 없다: moved/e.md",
            ],
            found,
            "AC-3.2: a(같다)와 c(고쳤고 이유가 있다)는 허용이다",
        )


if __name__ == "__main__":
    unittest.main()
