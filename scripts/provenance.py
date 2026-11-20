"""출처의 기록(`provenance.json`)의 검사의 논리. ADR-0002, ADR-0004 규칙 12.

함수는 문제를 글의 목록으로 준다. 빈 목록이 통과다. 글은 ID로 시작한다 (ADR-0004 규칙 4).
표준 라이브러리만 쓴다. Python 3.9에서 돈다.
"""
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

RECORD = "provenance.json"
KEYS = ("from", "to", "blob", "changed")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
SOURCE_PATHS = ("tstack/", ".claude/skills/explain-diff/", "tstack-guide.md")


def load(root):
    """저장소의 뿌리의 출처의 기록을 읽는다."""
    return json.loads((Path(root) / RECORD).read_text(encoding="utf-8"))


def _files(record):
    files = record.get("files")
    return files if isinstance(files, list) else []


def listing_problems(record, expected):
    """AC-3.1: 항목의 수가 맞고, 같은 출처 파일과 같은 자리가 두 번 나오지 않는다."""
    files = _files(record)
    problems = []
    if len(files) != expected:
        problems.append("AC-3.1: 항목이 %d개다. %d개여야 한다" % (len(files), expected))
    for key, subject in (("from", "from이"), ("to", "to가")):
        seen, twice = set(), []
        for entry in files:
            value = entry.get(key)
            if value in seen and value not in twice:
                twice.append(value)
            seen.add(value)
        problems += ["AC-3.1: %s 두 번 나온다: %s" % (subject, value) for value in twice]
    return problems


def count_by_source_path(record):
    """출처의 경로의 세 갈래마다 항목의 수를 준다. 어느 갈래도 아닌 것은 "다른 곳"이다."""
    counts = {}
    for entry in _files(record):
        source = str(entry.get("from"))
        for prefix in SOURCE_PATHS:
            if source == prefix or (prefix.endswith("/") and source.startswith(prefix)):
                counts[prefix] = counts.get(prefix, 0) + 1
                break
        else:
            counts["다른 곳"] = counts.get("다른 곳", 0) + 1
    return counts


def reason_problems(record):
    """AC-3.3: `changed`는 null이거나, 비어 있지 않은 글이다."""
    problems = []
    for entry in _files(record):
        changed = entry.get("changed")
        if changed is None:
            continue
        if not isinstance(changed, str) or not changed.strip():
            problems.append("AC-3.3: 바꾼 이유가 글이 아니거나 비어 있다: %s" % entry.get("to"))
    return problems


def source_problems(record):
    """AC-3.4: 출처 저장소의 URL과 출처 커밋의 전체 해시(16진수 40자)."""
    source = record.get("source")
    source = source if isinstance(source, dict) else {}
    problems = []
    repository = source.get("repository")
    if not isinstance(repository, str) or not repository.startswith("https://github.com/"):
        problems.append("AC-3.4: repository가 https://github.com/ 의 URL이 아니다: %s" % repository)
    commit = source.get("commit")
    if not isinstance(commit, str) or not HEX40.match(commit):
        problems.append("AC-3.4: commit이 16진수 40자가 아니다: %s" % commit)
    return problems


def _inside_repository(path):
    if not isinstance(path, str) or not path:
        return False
    pure = PurePosixPath(path)
    return not pure.is_absolute() and ".." not in pure.parts


def entry_problems(record):
    """ADR-0002 규칙 4: 항목마다 네 값이 있다. `blob`은 git blob 해시다. `to`는 저장소의 안이다."""
    problems = []
    for number, entry in enumerate(_files(record), 1):
        if not isinstance(entry, dict) or sorted(entry) != sorted(KEYS):
            keys = ", ".join(sorted(entry)) if isinstance(entry, dict) else type(entry).__name__
            problems.append("ADR-0002 규칙 4: 항목 %d의 키가 from, to, blob, changed가 아니다: %s" % (number, keys))
            continue
        if not isinstance(entry["blob"], str) or not HEX40.match(entry["blob"]):
            problems.append("ADR-0002 규칙 4: 항목 %d의 blob이 16진수 40자가 아니다: %s" % (number, entry["blob"]))
        if not isinstance(entry["from"], str) or not entry["from"]:
            problems.append("ADR-0002 규칙 4: 항목 %d의 from이 비어 있다" % number)
        if not _inside_repository(entry["to"]):
            problems.append("ADR-0002 규칙 4: 항목 %d의 to가 이 저장소의 안의 경로가 아니다: %s" % (number, entry["to"]))
    return problems



def git_blob_hash(data):
    """바이트의 내용의 git blob 해시를 준다: `blob <바이트의 수>\\0<내용>`의 SHA-1. ADR-0002 규칙 6."""
    header = ("blob %d" % len(data)).encode("ascii") + b"\x00"
    return hashlib.sha1(header + data).hexdigest()


def content_problems(record, root):
    """옮긴 파일의 내용을 출처의 `blob`과 비교한다. 출처 저장소는 읽지 않는다.

    AC-3.2: 바꾼 이유가 없는 파일은 출처와 바이트가 같다.
    ADR-0002 규칙 5: 출처와 같은 파일은 바꾼 이유가 없다 (`null`).
    """
    root = Path(root)
    problems = []
    for entry in _files(record):
        target = entry.get("to")
        path = root / str(target)
        if not path.is_file():
            problems.append("AC-3.2: 옮긴 파일이 없다: %s" % target)
            continue
        same = git_blob_hash(path.read_bytes()) == entry.get("blob")
        changed = entry.get("changed")
        if changed is None and not same:
            problems.append("AC-3.2: 내용이 출처와 다른데 바꾼 이유가 없다: %s" % target)
        if changed is not None and same:
            problems.append("ADR-0002 규칙 5: 내용이 출처와 같은데 바꾼 이유가 있다: %s" % target)
    return problems
