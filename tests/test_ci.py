"""CI의 workflow를 검사한다. ADR-0004의 규칙 8, 9, 10, 14.

workflow는 YAML이다. 표준 라이브러리에는 YAML을 읽는 모듈이 없다 (ADR-0004 규칙 2).
그래서 글자로 본다. workflow가 실제로 도는지는 push의 뒤에 GitHub Actions에서 본다.
"""
import tempfile
import unittest
from pathlib import Path

import support

ROOT = support.ROOT
GOOD = """name: check
on:
  push:
  pull_request:
jobs:
  check:
    strategy:
      matrix:
        python-version: ["3.9", "3.x"]
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0
      - run: python -m unittest discover -s tests -v
      - run: python plugins/tstack/skills/t-mode/scripts/tstack-check.py trace --tests tests
      - run: python plugins/tstack/skills/t-mode/scripts/tstack-check.py keywords
  remote-install:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0
      - env:
          TSTACK_REMOTE: "1"
        run: python -m unittest discover -s tests -p test_remote.py -v
"""


def only(problems, prefix):
    return [p for p in problems if p.startswith(prefix)]


def problems_of(text):
    with tempfile.TemporaryDirectory() as tmp:
        if text is not None:
            path = Path(tmp) / ".github" / "workflows" / "check.yml"
            path.parent.mkdir(parents=True)
            path.write_text(text, encoding="utf-8")
        return support.workflow_problems(Path(tmp))


class Workflow(unittest.TestCase):
    def check(self, prefix):
        found = only(support.workflow_problems(ROOT), prefix)
        self.assertEqual([], found, "%s CI의 workflow가 규칙을 어긴다: %s" % (prefix, found))

    def test_adr0004_8_ci_runs_every_check_on_push_and_pull_request(self):
        self.check("ADR-0004 규칙 8:")

    def test_adr0004_9_ci_runs_trace_and_keywords(self):
        self.check("ADR-0004 규칙 9:")

    def test_adr0004_10_ci_runs_the_remote_install_after_a_push_to_main(self):
        self.check("ADR-0004 규칙 10:")

    def test_adr0004_14_ci_runs_on_two_python_versions(self):
        self.check("ADR-0004 규칙 14:")

    def test_adr0004_8_checker_accepts_a_good_workflow_and_finds_a_missing_one(self):
        self.assertEqual([], problems_of(GOOD), "ADR-0004 규칙 8: 맞는 workflow에는 문제가 없다")
        self.assertEqual(["ADR-0004 규칙 8: CI의 workflow가 없다: .github/workflows/check.yml"], problems_of(None))

    def test_adr0004_8_checker_finds_every_workflow_problem(self):
        bad = (
            GOOD.replace("  pull_request:\n", "")
            .replace("          fetch-depth: 0\n", "          fetch-depth: 1\n")
            .replace("trace --tests tests", "trace")
            .replace("      - run: python plugins/tstack/skills/t-mode/scripts/tstack-check.py keywords\n", "")
            .replace('["3.9", "3.x"]', '["3.x"]')
            .replace("    if: github.event_name == 'push' && github.ref == 'refs/heads/main'\n", "")
            .replace('          TSTACK_REMOTE: "1"\n', "")
        )
        self.assertEqual(
            [
                "ADR-0004 규칙 10: `main`의 push의 조건이 없다: github.event_name == 'push'",
                "ADR-0004 규칙 10: `main`의 push의 조건이 없다: github.ref == 'refs/heads/main'",
                "ADR-0004 규칙 10: 환경 변수 TSTACK_REMOTE를 1로 주지 않는다",
                "ADR-0004 규칙 14: Python의 버전 3.9가 없다",
                "ADR-0004 규칙 8: pull_request에서 돌지 않는다",
                "ADR-0004 규칙 8: 역사와 태그를 모두 받지 않는다 (fetch-depth: 0이 checkout마다 있어야 한다)",
                "ADR-0004 규칙 9: `keywords`를 돌리지 않는다",
                "ADR-0004 규칙 9: `trace --tests tests`를 돌리지 않는다",
            ],
            problems_of(bad),
            "ADR-0004 규칙 8: 검사가 틀린 workflow의 문제 8개를 모두 찾아야 한다",
        )

    def test_adr0004_10_remote_test_runs_only_when_asked(self):
        self.assertTrue(support.remote_enabled({"TSTACK_REMOTE": "1"}), "ADR-0004 규칙 10: TSTACK_REMOTE가 1이면 돈다")
        for env in ({}, {"TSTACK_REMOTE": "0"}, {"TSTACK_REMOTE": ""}, {"CI": "true"}):
            self.assertFalse(support.remote_enabled(env), "ADR-0004 규칙 10: %r 에서는 돌지 않는다" % (env,))


if __name__ == "__main__":
    unittest.main()
