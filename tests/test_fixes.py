"""알려진 결함의 수정을 검사한다. Spec 01의 AC-2.3, AC-4.1 ~ AC-4.6. ADR-0002의 규칙 7.

스킬의 글의 요구는 글에 그 문장이 있는지를 본다. 모델의 행동은 보지 않는다 (Spec 01의 "받아들인 한계" 1번).
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import support

import provenance  # scripts/provenance.py

ROOT = support.ROOT
TSTACK = ROOT / "plugins" / "tstack"
CHECK = TSTACK / "skills" / "t-mode" / "scripts" / "tstack-check.py"
REFLECT = TSTACK / "skills" / "t-reflect" / "SKILL.md"
RULES = TSTACK / "skills" / "t-mode" / "references" / "project-rules.md"
PRINCIPLES = TSTACK / "skills" / "t-mode" / "principles"
EXPLAIN = ROOT / "plugins" / "explain-diff" / "skills" / "explain-diff" / "SKILL.md"
TEMPLATE = ROOT / "plugins" / "explain-diff" / "skills" / "explain-diff" / "assets" / "template.html"
PINNED = support.SOURCE_REPOSITORY + "/blob/" + support.SOURCE_COMMIT + "/"
CHANGED_SEVEN = [
    "plugins/explain-diff/skills/explain-diff/SKILL.md",
    "plugins/explain-diff/skills/explain-diff/assets/template.html",
    "plugins/tstack/.claude-plugin/plugin.json",
    "plugins/tstack/GUIDE.md",
    "plugins/tstack/README.md",
    "plugins/tstack/skills/t-mode/references/project-rules.md",
    "plugins/tstack/skills/t-reflect/SKILL.md",
]


def run_check(*args):
    return subprocess.run([sys.executable, str(CHECK)] + list(args), capture_output=True, text=True)


class SelfCheck(unittest.TestCase):
    def test_ac2_3_self_check_passes_inside_the_plugin_folder(self):
        result = run_check("self")
        self.assertEqual(0, result.returncode, "AC-2.3: tstack-check.py self가 통과해야 한다: %s" % result.stdout.strip())


class Reflect(unittest.TestCase):
    def test_ac4_1_reflect_forbids_editing_the_installed_copy(self):
        lines = [line for line in REFLECT.read_text(encoding="utf-8").splitlines() if "설치한 사본을 고치지 않는다" in line]
        self.assertTrue(lines, "AC-4.1: t-reflect의 글에 '설치한 사본을 고치지 않는다'는 금지의 문장이 없다")

    def test_ac4_2_reflect_gives_the_plugin_dir_command(self):
        self.assertIn(
            support.PLUGIN_DIR_COMMAND, REFLECT.read_text(encoding="utf-8"),
            "AC-4.2: t-reflect의 글에 수정안을 적용하는 방법(`--plugin-dir`의 명령)이 없다",
        )


class ExplainDiff(unittest.TestCase):
    def test_ac4_3_explain_diff_does_not_say_the_users_house_style(self):
        self.assertNotIn(
            "the user's house style", EXPLAIN.read_text(encoding="utf-8"),
            "AC-4.3: explain-diff의 글이 디자인을 'the user's house style'이라고 부른다",
        )


    def test_ac4_6_template_does_not_name_the_seminar_deck(self):
        lines = [n for n, line in enumerate(TEMPLATE.read_text(encoding="utf-8").splitlines(), 1) if "ai-seminar" in line]
        self.assertEqual([], lines, "AC-4.6: explain-diff의 문서의 틀이 글자 ai-seminar를 가진다 (줄: %s)" % lines)


class ProjectRules(unittest.TestCase):
    def test_ac4_4_rules_block_passes_the_keywords_check(self):
        block = support.first_code_block(RULES.read_text(encoding="utf-8"))
        self.assertIn("## 작업 일지", block, "AC-4.4: project-rules.md의 첫 코드 블록이 규칙의 블록이 아니다")
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "CLAUDE.md"
            target.write_text(block, encoding="utf-8")
            result = run_check("keywords", str(target))
        self.assertEqual(
            0, result.returncode,
            "AC-4.4: 규칙의 블록이 tstack-check.py keywords를 통과해야 한다: %s" % result.stdout.strip(),
        )

    def test_ac4_4_code_block_reader_takes_the_first_block(self):
        text = "글\n```markdown\n첫째 **반드시**\n둘째\n```\n글\n```text\n다른 블록\n```\n"
        self.assertEqual("첫째 **반드시**\n둘째\n", support.first_code_block(text), "AC-4.4: 첫 코드 블록의 내용만 줘야 한다")


class PrincipleCases(unittest.TestCase):
    def test_ac4_5_every_case_line_has_a_pinned_url(self):
        files = sorted(PRINCIPLES.glob("*.md"))
        self.assertEqual(12, len(files), "AC-4.5: principle은 12개다")
        missing = []
        for path in files:
            cases = [line for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("**사례:**")]
            if len(cases) != 1 or PINNED not in cases[0]:
                missing.append(path.name)
        self.assertEqual([], missing, "AC-4.5: '사례'의 줄에 고정 URL이 없는 principle: %s" % missing)


class ChangedFiles(unittest.TestCase):
    def test_adr0002_7_changed_entries_are_the_nineteen_files_of_the_spec(self):
        expected = sorted(CHANGED_SEVEN + ["plugins/tstack/skills/t-mode/principles/" + p.name for p in PRINCIPLES.glob("*.md")])
        self.assertEqual(19, len(expected), "ADR-0002 규칙 7: Spec 01의 바꾼 파일의 표는 19개다")
        record = provenance.load(ROOT)
        changed = sorted(entry["to"] for entry in record["files"] if entry["changed"] is not None)
        self.assertEqual(
            expected, changed,
            "ADR-0002 규칙 7: 출처의 기록의 바꾼 파일이 Spec 01의 표의 19개와 같아야 한다 (지금 %d개)" % len(changed),
        )


if __name__ == "__main__":
    unittest.main()
