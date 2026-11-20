# tstack

Claude Code의 플러그인 마켓플레이스다. 플러그인 2개가 있다: 문서를 먼저 쓰는 개발 워크플로 **tstack**과, diff를 학습 문서로 바꾸는 스킬 **explain-diff**.

## English

This repository is a Claude Code plugin marketplace. It has 2 plugins.

| Plugin | What it does | Language |
|---|---|---|
| `tstack` | A development workflow: write the documents first (spec, domain, ADR, plan), write the tests first, and write a journal entry for each step. | Korean |
| `explain-diff` | Turns a diff, commit, branch, or pull request into one self-contained HTML learning document with a recall quiz. | English |

Install. Run these commands in a Claude Code session:

```text
/plugin marketplace add tobyilee/tstack
/plugin install tstack@tstack
/plugin install explain-diff@tstack
```

You can install only one plugin. `tstack` works without `explain-diff`.

The rest of this page is in Korean. The `explain-diff` plugin has an English [README](plugins/explain-diff/README.md).

License: MIT.

## 플러그인

| 플러그인 | 하는 일 | 부르는 방법 | 문서 |
|---|---|---|---|
| `tstack` | 문서를 먼저 쓰고(브레인스토밍 → spec → domain → ADR → plan), 테스트를 먼저 쓰고, 스텝마다 일지를 쓴다. 한 번에 한 스텝만 한다. | `/tstack:t-mode <목표>` | [README](plugins/tstack/README.md), [가이드](plugins/tstack/GUIDE.md) |
| `explain-diff` | diff, 커밋, 가지, PR을 HTML 학습 문서 하나로 바꾼다: 배경, 핵심의 생각, 논리의 순서의 diff, 확인의 퀴즈. | `/explain-diff:explain-diff` | [README](plugins/explain-diff/README.md) |

tstack의 리뷰의 단계는 explain-diff가 있으면 설명 문서를 만든다. 없으면 그 단계를 건너뛴다. 그래서 둘은 따로 설치한다.

## 설치

Claude Code의 세션에서 아래의 명령을 돌린다. 첫 줄은 마켓플레이스를 등록한다. 둘째와 셋째 줄은 플러그인을 설치한다. 하나만 설치해도 된다.

```text
/plugin marketplace add tobyilee/tstack
/plugin install tstack@tstack
/plugin install explain-diff@tstack
```

셸에서는 같은 명령을 `claude plugin`으로 돌린다 (`claude plugin marketplace add tobyilee/tstack`).

설치의 이름의 `@`의 뒤는 마켓플레이스의 이름이다. 저장소의 이름과 글자는 같지만 다른 것이다.

## 업데이트

플러그인마다 버전이 있다 (`plugins/<이름>/.claude-plugin/plugin.json`의 `version`). 버전이 오르면 업데이트가 온다. 버전이 같으면 설치한 사본이 그대로다.

셸에서 마켓플레이스를 새로 받고 플러그인을 업데이트한다. 업데이트의 뒤에 Claude Code를 다시 시작한다.

```text
claude plugin marketplace update tstack
claude plugin update tstack@tstack
claude plugin update explain-diff@tstack
```

## 로컬의 변경을 바로 적용하기

플러그인의 파일을 고치면서 쓰려면 저장소를 받고, 설치하지 않고 플러그인의 폴더를 바로 올린다. Claude Code가 그 폴더를 그 자리에서 읽는다. 고친 것이 다음 세션에 적용된다.

```text
git clone https://github.com/tobyilee/tstack.git
cd tstack
claude --plugin-dir ./plugins/tstack
```

explain-diff는 `./plugins/explain-diff`를 준다. `--plugin-dir`를 두 번 쓰면 둘 다 올린다.

설치한 사본(Claude Code의 설정 폴더의 `plugins/cache/`의 아래)을 고치지 않는다. 다음 업데이트가 그 수정을 지운다.

## 저장소의 구조

```text
.claude-plugin/marketplace.json   마켓플레이스의 이름과 플러그인의 목록
plugins/
  tstack/                         플러그인. 설치는 이 폴더만 복사한다
  explain-diff/                   플러그인. 설치는 이 폴더만 복사한다
docs/                             이 저장소의 설계 문서와 일지 (설치에 들어가지 않는다)
tests/  scripts/                  검사 (설치에 들어가지 않는다)
provenance.json                   옮긴 파일 78개의 출처의 기록
```

## 검사

검사는 Python 3.9 이상의 표준 라이브러리만 쓴다.

```text
python3 -m unittest discover -s tests
python3 scripts/version_check.py
```

Claude Code의 CLI가 `PATH`에 있으면 검사가 `claude plugin validate --strict`와 설치를 돌린다. 임시의 설정 폴더에서 돌린다. 사용자의 설정은 바뀌지 않는다. CLI가 없으면 그 테스트를 건너뛴다.

## 출처

두 플러그인은 [trealworld](https://github.com/tobyilee/trealworld/tree/68fc5e24b76724b37dc9cc7e974121ea347c08ed) 프로젝트에서 나왔다. 그 저장소의 커밋 `68fc5e2`의 파일 78개를 옮겼고, 18개를 고쳤다. `provenance.json`이 파일마다 출처의 경로와 고친 이유를 적는다.

tstack의 구조는 Lauren Tan의 pstack의 원리를 따른다.

## 라이선스

MIT. [LICENSE](LICENSE)를 본다.
