# 00. 킥오프 브레인스토밍

- 작성일: 2026-11-20
- 상태: 초안. 결정 8개를 적었다 (6.1 ~ 6.8, 사용자가 결정, 2026-11-20). 열린 질문 7개(Q9 ~ Q15)와 새 질문 8개(6.9)가 남았다.
  - 수정 (2026-11-20): 설계 문서가 질문 15개를 닫았다. 답과 출처를 6.11에 더했다. 5절과 6.9의 "열렸다"는 그때의 기록이다. 지우지 않았다.
- 입력 자료:
  - tstack 플러그인: <https://github.com/tobyilee/trealworld>의 `tstack/`. 마지막으로 바뀐 커밋은 `ae74146` (2026-11-17)이다.
  - explain-diff 스킬: 같은 저장소의 `.claude/skills/explain-diff/`. 마지막으로 바뀐 커밋은 `68fc5e2` (2026-11-19)이다.
  - 마켓플레이스의 매니페스트: 같은 저장소의 `.claude-plugin/marketplace.json`.
  - 읽은 버전: 저장소의 HEAD `68fc5e2`. 아래의 경로는 이 저장소 안의 경로다.
  - Claude Code의 문서: <https://code.claude.com/docs/en/plugins/> 아래의 `marketplace-reference`, `loading`, `install`, `components`, `dependencies`와 <https://code.claude.com/docs/en/plugin-evals.md>, <https://code.claude.com/docs/en/skills.md>. 2026-11-20에 subagent가 읽었다.
  - Claude Code CLI 2.1.329의 `claude plugin` 도움말과 `claude plugin validate`의 출력.

## 이 문서를 읽는 법

- 이 문서는 요구를 정하지 않는다. 모르는 것을 찾고 질문을 닫는다. 요구는 spec과 ADR이 정한다.
- 사실의 라벨은 넷이다. **확인**: 명령을 실행해서 봤다. **읽음**: 파일을 읽었다. **읽음 (agent)**: subagent가 문서를 읽고 보고했다. 내가 그 문서를 직접 읽지 않았다. **추정**: 확인하지 않았다.

## 1. 읽은 사실

### 1.1 입력 자료

| # | 사실 | 라벨 |
|---|---|---|
| F1 | tstack 플러그인은 파일 34개다. 스킬 2개(`t-mode`, `t-reflect`), agent 1개(`t-reviewer`), Python 스크립트 1개(`tstack-check.py`)가 있다. `plugin.json`의 `version`은 `0.1.0`이다. | 확인 (`git ls-files`, `claude plugin validate`) |
| F2 | `claude plugin validate`가 tstack의 매니페스트를 통과시킨다. 이름은 `tstack:t-mode`, `tstack:t-reflect`, `tstack:t-reviewer`로 나온다. | 확인 |
| F3 | 같은 명령의 "plugin directory" 검사는 문제 1개와 경고 1개를 낸다. 문제: 라이선스가 없다 (`LICENSE_MISSING`). 경고: 아이콘이 없다 (`ICON_MISSING`). | 확인 |
| F4 | trealworld 저장소에 마켓플레이스의 매니페스트가 이미 있다. 이름은 `trealworld`이고 플러그인은 `tstack` 하나다 (`"source": "./tstack"`). 검증을 통과한다. | 확인 |
| F5 | 이 컴퓨터에 tstack은 설치되어 있지 않다. 지금의 세션은 `--plugin-dir ../trealworld/tstack`으로 tstack을 올렸다. | 확인 (`claude plugin list`, 프로세스의 인자) |
| F6 | explain-diff는 플러그인이 아니고 프로젝트의 스킬이다. 파일 43개다: `SKILL.md` (121줄), `assets/template.html` (274줄), `references/widgets.md` (36줄), `evals/`의 사례 3개. 스킬의 글은 영어다. | 확인 (`git ls-files`), 읽음 |
| F7 | explain-diff의 eval 사례는 `case.yaml` (`schema_version: "1.1"`), `prompt.md`, `graders/*.md`, `place-files.sh`, `files/*.diff`로 되어 있다. 위치는 스킬의 폴더의 안이다 (`skills/explain-diff/evals/`). | 읽음 |
| F8 | tstack은 explain-diff를 이름으로만 부른다. `playbooks/review.md`의 5번: "`explain-diff` 스킬이 있으면 설명 문서를 만든다. 스킬이 없으면 `skip`으로 남긴다." `tstack-guide.md`의 9.4는 이것을 의도한 선택으로 적는다 ("내용을 복사하지 않는다"). explain-diff는 tstack을 부르지 않는다. | 읽음 |
| F9 | tstack의 `README.md`는 플러그인의 밖의 파일을 가리킨다 (`../tstack-guide.md`). 설치 명령에 `tobyilee/trealworld`가 들어 있다. | 읽음 |
| F10 | `tstack-guide.md`는 356줄이다. trealworld의 일지 57스텝에서 tstack이 나온 과정을 설명한다 (9절). 같은 설치 명령과 trealworld의 파일의 지도가 들어 있다. | 읽음 |
| F11 | explain-diff의 `template.html`은 밖의 스타일시트 2개를 부른다: jsdelivr의 Pretendard, Google Fonts의 JetBrains Mono. `SKILL.md`는 이 디자인을 "the user's house style"이라고 부른다. | 읽음 |
| F12 | trealworld에 explain-diff의 사본이 하나 더 있다: `.agents/skills/explain-diff/`. git이 추적하지 않는다. `SKILL.md`의 45번 줄의 낱말 하나만 다르다 (`AGENTS.md` ↔ `CLAUDE.md`). | 확인 (`diff -rq`) |
| F13 | git의 역사에서 `tstack/`을 바꾼 커밋은 1개다. `.claude/skills/explain-diff/`를 바꾼 커밋도 1개다. | 확인 (`git log -- <경로>`) |
| F14 | `tstack-check.py`의 `self`는 스크립트의 위치에서 스킬의 폴더를 찾는다. `journal`은 git 저장소와 `docs/journal/`을 요구한다. 스크립트는 Python 3의 표준 라이브러리만 쓴다. | 읽음 |
| F15 | 새 프로젝트의 폴더는 비어 있었다. git 저장소가 아니다. `gh`는 `tobyilee` 계정으로 로그인되어 있다. | 확인 |

### 1.2 Claude Code의 규칙

D1 ~ D10은 subagent의 보고다. 나는 그 문서를 직접 읽지 않았다. CLI의 도움말로 다시 본 것에는 "확인"을 더했다.

| # | 사실 | 라벨 |
|---|---|---|
| D1 | 마켓플레이스의 매니페스트는 저장소의 `.claude-plugin/marketplace.json`에 둔다. 필수 필드는 `name`, `owner`, `plugins`다. 플러그인의 항목의 필수 필드는 `name`, `source`다. | 읽음 (agent). F4의 매니페스트가 이 모양으로 검증을 통과한다 (확인) |
| D2 | 쓰지 못하는 마켓플레이스의 이름이 있다: `claude-plugins-official`, `anthropic-plugins`, `agent-skills`, `claude-code-plugins`, `claudeai-`로 시작하는 이름, `inline`, `builtin`, `skills-dir`, `synced`. | 읽음 (agent) |
| D3 | 설치는 플러그인의 폴더만 캐시에 복사한다. 폴더의 밖의 파일은 복사하지 않는다. `../`로 나가는 경로는 거부된다. | 읽음 (agent) |
| D4 | 버전의 순서: `plugin.json`의 `version` → 마켓플레이스의 항목의 `version` → git 커밋의 SHA. `plugin.json`이 `version`을 고정하면, 그 글자가 바뀔 때까지 사용자는 캐시의 사본을 쓴다. | 읽음 (agent) |
| D5 | 플러그인의 스킬의 이름은 `/<플러그인>:<스킬>`이다. 접두사를 빼는 방법은 문서에 없다. 플러그인의 agent의 이름은 `<플러그인>:<이름>`이다. | 읽음 (agent). F2의 출력이 같은 모양이다 (확인) |
| D6 | 소스의 폴더에 `plugin.json`이 없으면 마켓플레이스의 항목이 매니페스트가 된다. 항목의 `skills: [...]`로 스킬의 폴더를 가리킨다. | 읽음 (agent) |
| D7 | 설치 명령은 두 가지다. (1) `/plugin marketplace add <owner>/<repo>` 뒤에 `/plugin install <플러그인>@<마켓플레이스의 이름>`. (2) `/plugin install <플러그인> --marketplace <owner>/<repo>`. (2)는 Claude Code 2.1.275 이상을 요구한다. 마켓플레이스의 이름은 저장소의 이름이 아니고 매니페스트의 `name`이다. | 읽음 (agent). `--marketplace`의 옵션이 CLI 2.1.329의 도움말에 있다 (확인) |
| D8 | `claude plugin eval`은 플러그인의 뿌리의 `evals/`를 읽는다. 다른 폴더는 `plugin.json`의 `experimental.evals`나 `--eval-dir`로 가리킨다. 스킬의 폴더의 안의 `evals/`는 문서에 없다. | 읽음 (agent). 기본 폴더와 두 옵션이 CLI의 도움말에 있다 (확인) |
| D9 | 플러그인은 `dependencies`로 다른 플러그인을 요구한다. 이름만 쓰면 같은 마켓플레이스에서 찾는다. | 읽음 (agent) |
| D10 | 프로젝트는 `.claude/settings.json`의 `extraKnownMarketplaces`와 `enabledPlugins`로 마켓플레이스와 플러그인을 등록한다. | 읽음 (agent). 이 컴퓨터의 사용자 설정이 같은 모양이다 (확인) |
| D11 | `claude plugin tag`는 `{name}--v{version}`의 git 태그를 만든다. `plugin.json`과 마켓플레이스의 항목의 버전이 같은지 검사한다. | 확인 (CLI의 도움말) |

## 2. 의도의 가설

**검증하지 않은 추측이다.** 요청의 문장과 1절의 사실에서 뽑았다.

| # | 가설 | 근거 | 반례나 약한 곳 |
|---|---|---|---|
| H1 | 목적은 trealworld의 밖에서 다시 쓰는 것이다. 다른 프로젝트와 다른 사람이 설치한다. | 요청: "github에 … 설치해서 사용할 수 있는". | 독자가 누구인지 요청에 없다. 본인만 쓰는 것과 공개하는 것은 요구가 다르다 (라이선스, 언어, 밖의 폰트). |
| H2 | 새 저장소가 원본이 된다. trealworld는 원본을 설치해서 쓰는 쪽이 된다. | 원본이 둘이면 내용이 갈라진다. F12가 이미 갈라진 사본이다. | trealworld의 가이드는 tstack을 "이 프로젝트의 일지에서 뽑은" 것으로 적는다. `t-reflect`는 일지를 읽고 tstack의 파일을 고친다. 일지는 trealworld에 있다. |
| H3 | tstack과 explain-diff는 따로 설치하는 두 부품으로 남는다. | F8: 이름으로만 부르고, 없으면 `skip`이다. explain-diff는 영어이고 tstack이 없어도 동작한다. | 요청의 "모아서"는 플러그인 하나로 합친다는 뜻으로도 읽힌다. |
| H4 | 이 저장소의 개발도 tstack의 방식으로 한다 (문서 먼저, 일지). | 요청이 `/tstack:t-mode`의 킥오프로 왔다. | 이 저장소의 산출물은 대부분 글과 JSON이다. "테스트를 먼저"가 무엇인지 정하지 않았다 (G9). |
| H5 | 저장소의 이름은 `tstack`이다. | 작업 폴더의 이름이 `tstack`이다. | 마켓플레이스의 이름도 `tstack`이면 설치의 이름이 `tstack@tstack`이 된다. 플러그인이 늘면 저장소의 이름이 내용보다 좁다. |
| H6 | 앞으로 플러그인이나 스킬이 더 들어온다. | 마켓플레이스의 형식을 골랐다. 플러그인 하나만 배포하면 형식이 더 단순하다. | 요청은 두 개만 말한다. |

## 3. 빈칸

입력 자료가 말하지 않는 것이다.

| # | 빈칸 | 왜 중요한가 |
|---|---|---|
| G1 | **설치한 플러그인은 캐시의 사본이다 (D3). `t-reflect`는 tstack의 파일을 고친다.** 캐시의 사본을 고치면 다음 업데이트에서 사라진다. | 회고의 결과를 원본에 넣는 길이 필요하다. 지금은 trealworld의 안에 원본이 있어서 문제가 없다. |
| G2 | explain-diff가 플러그인에 들어가면 이름이 `<플러그인>:explain-diff`가 된다 (D5). `review.md`는 "`explain-diff` 스킬"이라고만 쓴다. | 모델이 접두사가 붙은 스킬을 같은 것으로 찾는가. 추정: 찾는다. 확인하지 않았다. |
| G3 | explain-diff의 `evals/`는 스킬의 폴더의 안에 있다 (F7). `claude plugin eval`은 플러그인의 뿌리의 `evals/`를 읽는다 (D8). | 옮기거나 `experimental.evals`로 가리켜야 eval이 돈다. 설치에 eval을 넣을지도 정해야 한다 (43개 중 40개가 eval의 파일이다). |
| G4 | 버전의 정책이 없다. `0.1.0`이 고정되어 있다 (F1, D4). | 버전을 올리지 않고 push하면 사용자는 바뀐 것을 받지 못한다. |
| G5 | `tstack-guide.md`의 자리가 없다 (F9, F10). | 플러그인의 밖에 두면 설치에 들어가지 않는다 (D3). 안에 두면 trealworld의 이야기가 함께 간다. |
| G6 | 라이선스가 없다 (F3). | 공개하는 저장소에 라이선스가 없으면 다른 사람은 쓸 권리가 없다. |
| G7 | explain-diff의 문서는 밖의 폰트를 부른다 (F11). | 네트워크가 없는 곳에서는 대체 글꼴로 나온다. "house style"이 다른 사용자에게도 기본인지 정하지 않았다. |
| G8 | 언어가 섞여 있다. tstack은 한국어이고 explain-diff는 영어다. 저장소의 README의 언어를 정하지 않았다. | 독자가 정한다 (H1). |
| G9 | "설치해서 쓸 수 있다"를 무엇으로 검증하는지 정하지 않았다. | 실제의 표면은 GitHub에서 설치한 뒤의 세션이다. push의 뒤에만 보인다. push의 전에는 `claude plugin validate`와 로컬 경로의 마켓플레이스로 본다. |
| G10 | Claude Code가 아닌 도구의 지원을 정하지 않았다. F12는 다른 도구를 위한 사본으로 보인다 (추정). | 범위가 커진다. |
| G11 | trealworld의 `.claude/hooks/guard-git-discard.py`는 요청에 없다. tstack의 방식의 일부인지 모른다. | 요청은 두 개만 말한다. 넣지 않는 것으로 본다. |
| G12 | 요구하는 Claude Code의 최소 버전을 정하지 않았다 (D7: 2.1.275). | README의 설치 명령이 버전에 따라 다르다. |

## 4. 아이디어

| # | 아이디어 | 좋은 점 | 나쁜 점 |
|---|---|---|---|
| I1 | 플러그인 2개를 둔다: `tstack`, `explain-diff`. 마켓플레이스 하나가 둘을 가진다. | F8의 느슨한 연결을 그대로 둔다. explain-diff만 설치하는 사람이 tstack을 받지 않는다. eval이 플러그인의 뿌리의 `evals/`에 맞는다 (G3). | 설치가 두 번이다. 스킬의 이름이 `/explain-diff:explain-diff`가 된다. |
| I2 | ~~I1에 더해서 tstack이 `dependencies`로 explain-diff를 요구한다 (D9).~~ 버렸다 (6.2). | tstack을 설치하면 리뷰의 5번이 항상 동작한다. | "없으면 `skip`"의 선택을 강제로 바꾼다. 장치가 하나 는다. |
| I3 | ~~플러그인 1개로 합친다: tstack의 셋째 스킬 `tstack:explain-diff`.~~ 버렸다 (6.2). | 설치가 한 번이다. 버전이 하나다. | explain-diff만 쓰려는 사람이 tstack 전체를 받는다. 영어의 스킬과 한국어의 워크플로가 한 플러그인에 섞인다. |
| I4 | 폴더를 `plugins/<이름>/`으로 둔다. | 저장소의 뿌리에 문서, 검사, CI가 들어올 자리가 남는다. 플러그인이 늘어도 모양이 같다. | 경로가 한 단계 길다. |
| I5 | 파일을 그대로 복사하고 출처의 커밋을 적는다. git의 역사는 옮기지 않는다. | 단순하다. 옮길 역사가 커밋 1개씩이다 (F13). | `git blame`이 trealworld로 이어지지 않는다. |
| I6 | ~~`plugin.json`에서 `version`을 뺀다. 사용자는 커밋을 따라온다 (D4).~~ 버렸다 (6.8). | 올리는 것을 잊어도 사용자가 받는다. | 사용자가 어느 판을 쓰는지 숫자로 말하지 못한다. |
| I7 | `version`을 두고, 릴리스마다 올리고 `claude plugin tag`로 태그를 만든다 (D11). 검사가 "플러그인이 바뀌었는데 버전이 같다"를 잡는다. | 판을 숫자로 말한다. 규칙을 검사가 지킨다. | 검사를 만들어야 한다. |
| I8 | 가이드를 둘로 나눈다. 사용법은 플러그인의 안에 둔다. 기원의 이야기(9절)는 trealworld에 남긴다. | 설치한 사람이 사용법을 받는다. 프로젝트 하나의 이야기가 플러그인에 들어가지 않는다. | 가이드를 다시 써야 한다. |
| I9 | trealworld에서 `tstack/`, `.claude-plugin/`, `.claude/skills/explain-diff/`를 지우고, `extraKnownMarketplaces`로 새 마켓플레이스를 등록한다 (D10). | 원본이 하나다. | 다른 저장소를 고친다. trealworld의 문서의 링크가 깨진다. |
| I10 | 회고는 이 저장소의 clone에서 한다: `claude --plugin-dir <clone>/plugins/tstack`으로 올리고, 고친 것을 이 저장소에 커밋한다. `t-reflect`의 글에 이 길을 적는다. | G1을 닫는다. | 사용자가 회고의 전에 올리는 방법을 바꿔야 한다. |
| I11 | CI가 `tstack-check.py self`와 `claude plugin validate --strict`를 돌린다. | 깨진 색인과 깨진 매니페스트가 main에 들어가지 않는다. | CI에 Claude Code를 설치해야 한다. |

## 5. 열린 질문

Q1 ~ Q8은 닫혔다. 답은 6절에 있다. Q9 ~ Q15와 6.9의 새 질문은 열려 있다.

| # | 질문 | AI의 권장 | 상태 |
|---|---|---|---|
| Q1 | 이 저장소의 독자는 누구인가. 본인만인가, 공개인가. | 없다. 사용자만 정한다. | 닫혔다 (6.1) |
| Q2 | 둘을 어떻게 묶는가: I1, I2, I3. | I1. 뒤에 I2로 바꾸는 것은 한 줄이다. | 닫혔다 (6.2) |
| Q3 | 원본은 어디인가. trealworld의 사본을 어떻게 하는가 (I9). | 새 저장소가 원본이다. trealworld의 사본은 새 저장소의 설치를 확인한 뒤에 지운다. | 닫혔다 (6.3) |
| Q4 | `references/project-rules.md`의 규칙을 이 저장소의 `CLAUDE.md`에 넣는가. | 넣는다. | 닫혔다 (6.4) |
| Q5 | 저장소의 이름과 마켓플레이스의 이름은 무엇인가 (H5, D2, D7). | 저장소 `tobyilee/tstack`, 마켓플레이스 `tstack`. | 닫혔다 (6.5) |
| Q6 | 라이선스는 무엇인가 (G6). | MIT. | 닫혔다 (6.6) |
| Q7 | 저장소의 README와 이 저장소의 문서의 언어는 무엇인가 (G8). | 문서는 한국어. README는 두 언어. | 닫혔다 (6.7) |
| Q8 | 버전의 정책은 무엇인가: I6, I7 (G4). | I7. | 닫혔다 (6.8) |
| Q9 | 가이드를 어디에 두는가 (G5, I8). | I8. | 열렸다. 설계 문서에서 묻는다 |
| Q10 | eval을 설치에 넣는가. 어디에 두는가 (G3). | 플러그인의 뿌리의 `evals/`로 옮긴다. | 열렸다. 설계 문서에서 묻는다 |
| Q11 | explain-diff의 밖의 폰트와 "house style"을 그대로 두는가 (G7). | 그대로 둔다. `SKILL.md`의 "the user's house style"의 말만 고친다. | 열렸다. 설계 문서에서 묻는다 |
| Q12 | git의 역사를 옮기는가 (I5). | 옮기지 않는다. 출처의 커밋을 적는다. | 열렸다. 설계 문서에서 묻는다 |
| Q13 | 회고의 길을 어떻게 하는가 (G1, I10). | I10. | 열렸다. 설계 문서에서 묻는다 |
| Q14 | 다른 도구를 지원하는가 (G10). hook을 넣는가 (G11). | 둘 다 범위의 밖이다. | 열렸다. 설계 문서에서 묻는다 |
| Q15 | "설치해서 쓸 수 있다"의 검증은 무엇인가 (G9). CI를 두는가 (I11). | 세 단계: `validate` → 로컬 경로의 마켓플레이스 → push의 뒤에 GitHub에서 설치. | 열렸다. 설계 문서에서 묻는다 |

## 6. 결정된 것

6.1 ~ 6.8은 모두 "승인 (사용자가 결정, 2026-11-20)"이다.

승인의 방식: 질문 4개씩 두 번에 나눠서 물었다. 질문마다 선택지 3개를 보여 줬다. 사용자가 질문마다 하나를 골랐다. 8개 중 7개가 AI의 권장과 같다. 6.1에는 AI의 권장이 없었다.

### 6.1 독자 (Q1)

- 이 저장소는 공개한다. 다른 개발자가 tstack과 explain-diff를 설치한다.
- 그래서 라이선스(6.6), 모르는 사람이 읽는 README(6.7), 버전의 정책(6.8)이 필요하다.
- H1이 맞았다.

### 6.2 묶는 방식 (Q2)

- I1을 골랐다. 마켓플레이스 하나에 플러그인 2개를 둔다: `tstack`, `explain-diff`.
- tstack은 `dependencies`로 explain-diff를 요구하지 않는다. `review.md`의 "없으면 `skip`"이 그대로 남는다.
- 스킬의 이름은 `/tstack:t-mode`, `/tstack:t-reflect`, `/explain-diff:explain-diff`가 된다 (D5).
- 버린 것: I2, I3. H3이 맞았다.

### 6.3 원본 (Q3)

- 새 저장소가 유일한 원본이다.
- trealworld의 사본(`tstack/`, `.claude-plugin/marketplace.json`, `.claude/skills/explain-diff/`)은 지운다. 새 저장소에서 설치한 것을 확인한 뒤의 스텝에서 한다. trealworld에는 새 마켓플레이스를 등록한다 (I9).
- 이 결정은 다른 저장소를 고친다. 그 스텝은 사용자의 요청으로 시작한다.
- H2가 맞았다. H2의 약한 곳(회고의 길)은 Q13에 남아 있다.

### 6.4 프로젝트의 규칙 (Q4)

- `references/project-rules.md`의 규칙을 이 저장소의 `CLAUDE.md`에 넣는다.
- 처음의 질문의 미리보기에는 두 절이 빠져 있었다: "해당 없는 항목은 뺀다", "코드 식별자, 경로, 기술 용어는 원문을 쓸 수 있다. (MAY)". 사용자가 두 절을 따로 승인했다 (같은 날).
- 문서의 언어의 줄은 6.7의 답으로 채웠다.

### 6.5 이름 (Q5)

- GitHub 저장소: `tobyilee/tstack`. 마켓플레이스의 `name`: `tstack`.
- 설치의 이름은 `tstack@tstack`, `explain-diff@tstack`이다.
- `tobyilee/tstack`은 지금 없는 저장소다 (확인: `gh repo view`, 2026-11-20). `tstack`은 D2의 목록에 없다 (읽음).
- 받아들인 한계: 마켓플레이스의 이름을 뒤에 바꾸면 이미 설치한 사용자의 설치가 깨진다. tstack과 관계가 없는 플러그인을 더하면 이름이 내용보다 좁다.
- H5가 맞았다.

### 6.6 라이선스 (Q6)

- MIT.
- 근거로 본 것: pstack의 `plugin.json`의 `license`가 `MIT`다 (확인: 이 컴퓨터의 `cursor-plugins` 마켓플레이스의 사본). tstack은 pstack에서 생각 8개를 가져왔다 (읽음: `tstack-guide.md` 9.3). 글을 복사했는지는 대조하지 않았다 (추정: 복사하지 않았다).

### 6.7 언어 (Q7)

- 이 저장소의 문서(spec, domain, ADR, plan, 일지)는 한국어다.
- 저장소의 뿌리의 README는 영어의 짧은 절(무엇인가, 설치하는 방법)과 한국어의 본문을 둔다.
- 플러그인의 글은 번역하지 않는다. tstack은 한국어로, explain-diff는 영어로 남는다.

### 6.8 버전 (Q8)

- I7을 골랐다. 플러그인마다 `plugin.json`에 `version`을 둔다. 릴리스마다 올리고 `claude plugin tag`로 태그를 만든다.
- 스크립트가 "플러그인의 파일이 바뀌었는데 버전이 같다"를 실패로 낸다.
- 버린 것: I6.

### 6.9 답에서 나온 새 질문

AI가 6.1 ~ 6.8을 다시 읽고 찾았다. 사용자가 정하지 않았다. 설계 문서에서 제안하고 확인을 받는다.

| # | 질문 | 어느 결정에서 나왔는가 | AI의 권장 |
|---|---|---|---|
| N1 | 플러그인의 폴더를 `plugins/<이름>/`에 두는가 (I4). Q2의 미리보기에 이 모양이 있었다. 질문으로 묻지 않았다. | 6.2 | 둔다. |
| N2 | 라이선스의 저작권의 줄의 이름과 연도는 무엇인가. | 6.6 | `Toby Lee`, 2026. `plugin.json`의 `author`에서 가져왔다 (추정). |
| N3 | 설치는 플러그인의 폴더만 복사한다 (D3). 저장소의 뿌리의 `LICENSE`는 설치한 사본에 없다. 플러그인마다 `plugin.json`의 `license`를 쓰는가, `LICENSE` 파일을 넣는가. | 6.6, 6.2 | 둘 다 한다. |
| N4 | explain-diff 플러그인의 첫 버전은 무엇인가. 지금은 버전이 없다. | 6.8, 6.2 | `0.1.0`. tstack과 같다. |
| N5 | 버전의 검사는 무엇과 비교하는가 (마지막 태그, 원격의 main). 언제 도는가 (커밋의 전, CI). | 6.8 | 마지막 태그와 비교한다. Q15의 CI와 함께 정한다. |
| N6 | 플러그인의 안의 README의 언어는 무엇인가. explain-diff에는 README가 없다. | 6.7 | 플러그인의 글의 언어를 따른다: tstack은 한국어, explain-diff는 영어. |
| N7 | 저장소를 언제 공개하는가. 첫 push인가, 검증의 뒤인가. | 6.1 | 로컬 경로의 마켓플레이스로 검증한 뒤의 첫 push. |
| N8 | README가 요구하는 Claude Code의 최소 버전은 무엇인가 (G12). | 6.5 | 두 설치 명령을 모두 적는다. 짧은 명령에 "2.1.275 이상"을 적는다. |

### 6.11 설계 문서가 닫은 질문 (2026-11-20)

설계 문서의 단계에서 사용자에게 질문 4개를 물었다: 슬라이스의 끝, 내용의 수정의 범위, 검증의 방법, 가이드의 자리. 나머지는 AI가 제안으로 적었다. 제안은 사용자의 확인을 기다린다.

| 질문 | 답 | 누가 | 문서 |
|---|---|---|---|
| Q9 | 가이드를 플러그인의 안으로 옮긴다. 옮겨서 깨지는 것만 고친다. | 사용자 | ADR-0001의 규칙 4 |
| Q10 | eval 사례를 플러그인의 폴더의 `evals/`로 옮긴다. | AI | ADR-0001의 규칙 3 |
| Q11 | "the user's house style"의 말을 고친다. 밖의 폰트는 그대로 둔다. | 사용자 (말), AI (폰트) | Spec 01의 AC-4.3, "받아들인 한계" 3번 |
| Q12 | git의 역사를 옮기지 않는다. 출처의 기록을 둔다. | AI | ADR-0002 |
| Q13 | 슬라이스 1에서 `t-reflect`를 고친다. 방법은 `claude --plugin-dir`다. | 사용자 (고친다), AI (방법) | Spec 01의 AC-4.1, AC-4.2 |
| Q14 | 다른 도구와 hook은 범위의 밖이다. | AI | Spec 01의 "범위 밖" |
| Q15 | Python의 `unittest`와 GitHub Actions. 검사의 세 단계. | 사용자 (도구), AI (세부) | ADR-0004 |
| N1 | `plugins/<플러그인의 이름>/`. | AI | ADR-0001의 규칙 1 |
| N2 | `Copyright (c) 2026 Toby Lee`. | AI | Spec 01의 AC-6.2 |
| N3 | 플러그인마다 `LICENSE`와 `license`를 둔다. | AI | Spec 01의 AC-2.5, AC-2.6 |
| N4 | `explain-diff`는 `0.1.0`. `tstack`은 `0.2.0`. | AI | ADR-0003 |
| N5 | 마지막 릴리스의 태그와 비교한다. | AI | ADR-0003의 규칙 4 |
| N6 | 플러그인의 README는 플러그인의 글의 언어를 따른다. | AI | Spec 01의 "가정" 1번 |
| N7 | 슬라이스 1의 마지막 작업에서 공개한다. push는 그때 다시 묻는다. | 사용자 (슬라이스의 끝), AI (공개의 시점) | Plan 01의 작업 13 |
| N8 | README는 두 단계의 설치 명령만 적는다. | AI | Spec 01의 "가정" 2번 |

수정 (2026-11-20): 사용자가 이 표의 AI의 제안을 묶어서 승인했다. 하나씩 보지는 않았다. N8은 사용자가 방향을 다시 정했다: 설치의 방법은 마켓플레이스의 등록과 플러그인의 설치다. `--plugin-dir`는 로컬의 변경을 바로 적용하는 방법으로 가이드와 README에 넣는다 (Spec 01의 AC-2.11 ~ AC-2.13).

사용자가 AI의 권장과 다르게 고른 것: 내용의 수정의 범위. AI는 "옮기기만 한다"를 권했다. 사용자는 "옮기면서 결함 3개도 고친다"를 골랐다. 그 결과로 I7의 "첫 릴리스가 버전의 검사의 첫 실제 사용이 된다"는 생각은 버렸다. `tstack`의 첫 버전은 `0.2.0`이 됐다.

### 6.10 가설의 상태

| # | 상태 |
|---|---|
| H1 | 맞았다 (6.1). |
| H2 | 맞았다 (6.3). 약한 곳이 남았다: `t-reflect`가 읽는 일지는 trealworld에 있고, 고치는 파일은 이 저장소에 있다 (Q13). |
| H3 | 맞았다 (6.2). |
| H4 | 묻지 않았다. 6.4의 규칙이 "테스트를 먼저 쓴다"를 넣었다. 이 저장소의 산출물은 대부분 글과 JSON이다. 테스트가 무엇인지는 Q15에서 정한다. |
| H5 | 맞았다 (6.5). |
| H6 | 묻지 않았다. 검증하지 않은 추측으로 남는다. 6.5의 받아들인 한계가 이 가설에 걸려 있다. |
