"""버전의 검사의 논리. Spec 01의 목표 5, Domain 01의 R5, ADR-0003, ADR-0004 규칙 12.

플러그인 매니페스트의 `version`은 고정 핀이다. 그 글자가 같으면 사용자는 옛 사본을 계속 쓴다.
그래서 마지막 릴리스의 태그의 뒤에 플러그인의 폴더가 바뀌었는데 버전이 같으면 실패다.

함수는 문제를 글의 목록으로 준다. 빈 목록이 통과다. 글은 ID로 시작한다 (ADR-0004 규칙 4).
표준 라이브러리만 쓴다. Python 3.9에서 돈다.

    python3 scripts/version_check.py        # 이 저장소를 검사한다. 문제가 있으면 끝의 코드 1
"""
import json
import re
import subprocess
import sys
from pathlib import Path

PLUGINS_DIR = "plugins"
MANIFEST = ".claude-plugin/plugin.json"
RELEASE_TAG = re.compile(r"^(?P<plugin>.+)--v(?P<version>\d+\.\d+\.\d+)$")
MARK = "--v"


def git(root, *args):
    return subprocess.run(["git"] + list(args), cwd=str(root), capture_output=True, text=True)


def plugin_names(root):
    base = Path(root) / PLUGINS_DIR
    return sorted(d.name for d in base.iterdir() if d.is_dir() and (d / MANIFEST).is_file()) if base.is_dir() else []


def current_version(root, plugin):
    try:
        return json.loads((Path(root) / PLUGINS_DIR / plugin / MANIFEST).read_text(encoding="utf-8")).get("version")
    except (OSError, ValueError):
        return None


def release_tags(root):
    """이름에 `--v`가 있는 태그를 (태그, 플러그인, 버전)으로 준다. 모양이 틀리면 플러그인과 버전이 None이다."""
    found = []
    for tag in git(root, "tag", "--list").stdout.split():
        if MARK not in tag:
            continue
        match = RELEASE_TAG.match(tag)
        found.append((tag, match.group("plugin"), match.group("version")) if match else (tag, None, None))
    return found


def _key(version):
    return tuple(int(part) for part in version.split("."))


def latest_release_tag(root, plugin):
    """플러그인의 릴리스의 태그 중 버전이 가장 높은 것을 준다. 없으면 None이다."""
    mine = [(tag, version) for tag, name, version in release_tags(root) if name == plugin]
    return max(mine, key=lambda item: _key(item[1]))[0] if mine else None


def version_at(root, tag, plugin):
    shown = git(root, "show", "%s:%s/%s/%s" % (tag, PLUGINS_DIR, plugin, MANIFEST))
    try:
        return json.loads(shown.stdout).get("version") if shown.returncode == 0 else None
    except ValueError:
        return None


def changed_since(root, tag, plugin):
    """태그와 지금의 작업 트리가 플러그인의 폴더에서 다른가. git이 추적하는 파일만 본다."""
    return git(root, "diff", "--quiet", tag, "--", "%s/%s" % (PLUGINS_DIR, plugin)).returncode != 0


def version_problems(root):
    root = Path(root)
    if git(root, "rev-parse", "--is-shallow-repository").stdout.strip() == "true":
        return ["ADR-0003 규칙 5: 얕은 clone이다. 릴리스의 태그가 없는지 받지 않았는지 구분하지 못한다. 전체의 역사와 태그를 받는다"]
    plugins = plugin_names(root)
    problems = []
    for tag, plugin, version in release_tags(root):
        if plugin is None:
            problems.append("ADR-0003 규칙 3: 릴리스의 태그의 이름이 <플러그인의 이름>--v<버전>이 아니다: %s" % tag)
        elif plugin not in plugins:
            problems.append("ADR-0003 규칙 3: 릴리스의 태그의 플러그인이 없다: %s" % tag)
        elif version_at(root, tag, plugin) != version:
            problems.append("R5: 태그 %s이 가리키는 커밋의 플러그인 매니페스트의 버전은 %s이다" % (tag, version_at(root, tag, plugin)))
    for plugin in plugins:
        tag = latest_release_tag(root, plugin)
        if tag is None:
            continue  # AC-5.3: 릴리스가 아직 없다
        released = RELEASE_TAG.match(tag).group("version")
        if changed_since(root, tag, plugin) and current_version(root, plugin) == released:
            problems.append("AC-5.1: 플러그인 %s의 파일이 %s의 뒤에 바뀌었는데 version이 %s 그대로다" % (plugin, tag, released))
    return sorted(problems)


if __name__ == "__main__":
    found = version_problems(Path(__file__).resolve().parent.parent)
    for line in found:
        print(line)
    print("실패: 버전의 검사 (%d개)" % len(found) if found else "통과: 버전의 검사")
    sys.exit(1 if found else 0)
