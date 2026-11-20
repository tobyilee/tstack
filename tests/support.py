"""검사의 도우미. ADR-0004의 규칙을 확인하는 함수가 여기에 있다.

함수는 저장소의 뿌리를 인자로 받는다. 그래서 테스트가 임시의 폴더에도 돌린다.
표준 라이브러리만 쓴다 (ADR-0004 규칙 2). Python 3.9에서 돈다 (규칙 13).
"""
import ast
import importlib.util
import json
import re
import sys
import sysconfig
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))  # 테스트가 scripts/의 모듈을 가져온다 (ADR-0004 규칙 12)
CODE_DIRS = ("tests", "scripts")
CLI_HELPER = "tests/claude_cli.py"
CLI_NAME = "cl" + "aude"          # 이 파일이 규칙 5의 검사에 걸리지 않게 나눠서 쓴다
ID_TOKEN = re.compile(r"^test_(ac\d+_\d+|r\d+|adr\d{4}_\d+)_")
EVAL_IN_TEXT = re.compile(r"\bplugin\s+" + "eval" + r"\b")
EXEMPT_TABLE = "### 테스트가 없는 규칙"
EXEMPT_ROW = re.compile(r"ADR-(\d{4})의 규칙 (\d+)")


def python_files(root):
    """`tests/`와 `scripts/`의 `.py` 파일을 (저장소 기준의 경로, 전체 경로)로 준다."""
    root = Path(root)
    found = []
    for folder in CODE_DIRS:
        for path in sorted((root / folder).rglob("*.py")):
            if "__pycache__" not in path.parts:
                found.append((path.relative_to(root).as_posix(), path))
    return found


def parse(path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


# ---------------------------------------------------------------- 규칙 2

def _is_stdlib(name):
    if name in sys.builtin_module_names:
        return True
    try:
        spec = importlib.util.find_spec(name)
    except (ImportError, ValueError):
        return False
    if spec is None:
        return False
    if spec.origin in ("built-in", "frozen"):
        return True
    if not spec.origin:
        return False
    origin = Path(spec.origin).resolve()
    if "site-packages" in origin.parts or "dist-packages" in origin.parts:
        return False
    paths = sysconfig.get_paths()
    homes = [Path(paths[key]).resolve() for key in ("stdlib", "platstdlib")]
    return any(home == origin or home in origin.parents for home in homes)


def non_stdlib_imports(root):
    """표준 라이브러리도 이웃의 모듈도 아닌 import를 (파일, 모듈)로 준다."""
    root = Path(root)
    local = set()
    for folder in CODE_DIRS:
        base = root / folder
        if base.is_dir():
            local.add(folder)
            local |= {p.stem for p in base.glob("*.py")} | {p.name for p in base.iterdir() if p.is_dir()}
    found = []
    for rel, path in python_files(root):
        for node in ast.walk(parse(path)):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module]
            else:
                continue
            for name in names:
                top = name.split(".")[0]
                if top not in local and not _is_stdlib(top):
                    found.append((rel, top))
    return found


# ---------------------------------------------------------------- 규칙 3

def test_function_names(root):
    """`tests/test_*.py`의 테스트의 함수의 이름을 (파일, 이름)으로 준다. 파일의 안의 순서다."""
    found = []
    for rel, path in python_files(root):
        if not (rel.startswith("tests/") and path.name.startswith("test_")):
            continue
        functions = [
            node for node in ast.walk(parse(path))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test")
        ]
        for node in sorted(functions, key=lambda n: n.lineno):
            found.append((rel, node.name))
    return found


test_function_names.__test__ = False  # unittest가 이 함수를 테스트로 모으지 않는다


def badly_named_tests(root):
    return [(rel, name) for rel, name in test_function_names(root) if not ID_TOKEN.match(name)]


# ---------------------------------------------------------------- 규칙 5

def _strings(tree):
    return [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def direct_cli_calls(root):
    """도우미의 밖에서 CLI의 이름을 글자로 가진 파일을 준다."""
    found = []
    for rel, path in python_files(root):
        if rel == CLI_HELPER:
            continue
        for text in _strings(parse(path)):
            if text == CLI_NAME or text.startswith(CLI_NAME + " "):
                found.append(rel)
                break
    return sorted(found)


# --------------------------------------------------------------- 규칙 11

def _has_eval_args(tree):
    for node in ast.walk(tree):
        if not isinstance(node, (ast.List, ast.Tuple)):
            continue
        values = [e.value if isinstance(e, ast.Constant) else None for e in node.elts]
        for first, second in zip(values, values[1:]):
            if first == "plugin" and second == "eval":
                return True
    return False


def eval_runs(root):
    """플러그인의 eval을 돌리는 파일을 준다: 검사의 코드와 CI의 workflow."""
    root = Path(root)
    found = []
    for rel, path in python_files(root):
        tree = parse(path)
        if _has_eval_args(tree) or any(EVAL_IN_TEXT.search(text) for text in _strings(tree)):
            found.append(rel)
    workflows = root / ".github" / "workflows"
    if workflows.is_dir():
        for path in sorted(workflows.iterdir()):
            if path.suffix in (".yml", ".yaml") and EVAL_IN_TEXT.search(path.read_text(encoding="utf-8")):
                found.append(path.relative_to(root).as_posix())
    return sorted(found)


# --------------------------------------------------------------- 규칙 13

def not_python39(root):
    """Python 3.9의 문법으로 읽히지 않는 파일을 준다. 문법만 본다. 실행은 CI가 한다 (규칙 14)."""
    found = []
    for rel, path in python_files(root):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path), feature_version=(3, 9))
        except SyntaxError:
            found.append(rel)
    return found


# --------------------------------------------------------------- 규칙 15

def adr_rules(root):
    """ADR의 "결정"의 절의 첫 표의 규칙을 (ADR의 번호, 규칙의 번호)로 준다."""
    found = []
    for path in sorted((Path(root) / "docs" / "adr").glob("[0-9][0-9][0-9][0-9]-*.md")):
        in_decision = False
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                in_decision = line.strip() == "## 결정"
            elif line.startswith("### "):
                in_decision = False
            elif in_decision and line.startswith("| "):
                first = line.split("|")[1].strip()
                if first.isdigit():
                    found.append((path.name[:4], int(first)))
    return found


def exempt_adr_rules(root):
    """"테스트가 없는 규칙"의 표에 있는 규칙을 준다."""
    found = set()
    for path in sorted((Path(root) / "docs" / "adr").glob("*.md")):
        in_table = False
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("#"):
                in_table = line.strip() == EXEMPT_TABLE
            elif in_table and line.startswith("| "):
                match = EXEMPT_ROW.search(line.split("|")[1])
                if match:
                    found.add((match.group(1), int(match.group(2))))
    return found


def adr_rules_without_tests(root):
    names = [name for _, name in test_function_names(root)]
    exempt = exempt_adr_rules(root)
    missing = []
    for adr, rule in adr_rules(root):
        token = "test_adr%s_%d_" % (adr, rule)
        if (adr, rule) not in exempt and not any(name.startswith(token) for name in names):
            missing.append("ADR-%s 규칙 %d" % (adr, rule))
    return missing



# --------------------------------------------------------------- ADR-0001

PLUGINS_DIR = "plugins"
NOT_PLUGIN_THINGS = ("docs", "tests", "scripts", ".github", "provenance.json")
EVALS_HOME = "plugins/explain-diff/evals"
GUIDE = "plugins/tstack/GUIDE.md"
OLD_GUIDE_NAME = "tstack-guide.md"
SKIP_DIRS = {".git", "__pycache__"}


def _walk(root):
    """저장소의 파일과 폴더를 준다. `.git`과 `__pycache__`의 안은 보지 않는다."""
    pending = [Path(root)]
    while pending:
        folder = pending.pop()
        for child in sorted(folder.iterdir()):
            if child.name in SKIP_DIRS:
                continue
            yield child
            if child.is_dir() and not child.is_symlink():
                pending.append(child)


def layout_problems(root, plugins=("tstack", "explain-diff")):
    """ADR-0001의 규칙 1 ~ 5를 어긴 곳을 글로 준다. 글은 `ADR-0001 규칙 N:`으로 시작한다."""
    root = Path(root)
    rel = lambda path: path.relative_to(root).as_posix()
    everything = list(_walk(root))
    problems = []

    for name in plugins:
        if not (root / PLUGINS_DIR / name).is_dir():
            problems.append("ADR-0001 규칙 1: 플러그인의 폴더가 없다: %s/%s" % (PLUGINS_DIR, name))
    for path in everything:
        if path.name == "plugin.json" and path.parent.name == ".claude-plugin":
            parts = path.relative_to(root).parts
            if not (len(parts) == 4 and parts[0] == PLUGINS_DIR):
                problems.append("ADR-0001 규칙 1: 플러그인 매니페스트가 plugins/<이름>/의 밖에 있다: %s" % rel(path))

    plugins_dir = root / PLUGINS_DIR
    if plugins_dir.is_dir():
        candidates = [plugins_dir] + [d for d in sorted(plugins_dir.iterdir()) if d.is_dir()]
        for folder in candidates:
            for thing in NOT_PLUGIN_THINGS:
                if (folder / thing).exists():
                    problems.append("ADR-0001 규칙 2: 플러그인의 폴더가 아닌 것이 plugins/의 안에 있다: %s" % rel(folder / thing))

    if not (root / EVALS_HOME).is_dir():
        problems.append("ADR-0001 규칙 3: eval 사례의 폴더가 없다: %s" % EVALS_HOME)
    for path in everything:
        if path.is_dir() and path.name == "evals" and rel(path).startswith(PLUGINS_DIR + "/") and rel(path) != EVALS_HOME:
            problems.append("ADR-0001 규칙 3: evals/가 다른 자리에 있다: %s" % rel(path))

    if not (root / GUIDE).is_file():
        problems.append("ADR-0001 규칙 4: 가이드가 없다: %s" % GUIDE)
    for path in everything:
        if path.is_file() and path.name == OLD_GUIDE_NAME:
            problems.append("ADR-0001 규칙 4: 가이드가 옛 이름으로 있다: %s" % rel(path))

    for name in ("agents", "skills"):
        if (root / name).exists():
            problems.append("ADR-0001 규칙 5: 저장소의 뿌리에 부품의 폴더가 있다: %s" % name)
    return sorted(problems, key=lambda text: (text.split(":")[0], text))


# ----------------------------------------------------------- AC-2.9, R7, R8

def eval_cases(root):
    """eval 사례의 이름을 준다: `plugins/explain-diff/evals/`의 바로 아래의 폴더."""
    home = Path(root) / EVALS_HOME
    if not home.is_dir():
        return []
    return sorted(d.name for d in home.iterdir() if d.is_dir() and d.name not in SKIP_DIRS)


def eval_case_problems(root):
    """R7과 R8을 어긴 eval 사례를 글로 준다."""
    home = Path(root) / EVALS_HOME
    problems = []
    for name in eval_cases(root):
        if not (home / name / "prompt.md").is_file():
            problems.append("R7: eval 사례에 prompt.md가 없다: %s" % name)
        graders = home / name / "graders"
        if not (graders.is_dir() and any(f.suffix == ".md" for f in graders.iterdir() if f.is_file())):
            problems.append("R8: eval 사례의 graders/에 .md 파일이 없다: %s" % name)
    return problems


# ------------------------------------------- 매니페스트: AC-1.x, AC-2.6, R1 ~ R4

MARKETPLACE = ".claude-plugin/marketplace.json"
MARKETPLACE_NAME = "tstack"
VERSION = re.compile(r"^\d+\.\d+\.\d+$")


def read_json(path):
    """JSON 파일을 읽는다. 파일이 없거나 JSON이 아니면 None을 준다."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def plugin_folders(root):
    base = Path(root) / PLUGINS_DIR
    return sorted(d.name for d in base.iterdir() if d.is_dir() and d.name not in SKIP_DIRS) if base.is_dir() else []


def plugin_manifest(root, name):
    return read_json(Path(root) / PLUGINS_DIR / name / ".claude-plugin" / "plugin.json")


def _depends_on(manifest, target):
    for item in manifest.get("dependencies") or []:
        name = item.get("name") if isinstance(item, dict) else str(item)
        if str(name).split("@")[0] == target:
            return True
    return False


def manifest_problems(root, plugins=("tstack", "explain-diff")):
    """마켓플레이스 매니페스트와 플러그인 매니페스트의 문제를 글로 준다. 글은 ID로 시작한다."""
    root = Path(root)
    problems = []
    market = read_json(root / MARKETPLACE)
    if not isinstance(market, dict):
        problems.append("AC-1.1: 마켓플레이스 매니페스트가 없다: %s" % MARKETPLACE)
        market = {}
    elif market.get("name") != MARKETPLACE_NAME:
        problems.append("AC-1.2: 마켓플레이스의 name이 %s이 아니다: %s" % (MARKETPLACE_NAME, market.get("name")))
    entries = [e for e in market.get("plugins") or [] if isinstance(e, dict)]
    names = sorted(str(e.get("name")) for e in entries)
    if market and names != sorted(plugins):
        problems.append("AC-1.3: 플러그인의 목록이 %s의 %d개가 아니다: %s" % (", ".join(plugins), len(plugins), ", ".join(names)))
    folders = plugin_folders(root)
    for entry in entries:
        name = str(entry.get("name"))
        if entry.get("source") != "./%s/%s" % (PLUGINS_DIR, name):
            problems.append("R2: 플러그인의 항목의 source가 ./%s/%s이 아니다: %s" % (PLUGINS_DIR, name, entry.get("source")))
        if "version" in entry:
            problems.append("R4: 플러그인의 항목이 version을 가진다: %s" % name)
        if name not in folders:
            problems.append("R1: 플러그인의 항목에 맞는 플러그인의 폴더가 없다: %s" % name)
    for folder in folders:
        manifest = plugin_manifest(root, folder)
        if not isinstance(manifest, dict):
            problems.append("R1: 플러그인 매니페스트가 없다: %s/%s/.claude-plugin/plugin.json" % (PLUGINS_DIR, folder))
            continue
        if manifest.get("name") != folder:
            problems.append("R1: 플러그인 매니페스트의 name이 폴더의 이름과 다르다: %s/%s (%s)" % (PLUGINS_DIR, folder, manifest.get("name")))
        if market and folder not in names:
            problems.append("R1: 플러그인의 폴더에 맞는 플러그인의 항목이 없다: %s" % folder)
        if "version" not in manifest:
            problems.append("ADR-0003 규칙 1: 플러그인 매니페스트에 version이 없다: %s" % folder)
        elif not isinstance(manifest["version"], str) or not VERSION.match(manifest["version"]):
            problems.append("R3: 버전이 점으로 나눈 숫자 3개가 아니다: %s (%s)" % (folder, manifest["version"]))
        if manifest.get("license") != "MIT":
            problems.append("AC-2.6: 플러그인 매니페스트의 license가 MIT가 아니다: %s (%s)" % (folder, manifest.get("license")))
        if folder == "tstack" and _depends_on(manifest, "explain-diff"):
            problems.append("AC-1.9: 플러그인 tstack이 dependencies로 explain-diff를 요구한다")
    return sorted(problems)


def plugin_components(root, name):
    """플러그인이 제공하는 부품의 이름을 준다: `SKILL.md`가 있는 스킬의 폴더, `agents/`의 `.md` 파일."""
    base = Path(root) / PLUGINS_DIR / name
    skills = sorted(d.name for d in (base / "skills").iterdir() if (d / "SKILL.md").is_file()) if (base / "skills").is_dir() else []
    agents = sorted(f.stem for f in (base / "agents").iterdir() if f.is_file() and f.suffix == ".md") if (base / "agents").is_dir() else []
    return {"skills": skills, "agents": agents}


# ------------------------------------- 라이선스와 README: AC-2.4, AC-2.5, AC-6.1, AC-6.2, R6

COPYRIGHT_LINE = "Copyright (c) 2026 Toby Lee"


def license_problems(root):
    """`LICENSE` 3개와 플러그인의 `README.md`의 문제를 글로 준다."""
    root = Path(root)
    problems = []
    top = root / "LICENSE"
    top_text = top.read_text(encoding="utf-8") if top.is_file() else None
    if top_text is None:
        problems.append("AC-6.1: 저장소의 뿌리에 LICENSE가 없다")
    else:
        lines = top_text.splitlines()
        first = lines[0].strip() if lines else ""
        if first != "MIT License":
            problems.append("AC-6.1: 뿌리의 LICENSE의 첫 줄이 MIT License가 아니다: %s" % first)
        if COPYRIGHT_LINE not in [line.strip() for line in lines]:
            problems.append("AC-6.2: 뿌리의 LICENSE에 저작권의 줄이 없다: %s" % COPYRIGHT_LINE)
    for name in plugin_folders(root):
        folder = root / PLUGINS_DIR / name
        if not (folder / "README.md").is_file():
            problems.append("AC-2.4: 플러그인의 폴더에 README.md가 없다: %s/%s" % (PLUGINS_DIR, name))
        if not (folder / "LICENSE").is_file():
            problems.append("AC-2.5: 플러그인의 폴더에 LICENSE가 없다: %s/%s" % (PLUGINS_DIR, name))
        elif top_text is not None and (folder / "LICENSE").read_text(encoding="utf-8") != top_text:
            problems.append("R6: LICENSE의 내용이 저장소의 뿌리의 것과 다르다: %s/%s/LICENSE" % (PLUGINS_DIR, name))
    return sorted(problems)


# ------------------------------------------ 플러그인의 글: AC-2.1, AC-2.2, AC-2.8, AC-2.10 ~ AC-2.16

SOURCE_REPOSITORY = "https://github.com/tobyilee/trealworld"
SOURCE_COMMIT = "68fc5e24b76724b37dc9cc7e974121ea347c08ed"
INSTALL_COMMANDS = ("/plugin marketplace add tobyilee/tstack", "/plugin install tstack@tstack")
PLUGIN_DIR_COMMAND = CLI_NAME + " --plugin-dir"
INSTALL_DOCS = ("plugins/tstack/GUIDE.md", "plugins/tstack/README.md")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
INLINE_CODE = re.compile(r"`[^`]*`")
# 출처 저장소의 URL: 호스트의 뒤에 tobyilee/trealworld가 온다. 스킴, `git@`, `www.`은 가리지 않는다 (Spec 01의 "읽는 법").
SOURCE_URL = re.compile(
    r"(?:[a-z][a-z0-9+.-]*://)?(?:[\w.-]+@)?(?:www\.)?(?:github\.com|raw\.githubusercontent\.com)[/:]tobyilee/trealworld"
    r"(?![\w-])[^\s)>\"'`]*"
)
SLASH_COMMAND = "/plugin "


def is_pinned(url):
    """고정 URL인가: `https://github.com/tobyilee/trealworld/`로 시작하고 출처 커밋의 전체 해시를 가진다."""
    return url.startswith(SOURCE_REPOSITORY + "/") and SOURCE_COMMIT in url


def crowded_code_blocks(lines):
    """슬래시 명령의 줄이 2개 이상인 코드 블록을 (블록의 첫 줄의 번호, 줄의 수)로 준다. AC-2.16, AC-6.7."""
    found, start, count = [], None, 0
    for number, line in enumerate(lines, 1):
        text = line.lstrip()
        if text.startswith("```"):
            if start is None:
                start, count = number, 0
            else:
                if count >= 2:
                    found.append((start, count))
                start = None
        elif start is not None and text.startswith(SLASH_COMMAND):
            count += 1
    return found


def plugin_text_files(root):
    """플러그인의 폴더의 글의 파일을 (저장소 기준의 경로, 플러그인의 폴더, 줄의 목록)으로 준다."""
    root = Path(root)
    found = []
    for name in plugin_folders(root):
        folder = root / PLUGINS_DIR / name
        for path in sorted(p for p in folder.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            found.append((path.relative_to(root).as_posix(), folder, lines))
    return found


def _links(lines):
    """Markdown의 줄에서 (줄의 번호, 링크의 경로)를 준다. 코드 블록과 글의 안의 코드는 보지 않는다."""
    in_code = False
    for number, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        for match in MD_LINK.finditer(INLINE_CODE.sub("", line)):
            yield number, match.group(1)


def text_problems(root):
    """플러그인의 글의 문제를 글로 준다. 글은 ID로 시작한다."""
    root = Path(root)
    names = plugin_folders(root)
    path_of_plugin = re.compile(r"%s/(%s)(?![\w-])" % (PLUGINS_DIR, "|".join(re.escape(n) for n in names) or "x"))
    problems = []
    for rel, folder, lines in plugin_text_files(root):
        where = lambda number: "%s:%d" % (rel, number)
        if rel.endswith(".md"):
            for number, target in _links(lines):
                if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                    continue
                resolved = (root / rel).parent.joinpath(target.split("#")[0]).resolve()
                home = folder.resolve()
                if resolved != home and home not in resolved.parents:
                    problems.append("AC-2.1: 상대 링크가 플러그인의 폴더의 밖을 가리킨다: %s (%s)" % (where(number), target))
                elif not resolved.exists():
                    problems.append("AC-2.2: 상대 링크가 없는 파일을 가리킨다: %s (%s)" % (where(number), target))
            for start, count in crowded_code_blocks(lines):
                problems.append("AC-2.16: 코드 블록 하나에 슬래시 명령의 줄이 %d개다: %s" % (count, where(start)))
        for number, line in enumerate(lines, 1):
            if ("plugin install" in line or "marketplace add" in line) and "trealworld" in line:
                problems.append("AC-2.8: 설치 명령의 줄이 글자 trealworld를 가진다: %s" % where(number))
            if rel == INSTALL_DOCS[0] and "이 프로젝트" in line:
                problems.append("AC-2.10: 가이드가 글자 `이 프로젝트`를 가진다: %s" % where(number))
            if PLUGIN_DIR_COMMAND in line and not path_of_plugin.search(line):
                problems.append("AC-2.13: `--plugin-dir`의 명령의 줄에 경로 plugins/<플러그인의 이름>이 없다: %s" % where(number))
            words = line.split()
            if rel.endswith(".md") and len(words) >= 2 and words[0] == "python3" and not words[1].startswith("-"):
                if not (root / words[1]).is_file():
                    problems.append("AC-2.15: `python3`의 명령의 줄의 스크립트가 저장소의 뿌리에서 없다: %s (%s)" % (where(number), words[1]))
            for url in SOURCE_URL.findall(line):
                if not is_pinned(url):
                    problems.append("AC-2.14: 출처 저장소의 URL이 고정 URL이 아니다: %s (%s)" % (where(number), url.rstrip(".,")))
        if rel in INSTALL_DOCS:
            text = "\n".join(lines)
            for command in INSTALL_COMMANDS:
                if command not in text:
                    problems.append("AC-2.11: 설치 명령이 없다: %s (%s)" % (rel, command))
            if PLUGIN_DIR_COMMAND not in text:
                problems.append("AC-2.12: `claude --plugin-dir`의 명령이 없다: %s" % rel)
    return sorted(problems)


# ------------------------------------------------------------------ AC-4.4

def first_code_block(text):
    """Markdown의 첫 코드 블록의 내용을 준다. 울타리의 줄은 뺀다."""
    lines, inside = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            if inside:
                break
            inside = True
            continue
        if inside:
            lines.append(line)
    return "\n".join(lines) + ("\n" if lines else "")



# ------------------------------------------------------------ ADR-0004 규칙 1, 4

def _test_files(root):
    return [(rel, path) for rel, path in python_files(root) if rel.startswith("tests/") and path.name.startswith("test_")]


def _is_test(node):
    return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test")


def tests_outside_testcase(root):
    """`unittest.TestCase`의 메서드가 아닌 테스트를 (파일, 이름)으로 준다. ADR-0004 규칙 1."""
    found = []
    for rel, path in _test_files(root):
        tree = parse(path)
        classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}

        def is_testcase(cls, seen=()):
            for base in cls.bases:
                name = base.attr if isinstance(base, ast.Attribute) else getattr(base, "id", "")
                if name == "TestCase":
                    return True
                if name in classes and name not in seen and is_testcase(classes[name], seen + (name,)):
                    return True
            return False

        good = set()
        for cls in classes.values():
            if is_testcase(cls):
                good |= {id(node) for node in cls.body if _is_test(node)}
        for node in sorted((n for n in ast.walk(tree) if _is_test(n)), key=lambda n: n.lineno):
            if id(node) not in good:
                found.append((rel, node.name))
    return found


def id_of_test(name):
    """테스트의 이름의 ID의 표지를 문서의 ID로 바꾼다: `test_ac1_10_x` → `AC-1.10`."""
    match = re.match(r"^test_(?:ac(\d+)_(\d+)|r(\d+)|adr(\d{4})_(\d+))_", name)
    if not match:
        return None
    goal, number, rule, adr, adr_rule = match.groups()
    if goal:
        return "AC-%s.%s" % (goal, number)
    if rule:
        return "R%s" % rule
    return "ADR-%s 규칙 %s" % (adr, adr_rule)


def tests_without_id_message(root):
    """자기의 ID를 글로 가지지 않은 테스트를 (파일, 이름, ID)로 준다. ADR-0004 규칙 4.

    테스트의 함수의 안의 글자의 상수에 ID가 있어야 한다. ID의 뒤에 숫자가 이어지면 다른 ID다.
    """
    found = []
    for rel, path in _test_files(root):
        for node in sorted((n for n in ast.walk(parse(path)) if _is_test(n)), key=lambda n: n.lineno):
            wanted = id_of_test(node.name)
            if wanted is None:
                continue
            pattern = re.compile(re.escape(wanted) + r"(?!\d)")
            if not any(pattern.search(text) for text in _strings(node)):
                found.append((rel, node.name, wanted))
    return found


# ------------------------------------------------------- 뿌리의 README: AC-6.3 ~ AC-6.7

ENGLISH_HEADING = "## English"
ROOT_INSTALL_COMMANDS = INSTALL_COMMANDS + ("/plugin install explain-diff@tstack",)
ROOT_LOCAL_COMMAND = PLUGIN_DIR_COMMAND + " ./plugins/tstack"


def split_readme(text):
    """README를 (영어의 절, 한국어의 본문)으로 나눈다. 영어의 절이 없으면 (None, 전체)다."""
    english, korean, inside, seen = [], [], False, False
    for line in text.splitlines():
        if line.strip() == ENGLISH_HEADING:
            inside, seen = True, True
            continue
        if inside and line.startswith("## "):
            inside = False
        (english if inside else korean).append(line)
    return ("\n".join(english) if seen else None), "\n".join(korean)


def readme_problems(root):
    path = Path(root) / "README.md"
    if not path.is_file():
        return ["AC-6.3: 저장소의 뿌리에 README.md가 없다"]
    text = path.read_text(encoding="utf-8")
    english, korean = split_readme(text)
    problems = []
    for start, count in crowded_code_blocks(text.splitlines()):
        problems.append("AC-6.7: 뿌리의 README.md의 코드 블록 하나에 슬래시 명령의 줄이 %d개다: README.md:%d" % (count, start))
    if english is None:
        problems.append("AC-6.3: 뿌리의 README.md에 머리가 `%s`인 절이 없다" % ENGLISH_HEADING)
    for command in ROOT_INSTALL_COMMANDS:
        if english is not None and command not in english:
            problems.append("AC-6.4: `%s`의 절에 설치 명령이 없다: %s" % (ENGLISH_HEADING, command))
        if command not in korean:
            problems.append("AC-6.5: 한국어의 본문에 설치 명령이 없다: %s" % command)
    if ROOT_LOCAL_COMMAND not in korean:
        problems.append("AC-6.6: 한국어의 본문에 명령이 없다: %s" % ROOT_LOCAL_COMMAND)
    return sorted(problems)


# ------------------------------------------------------ CI: ADR-0004 규칙 8, 9, 10, 14

WORKFLOW = ".github/workflows/check.yml"


def remote_enabled(env):
    """GitHub에서 설치하는 테스트를 돌리는가. ADR-0004 규칙 10."""
    return env.get("TSTACK_REMOTE") == "1"


def workflow_problems(root):
    """CI의 workflow의 문제를 글로 준다. YAML을 글자로 본다 (표준 라이브러리에 YAML의 모듈이 없다)."""
    path = Path(root) / WORKFLOW
    if not path.is_file():
        return ["ADR-0004 규칙 8: CI의 workflow가 없다: %s" % WORKFLOW]
    text = path.read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines() if not line.strip().startswith("#")]
    problems = []
    for trigger in ("push", "pull_request"):
        if trigger + ":" not in lines:
            problems.append("ADR-0004 규칙 8: %s에서 돌지 않는다" % trigger)
    checkouts = sum(1 for line in lines if "actions/checkout@" in line)
    if checkouts == 0 or lines.count("fetch-depth: 0") != checkouts:
        problems.append("ADR-0004 규칙 8: 역사와 태그를 모두 받지 않는다 (fetch-depth: 0이 checkout마다 있어야 한다)")
    if not any("unittest discover -s tests" in line and "-p " not in line for line in lines):
        problems.append("ADR-0004 규칙 8: 검사를 모두 돌리지 않는다 (unittest discover -s tests)")
    if not any("tstack-check.py trace --tests tests" in line for line in lines):
        problems.append("ADR-0004 규칙 9: `trace --tests tests`를 돌리지 않는다")
    if not any("tstack-check.py keywords" in line for line in lines):
        problems.append("ADR-0004 규칙 9: `keywords`를 돌리지 않는다")
    if not any(re.match(r"^TSTACK_REMOTE:\s*[\"']?1[\"']?$", line) for line in lines):
        problems.append("ADR-0004 규칙 10: 환경 변수 TSTACK_REMOTE를 1로 주지 않는다")
    for condition in ("github.event_name == 'push'", "github.ref == 'refs/heads/main'"):
        if not any(line.startswith("if:") and condition in line for line in lines):
            problems.append("ADR-0004 규칙 10: `main`의 push의 조건이 없다: %s" % condition)
    matrix = " ".join(line for line in lines if line.startswith("python-version:") and "[" in line)
    for version in ("3.9", "3.x"):
        if '"%s"' % version not in matrix:
            problems.append("ADR-0004 규칙 14: Python의 버전 %s가 없다" % version)
    return sorted(problems)
