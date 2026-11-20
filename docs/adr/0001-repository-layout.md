# ADR-0001. 저장소의 구조

- 상태: 승인 (사용자가 결정, 2026-11-20). AI가 제안했다. 사용자가 묶어서 승인했다. 하나씩 보지는 않았다. 규칙마다 "출처"의 열은 제안한 쪽을 그대로 남긴다.

## 이 문서를 읽는 법

요구의 수준의 키워드는 [Spec 01의 "이 문서를 읽는 법"](../spec/01-marketplace.md#이-문서를-읽는-법)을 따른다. 용어는 [Domain 01](../domain/01-marketplace.md)을 따른다.

## 맥락

- 저장소는 마켓플레이스 하나와 플러그인 2개를 가진다 (사용자가 결정, 2026-11-20).
- 설치는 플러그인의 폴더만 복사한다 (확인: Spec 01의 E2).
- 저장소에는 플러그인이 아닌 것도 있다: 설계 문서, 일지, 검사, CI의 설정, 출처의 기록.
- 출처의 가이드(`tstack-guide.md`)는 플러그인의 폴더의 밖에 있었다. 그래서 설치한 사본에 없었다.
- 출처의 eval 사례는 스킬의 폴더의 안에 있었다. `claude plugin eval`은 플러그인의 폴더의 `evals/`를 읽는다 (확인: `claude plugin eval --help`).

## 결정

저장소의 구조는 아래와 같다.

```text
.claude-plugin/marketplace.json
plugins/
  tstack/
    .claude-plugin/plugin.json
    README.md
    GUIDE.md
    LICENSE
    agents/
    skills/
  explain-diff/
    .claude-plugin/plugin.json
    README.md
    LICENSE
    skills/explain-diff/
    evals/
docs/
tests/
scripts/
.github/workflows/
provenance.json
README.md
LICENSE
CLAUDE.md
```

| # | 규칙 | 출처 |
|---|---|---|
| 1 | 플러그인의 폴더는 **반드시** `plugins/<플러그인의 이름>/`에 있어**야 한다**. | AI가 제안. 사용자가 고른 미리보기 2개에 이 모양이 있었다. 질문으로 묻지 않았다. |
| 2 | 플러그인의 폴더가 아닌 것(`docs/`, `tests/`, `scripts/`, `.github/`, `provenance.json`)은 `plugins/`의 밖에 **반드시** 있어**야 한다**. | AI가 제안. |
| 3 | 플러그인 `explain-diff`의 eval 사례는 **반드시** `plugins/explain-diff/evals/`에 있어**야 한다**. | AI가 제안 (브레인스토밍의 Q10). |
| 4 | 가이드는 **반드시** `plugins/tstack/GUIDE.md`에 있어**야 한다**. | 사용자가 결정 (플러그인의 안으로 옮긴다, 2026-11-20). 파일의 이름은 AI가 제안. |
| 5 | 저장소의 뿌리는 `skills/`와 `agents/`를 **절대** 가져**서는 안 된다**. | AI가 제안. |

규칙 5의 이유: 뿌리에 부품이 있으면 저장소 전체가 플러그인 하나로도 읽힌다. 플러그인은 `plugins/`의 아래에만 있다.

## 결과

- 좋은 점: 설치한 사본에 설계 문서와 검사가 들어가지 않는다. 플러그인이 늘어도 모양이 같다.
- 좋은 점: 가이드와 eval 사례가 플러그인과 함께 설치된다.
- 나쁜 점: 설치한 사본이 eval 사례의 파일 40개를 가진다. 사용자는 그 파일을 쓰지 않는다.
- 나쁜 점: 가이드에 trealworld의 기원의 이야기(9절)가 남는다.
- 결정이 유효한 조건: 설치가 플러그인의 폴더만 복사한다. 이 동작이 바뀌면 규칙 2 ~ 4를 다시 본다.

## 버린 대안

| 대안 | 좋은 점 | 버린 이유 |
|---|---|---|
| 플러그인의 폴더를 저장소의 뿌리에 둔다 (`tstack/`, `explain-diff/`). | 경로가 한 단계 짧다. 출처의 경로와 같다. | 뿌리에서 플러그인과 저장소의 폴더가 섞인다. |
| eval 사례를 스킬의 폴더의 안에 그대로 두고 `experimental.evals`로 가리킨다. | 파일을 옮기지 않는다. | `experimental`의 필드에 기댄다. 기본의 위치가 더 단순하다. |
| eval 사례를 저장소의 뿌리에 둔다. | 설치한 사본이 가볍다. | `claude plugin eval`의 폴더는 플러그인의 폴더의 아래여야 한다 (확인: `--eval-dir`의 도움말). |
| 가이드를 저장소의 `docs/`에 둔다. | 플러그인의 내용이 출처와 같게 남는다. | 설치한 사본에 가이드가 없다. 사용자가 이 대안을 고르지 않았다. |
| 가이드를 사용법과 기원의 이야기로 나눈다. | 플러그인이 가볍다. | 가이드를 다시 쓰는 일이다. 사용자가 뒤의 슬라이스로 미뤘다. |
