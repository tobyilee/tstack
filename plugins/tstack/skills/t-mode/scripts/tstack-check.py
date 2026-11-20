#!/usr/bin/env python3
"""tstack의 검사. 글로 쓴 규칙을 실행할 수 있는 검사로 바꾼 것이다.

  trace     spec과 domain의 ID가 plan과 테스트의 이름에 모두 있는가
  keywords  문서의 RFC 2119 키워드가 규칙대로 쓰였는가
  journal   오늘의 일지가 이 변경과 함께 바뀌었는가
  self      t-mode의 색인과 파일이 맞는가

끝의 코드: 0은 통과, 1은 실패, 2는 검사할 수 없음(미확정).
표준 라이브러리만 쓴다.
"""
import argparse
import datetime
import re
import subprocess
import sys
from pathlib import Path

PASS, FAIL, INCONCLUSIVE = 0, 1, 2
TEXT_SUFFIXES = {
    ".java", ".kt", ".kts", ".groovy", ".scala", ".py", ".js", ".jsx", ".ts",
    ".tsx", ".go", ".rs", ".rb", ".cs", ".swift", ".php", ".hurl", ".feature",
}


def read(path):
    return Path(path).read_text(encoding="utf-8")


def report(name, problems, summary):
    if problems:
        print(f"실패: {name}")
        for p in problems:
            print(f"  - {p}")
        print(f"  ({summary})")
        return FAIL
    print(f"통과: {name} ({summary})")
    return PASS


def inconclusive(name, why):
    print(f"미확정: {name}. {why}")
    return INCONCLUSIVE


# ---------------------------------------------------------------- trace

AC_ROW = re.compile(r"^\|\s*(AC-\d+\.\d+)\s*\|")
R_ROW = re.compile(r"^\|\s*(R\d+)\s*\|")
AC_RANGE = re.compile(r"AC-(\d+)\.(\d+)\s*[~∼-]\s*(?:AC-)?(?:\1\.)?(\d+)")
R_RANGE = re.compile(r"\bR(\d+)\s*[~∼-]\s*R?(\d+)\b")
AC_ONE = re.compile(r"AC-\d+\.\d+")
R_ONE = re.compile(r"(?<![A-Za-z0-9])R\d+(?![0-9A-Za-z])")


def defined_ids(folder, row):
    ids, dup = [], []
    for f in sorted(Path(folder).glob("*.md")):
        for line in read(f).splitlines():
            m = row.match(line)
            if m:
                (dup if m.group(1) in ids else ids).append(m.group(1))
    return ids, dup


def ids_in_text(text):
    found = set(AC_ONE.findall(text)) | set(R_ONE.findall(text))
    for major, a, b in AC_RANGE.findall(text):
        found |= {f"AC-{major}.{n}" for n in range(int(a), int(b) + 1)}
    for a, b in R_RANGE.findall(text):
        found |= {f"R{n}" for n in range(int(a), int(b) + 1)}
    return found


def test_token(id_):
    if id_.startswith("AC-"):
        return "ac" + id_[3:].replace(".", "_") + "_"
    return id_.lower() + "_"


def cmd_trace(args):
    docs = Path(args.docs)
    acs, dup_ac = defined_ids(docs / "spec", AC_ROW)
    rules, dup_r = defined_ids(docs / "domain", R_ROW)
    ids = acs + rules
    if not ids:
        return inconclusive("trace", f"{docs}/spec과 {docs}/domain의 표에 ID가 없다")
    problems = [f"ID가 두 번 정의됐다: {d}" for d in dup_ac + dup_r]

    plans = sorted((docs / "plan").glob("*.md"))
    if plans:
        planned = set()
        for p in plans:
            planned |= ids_in_text(read(p))
        problems += [f"plan에 없다: {i}" for i in ids if i not in planned]
        known = set(ids)
        problems += [f"plan이 없는 ID를 가리킨다: {i}" for i in sorted(planned - known)]
    else:
        problems.append(f"{docs}/plan에 문서가 없다")

    tested = "보지 않았다 (--no-tests)"
    if not args.no_tests:
        tests = Path(args.tests)
        if not tests.is_dir():
            return inconclusive("trace", f"테스트의 폴더가 없다: {tests}. 문서만 보려면 --no-tests")
        blob = "\n".join(
            read(f).lower() for f in tests.rglob("*")
            if f.is_file() and f.suffix in TEXT_SUFFIXES
        )
        missing = [
            i for i in ids
            if not re.search(r"(?<![a-z0-9])" + re.escape(test_token(i)), blob)
        ]
        problems += [f"이름에 `{test_token(i)}`가 있는 테스트가 없다: {i}" for i in missing]
        tested = f"테스트가 있는 ID {len(ids) - len(missing)}/{len(ids)}"
    return report("trace", problems, f"수용 기준 {len(acs)}개, 규칙 {len(rules)}개, {tested}")


# ------------------------------------------------------------- keywords

BOLD = re.compile(r"\*\*[^*]+\*\*")
LEVEL_ROW = re.compile(r"^\|\s*([A-Za-z0-9.\-]+)\s*\|\s*(MUST NOT|MUST|SHOULD|MAY)\s*\|(.*)$")
LEVEL_WORD = {"MUST": "반드시", "MUST NOT": "절대", "SHOULD": "권장한다", "MAY": "수 있다"}
CODE = re.compile(r"`[^`]*`")
QUOTED = re.compile(r"\"[^\"]*\"|“[^”]*”")


def requirement_lines(text):
    """요구가 있을 수 있는 줄만 준다. 읽는 법, 상태의 줄, 코드 블록은 뺀다."""
    skip_section = in_code = False
    for no, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if line.startswith("#"):
            skip_section = "읽는 법" in line
            continue
        if skip_section or re.match(r"^- (상태|읽는 법)\s*:", line):
            continue
        yield no, line


def cmd_keywords(args):
    files = [Path(f) for f in args.files]
    if not files:
        docs = Path(args.docs)
        for sub in ("spec", "domain", "adr"):
            files += sorted((docs / sub).glob("*.md"))
    if not files:
        return inconclusive("keywords", "검사할 문서가 없다")
    problems, counts = [], {"반드시": 0, "절대": 0, "권장한다": 0, "MAY": 0}
    for f in files:
        for no, line in requirement_lines(read(f)):
            where = f"{f}:{no}"
            bolds = " ".join(BOLD.findall(line))
            plain = QUOTED.sub("", CODE.sub("", BOLD.sub("", line)))
            counts["반드시"] += bolds.count("반드시")
            counts["절대"] += bolds.count("절대")
            counts["권장한다"] += bolds.count("권장한다")
            counts["MAY"] += bolds.count("수 있다")
            for word in ("반드시", "절대"):
                if word in plain:
                    problems.append(f"{where} 굵지 않은 \"{word}\". 요구면 굵게 쓰고, 설명이면 다른 말을 쓴다")
            if re.search(r"수\s*(있|없)", plain):
                problems.append(f"{where} 허용(MAY)이 아닌 \"수 있다/없다\". 능력과 가능성에는 다른 말을 쓴다")
            m = LEVEL_ROW.match(line)
            if m:
                id_, level, rest = m.groups()
                rest_bold = " ".join(BOLD.findall(rest))
                if LEVEL_WORD[level] not in rest_bold:
                    problems.append(f"{where} {id_}의 수준은 {level}인데 문장에 굵은 \"{LEVEL_WORD[level]}\"가 없다")
                if level == "MUST" and "절대" in rest_bold and "반드시" not in rest_bold:
                    problems.append(f"{where} {id_}의 수준은 MUST인데 문장은 금지다")
    summary = f"문서 {len(files)}개, " + ", ".join(f"{k} {v}" for k, v in counts.items())
    return report("keywords", problems, summary)


# -------------------------------------------------------------- journal

def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True)


def cmd_journal(args):
    date = args.date or datetime.date.today().isoformat()
    journal = f"{args.docs}/journal/{date}.md"
    status = git("status", "--porcelain", "--untracked-files=all")
    if status.returncode != 0:
        return inconclusive("journal", "git 저장소가 아니다")
    changed = [line[3:].split(" -> ")[-1].strip('"') for line in status.stdout.splitlines()]
    if not changed:
        last = git("log", "-1", "--name-only", "--format=").stdout.split()
        if journal in last:
            return report("journal", [], "작업 트리가 깨끗하다. 마지막 커밋에 오늘의 일지가 있다")
        return report("journal", [], "작업 트리가 깨끗하다. 기록할 변경이 없다")
    if journal in changed:
        steps = len(re.findall(r"^## 스텝 \d+", read(journal), re.M)) if Path(journal).exists() else 0
        return report("journal", [], f"{journal}이 바뀌었다. 스텝 {steps}개. 바뀐 파일 {len(changed)}개")
    return report(
        "journal",
        [f"바뀐 파일이 {len(changed)}개인데 {journal}은 바뀌지 않았다. 커밋의 전에 일지를 쓴다"],
        "일지는 스텝마다 쓴다",
    )


# ----------------------------------------------------------------- self

REF = re.compile(r"`((?:playbooks|principles|references|scripts)/[A-Za-z0-9_.\-]+)`")


def cmd_self(args):
    root = Path(__file__).resolve().parent.parent
    router = root / "SKILL.md"
    problems = []
    router_text = read(router)
    indexed = set(REF.findall(router_text))
    for kind in ("playbooks", "principles"):
        on_disk = {f"{kind}/{f.name}" for f in (root / kind).glob("*.md")}
        in_index = {r for r in indexed if r.startswith(kind + "/")}
        problems += [f"색인에 없다: {r}" for r in sorted(on_disk - in_index)]
        problems += [f"파일이 없다: {r}" for r in sorted(in_index - on_disk)]
    if len(router_text.splitlines()) > 150:
        problems.append("라우터가 150줄을 넘는다. 본문을 별도의 파일로 옮긴다")
    for f in sorted(root.rglob("*.md")):
        base = f.parent if f.parent.name in ("playbooks", "principles", "references") else None
        for ref in REF.findall(read(f)):
            if not (root / ref).exists():
                problems.append(f"{f.relative_to(root)}가 없는 파일을 가리킨다: {ref}")
        if base is None:
            continue
        lines = [line for line in read(f).splitlines() if line.strip()]
        rel = f.relative_to(root)
        if base.name == "playbooks":
            if not lines[0].startswith("### "):
                problems.append(f"{rel} 첫 줄이 `### 이름`이 아니다")
            if not lines[1].startswith("**당신은"):
                problems.append(f"{rel} 둘째 줄이 소유의 문장(`**당신은 …`)이 아니다")
            if not lines[-1].startswith("**보고:**"):
                problems.append(f"{rel} 마지막 줄이 `**보고:**`가 아니다")
            steps = [line for line in lines if re.match(r"^\d+\. ", line)]
            if len(steps) < 3:
                problems.append(f"{rel} 번호가 있는 단계가 3개보다 적다")
            if len(lines) > 25:
                problems.append(f"{rel} 비어 있지 않은 줄이 {len(lines)}개다. 25개 이하로 줄인다")
            if f.name not in ("wrap-up.md",) and not any("wrap-up.md" in s for s in steps):
                problems.append(f"{rel} 마무리(`wrap-up.md`)를 부르는 단계가 없다")
        if base.name == "principles":
            for mark in ("**왜:**", "**방법:**", "**쓴 흔적:**"):
                if not any(line.startswith(mark) for line in lines):
                    problems.append(f"{rel} `{mark}`가 없다")
    n_pb = len(list((root / "playbooks").glob("*.md")))
    n_pr = len(list((root / "principles").glob("*.md")))
    return report("self", problems, f"playbook {n_pb}개, principle {n_pr}개, 라우터 {len(router_text.splitlines())}줄")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("trace")
    t.add_argument("--docs", default="docs")
    t.add_argument("--tests", default="src/test")
    t.add_argument("--no-tests", action="store_true")
    t.set_defaults(fn=cmd_trace)
    k = sub.add_parser("keywords")
    k.add_argument("files", nargs="*")
    k.add_argument("--docs", default="docs")
    k.set_defaults(fn=cmd_keywords)
    j = sub.add_parser("journal")
    j.add_argument("--docs", default="docs")
    j.add_argument("--date")
    j.set_defaults(fn=cmd_journal)
    s = sub.add_parser("self")
    s.set_defaults(fn=cmd_self)
    args = p.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
