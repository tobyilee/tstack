"""마켓플레이스 매니페스트와 플러그인 매니페스트를 검사한다.

Spec 01의 AC-1.1 ~ AC-1.3, AC-1.6, AC-1.7, AC-1.9, AC-2.6. Domain 01의 R1 ~ R4. ADR-0003의 규칙 1, 2.
`support.manifest_problems`가 문제의 글을 준다. 글은 ID로 시작한다. 테스트가 ID로 거른다.
"""
import json
import tempfile
import unittest
from pathlib import Path

import support

ROOT = support.ROOT


def write_json(folder, name, data):
    path = Path(folder) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def only(problems, prefix):
    return [p for p in problems if p.startswith(prefix)]


class Manifests(unittest.TestCase):
    def check(self, prefix):
        found = only(support.manifest_problems(ROOT), prefix)
        self.assertEqual([], found, "%s 매니페스트가 요구를 어긴다: %s" % (prefix, found))

    def test_ac1_1_marketplace_manifest_exists(self):
        self.check("AC-1.1:")

    def test_ac1_2_marketplace_name_is_tstack(self):
        self.check("AC-1.2:")

    def test_ac1_3_marketplace_lists_the_two_plugins(self):
        self.check("AC-1.3:")

    def test_ac1_9_tstack_does_not_depend_on_explain_diff(self):
        self.check("AC-1.9:")

    def test_ac2_6_plugin_license_is_mit(self):
        self.check("AC-2.6:")

    def test_r1_plugin_name_is_the_same_in_three_places(self):
        self.check("R1:")

    def test_r2_entry_source_points_to_the_plugin_folder(self):
        self.check("R2:")

    def test_r3_version_is_three_numbers(self):
        self.check("R3:")

    def test_r4_marketplace_entries_have_no_version(self):
        self.check("R4:")

    def test_adr0003_1_plugin_manifests_have_a_version(self):
        self.check("ADR-0003 규칙 1:")

    def test_adr0003_2_version_lives_only_in_the_plugin_manifest(self):
        self.check("R4:")
        for name in ("tstack", "explain-diff"):
            manifest = json.loads((ROOT / "plugins" / name / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
            self.assertIn("version", manifest, "ADR-0003 규칙 2: 버전의 자리는 플러그인 매니페스트다: %s" % name)

    def test_ac1_3_checker_accepts_good_manifests(self):
        with tempfile.TemporaryDirectory() as tmp:
            good_manifests(tmp)
            self.assertEqual([], support.manifest_problems(Path(tmp)), "AC-1.3: 맞는 매니페스트에는 문제가 없다")

    def test_ac1_1_checker_finds_a_missing_marketplace_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            good_manifests(tmp)
            (Path(tmp) / ".claude-plugin" / "marketplace.json").unlink()
            found = only(support.manifest_problems(Path(tmp)), "AC-1.1:")
        self.assertEqual(["AC-1.1: 마켓플레이스 매니페스트가 없다: .claude-plugin/marketplace.json"], found)

    def test_r4_checker_finds_every_manifest_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_json(tmp, ".claude-plugin/marketplace.json", {
                "name": "trealworld", "owner": {"name": "x"},
                "plugins": [
                    {"name": "tstack", "source": "./tstack", "version": "0.2.0"},
                    {"name": "explain-diff", "source": "./plugins/explain-diff"},
                    {"name": "extra", "source": "./plugins/extra"},
                ],
            })
            write_json(tmp, "plugins/tstack/.claude-plugin/plugin.json", {
                "name": "t-stack", "version": "0.2", "license": "Apache-2.0",
                "dependencies": ["other", {"name": "explain-diff"}],
            })
            write_json(tmp, "plugins/explain-diff/.claude-plugin/plugin.json", {"name": "explain-diff"})
            found = support.manifest_problems(Path(tmp))
        self.assertEqual(
            [
                "AC-1.2: 마켓플레이스의 name이 tstack이 아니다: trealworld",
                "AC-1.3: 플러그인의 목록이 tstack, explain-diff의 2개가 아니다: explain-diff, extra, tstack",
                "AC-1.9: 플러그인 tstack이 dependencies로 explain-diff를 요구한다",
                "AC-2.6: 플러그인 매니페스트의 license가 MIT가 아니다: explain-diff (None)",
                "AC-2.6: 플러그인 매니페스트의 license가 MIT가 아니다: tstack (Apache-2.0)",
                "ADR-0003 규칙 1: 플러그인 매니페스트에 version이 없다: explain-diff",
                "R1: 플러그인 매니페스트의 name이 폴더의 이름과 다르다: plugins/tstack (t-stack)",
                "R1: 플러그인의 항목에 맞는 플러그인의 폴더가 없다: extra",
                "R2: 플러그인의 항목의 source가 ./plugins/tstack이 아니다: ./tstack",
                "R3: 버전이 점으로 나눈 숫자 3개가 아니다: tstack (0.2)",
                "R4: 플러그인의 항목이 version을 가진다: tstack",
            ],
            found,
            "R4: 검사가 틀린 매니페스트의 문제 11개를 모두 찾아야 한다",
        )

    def test_ac1_9_checker_reads_the_three_shapes_of_a_dependency(self):
        for dependency in ("explain-diff", "explain-diff@tstack", {"name": "explain-diff", "version": "^0.1"}):
            with tempfile.TemporaryDirectory() as tmp:
                good_manifests(tmp, tstack_extra={"dependencies": [dependency]})
                found = only(support.manifest_problems(Path(tmp)), "AC-1.9:")
            self.assertEqual(
                ["AC-1.9: 플러그인 tstack이 dependencies로 explain-diff를 요구한다"], found,
                "AC-1.9: 검사가 %r 의 모양을 찾아야 한다" % (dependency,),
            )
        with tempfile.TemporaryDirectory() as tmp:
            good_manifests(tmp, tstack_extra={"dependencies": ["something-else"]})
            self.assertEqual([], support.manifest_problems(Path(tmp)), "AC-1.9: 다른 플러그인의 dependency는 허용이다")


class Components(unittest.TestCase):
    def test_ac1_6_tstack_provides_two_skills_and_one_agent(self):
        self.assertEqual(
            {"skills": ["t-mode", "t-reflect"], "agents": ["t-reviewer"]},
            support.plugin_components(ROOT, "tstack"),
            "AC-1.6: 플러그인 tstack은 스킬 t-mode, t-reflect와 agent t-reviewer를 제공해야 한다",
        )

    def test_ac1_7_explain_diff_provides_one_skill(self):
        self.assertEqual(
            {"skills": ["explain-diff"], "agents": []},
            support.plugin_components(ROOT, "explain-diff"),
            "AC-1.7: 플러그인 explain-diff는 스킬 explain-diff 1개를 제공해야 한다",
        )
        self.assertTrue(
            (ROOT / "plugins/explain-diff/.claude-plugin/plugin.json").is_file(),
            "AC-1.7: 플러그인 explain-diff에 플러그인 매니페스트가 없다. 매니페스트가 없으면 플러그인이 아니다",
        )

    def test_ac1_6_checker_counts_only_real_components(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "plugins" / "p"
            for rel in ("skills/a/SKILL.md", "skills/b/notes.md", "skills/c/SKILL.md", "agents/x.md", "agents/readme.txt"):
                (base / rel).parent.mkdir(parents=True, exist_ok=True)
                (base / rel).write_text("", encoding="utf-8")
            self.assertEqual(
                {"skills": ["a", "c"], "agents": ["x"]}, support.plugin_components(Path(tmp), "p"),
                "AC-1.6: SKILL.md가 있는 폴더만 스킬이다. .md 파일만 agent다",
            )


def good_manifests(tmp, tstack_extra=None):
    write_json(tmp, ".claude-plugin/marketplace.json", {
        "name": "tstack", "owner": {"name": "x"},
        "plugins": [
            {"name": "tstack", "source": "./plugins/tstack"},
            {"name": "explain-diff", "source": "./plugins/explain-diff"},
        ],
    })
    tstack = {"name": "tstack", "version": "0.2.0", "license": "MIT"}
    tstack.update(tstack_extra or {})
    write_json(tmp, "plugins/tstack/.claude-plugin/plugin.json", tstack)
    write_json(tmp, "plugins/explain-diff/.claude-plugin/plugin.json", {"name": "explain-diff", "version": "0.1.0", "license": "MIT"})


if __name__ == "__main__":
    unittest.main()
