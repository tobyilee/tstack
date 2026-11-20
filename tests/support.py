"""검사의 도우미. ADR-0004의 규칙을 확인하는 함수가 여기에 있다.

함수는 저장소의 뿌리를 인자로 받는다. 그래서 테스트가 임시의 폴더에도 돌린다.
표준 라이브러리만 쓴다 (ADR-0004 규칙 2). Python 3.9에서 돈다 (규칙 13).
"""
import ast
import importlib.util
import re
import sys
import sysconfig
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
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
