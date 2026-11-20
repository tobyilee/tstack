"""Claude Code의 CLI를 부르는 유일한 자리다.

ADR-0004 규칙 5: CLI를 부르는 테스트는 격리된 설정 폴더에서 돈다.
ADR-0004 규칙 6: 검사는 사용자의 설정 폴더를 바꾸지 않는다.
다른 파일은 CLI를 직접 부르지 않는다. 이 파일의 `run_claude`를 쓴다.
"""
import os
import subprocess
from pathlib import Path

CLAUDE = "claude"
CONFIG_VAR = "CLAUDE_CONFIG_DIR"


def user_config_dirs(base_env):
    """사용자의 설정 폴더를 준다: `~/.claude`와, 이미 쓰고 있는 설정 폴더."""
    found = [(Path.home() / ".claude").resolve()]
    ambient = base_env.get(CONFIG_VAR)
    if ambient:
        found.append(Path(ambient).resolve())
    return found


def isolated_env(config_dir, base_env=None):
    """CLI에 줄 환경 변수를 새 dict로 만든다. 사용자의 설정 폴더는 거부한다."""
    base = dict(os.environ if base_env is None else base_env)
    if config_dir is None or str(config_dir) == "":
        raise ValueError("ADR-0004 규칙 5: 격리된 설정 폴더가 없다. 임시 폴더의 경로를 준다")
    target = Path(config_dir).resolve()
    for user_dir in user_config_dirs(base):
        if target == user_dir or user_dir in target.parents:
            raise ValueError("ADR-0004 규칙 6: %s 는 사용자의 설정 폴더(%s)다. 임시 폴더를 쓴다" % (target, user_dir))
    base[CONFIG_VAR] = str(target)
    return base


def run_claude(args, config_dir, cwd=None, timeout=300):
    """격리된 설정 폴더에서 CLI를 돌린다. 끝의 코드와 출력을 가진 결과를 준다."""
    return subprocess.run(
        [CLAUDE] + list(args), env=isolated_env(config_dir), cwd=cwd,
        capture_output=True, text=True, timeout=timeout,
    )
