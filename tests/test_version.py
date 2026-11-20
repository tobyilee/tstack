"""버전의 검사를 검사한다. Spec 01의 AC-5.1 ~ AC-5.3. Domain 01의 R5. ADR-0003의 규칙 3 ~ 5. ADR-0004의 규칙 12.

검사의 논리는 `scripts/version_check.py`에 있다. 테스트는 임시의 git 저장소에서 상태를 만든다.
이 저장소는 "태그가 있고 파일이 바뀐" 상태가 아니다. 그래서 임시의 저장소가 필요하다.
"""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import support

import provenance      # scripts/provenance.py
import version_check   # scripts/version_check.py

ROOT = support.ROOT
GIT = ["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false"]


def git(repo, *args):
    done = subprocess.run(GIT + list(args), cwd=str(repo), capture_output=True, text=True)
    assert done.returncode == 0, "git %s: %s" % (" ".join(args), done.stderr)
    return done.stdout


def manifest(repo, name, version):
    path = Path(repo) / "plugins" / name / ".claude-plugin" / "plugin.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"name": name, "version": version}), encoding="utf-8")


def write(repo, rel, text):
    path = Path(repo) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def new_repo(tmp):
    """플러그인 a와 b가 있고 커밋이 1개인 저장소. 버전은 둘 다 1.0.0이다."""
    repo = Path(tmp) / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    for name in ("a", "b"):
        manifest(repo, name, "1.0.0")
        write(repo, "plugins/%s/skills/s/SKILL.md" % name, "v1\n")
    write(repo, "README.md", "root\n")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "first")
    return repo


def release(repo, *tags):
    for tag in tags:
        git(repo, "tag", tag)


class VersionCheck(unittest.TestCase):
    def problems(self, repo):
        return version_check.version_problems(repo)

    def test_ac5_3_plugin_without_a_release_tag_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = new_repo(tmp)
            write(repo, "plugins/a/skills/s/SKILL.md", "changed\n")
            self.assertEqual([], self.problems(repo), "AC-5.3: 릴리스의 태그가 없으면 버전의 검사는 통과한다")

    def test_ac5_2_plugin_unchanged_since_the_tag_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = new_repo(tmp)
            release(repo, "a--v1.0.0", "b--v1.0.0")
            write(repo, "README.md", "the root changed\n")
            write(repo, "docs/note.md", "new file outside the plugins\n")
            self.assertEqual([], self.problems(repo), "AC-5.2: 플러그인의 폴더가 바뀌지 않았으면 통과한다. 폴더의 밖의 변경은 세지 않는다")

    def test_ac5_1_changed_plugin_with_the_same_version_fails(self):
        expected = ["AC-5.1: 플러그인 a의 파일이 a--v1.0.0의 뒤에 바뀌었는데 version이 1.0.0 그대로다"]
        with tempfile.TemporaryDirectory() as tmp:
            repo = new_repo(tmp)
            release(repo, "a--v1.0.0", "b--v1.0.0")
            write(repo, "plugins/a/skills/s/SKILL.md", "fixed a typo\n")
            self.assertEqual(expected, self.problems(repo), "AC-5.1: 커밋하지 않은 변경도 '바뀌었다'다")
            git(repo, "commit", "-q", "-am", "typo")
            self.assertEqual(expected, self.problems(repo), "AC-5.1: 커밋한 변경도 '바뀌었다'다")
            manifest(repo, "a", "1.0.1")
            self.assertEqual([], self.problems(repo), "AC-5.1: 버전을 올리면 통과한다")

    def test_ac5_1_added_and_deleted_files_count_as_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = new_repo(tmp)
            release(repo, "a--v1.0.0", "b--v1.0.0")
            write(repo, "plugins/b/skills/s/extra.md", "new\n")
            self.assertEqual([], self.problems(repo), "AC-5.1: git이 추적하지 않는 파일은 세지 않는다 (ADR-0003)")
            git(repo, "add", "plugins/b/skills/s/extra.md")
            self.assertEqual(
                ["AC-5.1: 플러그인 b의 파일이 b--v1.0.0의 뒤에 바뀌었는데 version이 1.0.0 그대로다"], self.problems(repo),
                "AC-5.1: 더한 파일은 git이 추적한 뒤에 센다",
            )
            git(repo, "rm", "-q", "-f", "plugins/b/skills/s/extra.md")
            git(repo, "rm", "-q", "plugins/a/skills/s/SKILL.md")
            self.assertEqual(
                ["AC-5.1: 플러그인 a의 파일이 a--v1.0.0의 뒤에 바뀌었는데 version이 1.0.0 그대로다"], self.problems(repo),
                "AC-5.1: 지운 파일도 '바뀌었다'다",
            )

    def test_ac5_1_this_repository_has_no_change_without_a_version_bump(self):
        self.assertEqual([], version_check.version_problems(ROOT), "AC-5.1: 이 저장소의 버전의 검사가 통과해야 한다")

    def test_r5_tag_version_matches_the_manifest_at_the_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = new_repo(tmp)
            release(repo, "a--v1.0.0", "b--v2.0.0")
            self.assertEqual(
                ["R5: 태그 b--v2.0.0이 가리키는 커밋의 플러그인 매니페스트의 버전은 1.0.0이다"], self.problems(repo),
                "R5: 태그의 버전과 그 커밋의 매니페스트의 버전이 다르면 실패한다",
            )

    def test_adr0003_3_release_tags_are_named_plugin_dash_dash_v_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = new_repo(tmp)
            release(repo, "a--v1.0.0", "a--vbeta", "ghost--v1.0.0", "v1.0.0")
            self.assertEqual(
                [
                    "ADR-0003 규칙 3: 릴리스의 태그의 이름이 <플러그인의 이름>--v<버전>이 아니다: a--vbeta",
                    "ADR-0003 규칙 3: 릴리스의 태그의 플러그인이 없다: ghost--v1.0.0",
                ],
                self.problems(repo),
                "ADR-0003 규칙 3: `--v`가 없는 태그(v1.0.0)는 릴리스의 태그가 아니다. 보지 않는다",
            )

    def test_adr0003_4_each_plugin_is_compared_with_its_own_latest_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = new_repo(tmp)
            release(repo, "a--v1.0.0", "b--v1.0.0")
            manifest(repo, "a", "1.9.0")
            git(repo, "commit", "-q", "-am", "a 1.9.0")
            release(repo, "a--v1.9.0")
            manifest(repo, "a", "1.10.0")
            git(repo, "commit", "-q", "-am", "a 1.10.0")
            release(repo, "a--v1.10.0")
            self.assertEqual("a--v1.10.0", version_check.latest_release_tag(repo, "a"), "ADR-0003 규칙 4: 1.10.0은 1.9.0보다 높다. 글자의 순서가 아니다")
            self.assertEqual(None, version_check.latest_release_tag(repo, "none"), "ADR-0003 규칙 4: 태그가 없으면 None이다")
            self.assertEqual([], self.problems(repo), "ADR-0003 규칙 4: a의 변경은 b의 검사에 들지 않는다")
            write(repo, "plugins/a/skills/s/SKILL.md", "after 1.10.0\n")
            self.assertEqual(
                ["AC-5.1: 플러그인 a의 파일이 a--v1.10.0의 뒤에 바뀌었는데 version이 1.10.0 그대로다"], self.problems(repo),
                "ADR-0003 규칙 4: 비교의 기준은 마지막 릴리스의 태그다",
            )

    def test_adr0003_5_shallow_clone_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = new_repo(tmp)
            release(repo, "a--v1.0.0")
            write(repo, "plugins/a/skills/s/SKILL.md", "second\n")
            git(repo, "commit", "-q", "-am", "second")
            shallow = Path(tmp) / "shallow"
            git(tmp, "clone", "-q", "--depth", "1", "--no-tags", repo.as_uri(), str(shallow))
            self.assertEqual(
                ["ADR-0003 규칙 5: 얕은 clone이다. 릴리스의 태그가 없는지 받지 않았는지 구분하지 못한다. 전체의 역사와 태그를 받는다"],
                self.problems(shallow),
                "ADR-0003 규칙 5: 얕은 clone에서는 통과가 아니고 실패다",
            )

    def test_adr0004_12_check_logic_lives_in_the_scripts_folder(self):
        for module, function in ((version_check, "version_problems"), (provenance, "content_problems")):
            self.assertTrue(callable(getattr(module, function, None)), "ADR-0004 규칙 12: %s.%s가 없다" % (module.__name__, function))
            self.assertEqual(
                ROOT / "scripts", Path(module.__file__).resolve().parent,
                "ADR-0004 규칙 12: %s의 논리는 scripts/에 있어야 한다" % module.__name__,
            )


if __name__ == "__main__":
    unittest.main()
