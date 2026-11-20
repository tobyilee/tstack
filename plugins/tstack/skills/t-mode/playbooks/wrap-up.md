### 마무리

**당신은 스텝의 기록을 가진다.** 모든 playbook의 끝에서 한다. 커밋만 요청받은 때에도 1번부터 한다.

기록을 규칙에 맞춘다. "결정이 없는 단순한 스텝"도 스텝이다.

1. `git status`와 `git diff --stat`을 읽는다. 내가 만들지 않은 파일, 이 스텝에 속하지 않는 파일, 남은 임시 파일, 되돌리지 않은 결함을 찾는다.
2. 일지를 쓴다 (`references/journal-format.md`). 커밋의 전에 쓴다.
3. `scripts/tstack-check.py journal`을 돌린다.
4. 보고를 쓴다 (`references/report-template.md`).
5. 커밋의 요청이 없으면 8번으로 간다.
6. 커밋한다. 경로를 지정해서 올린다. 내가 만들지 않은 파일은 넣기 전에 묻는다. 코드의 변경과 리뷰의 기록(설명 문서)은 다른 커밋이다. 메시지는 프로젝트의 문서의 언어로 쓴다.
7. push는 요청이 있을 때만 한다. push한 커밋의 역사는 바꾸지 않는다. 확인은 `git`에 직접 묻는다 (`git status -sb`, `git ls-remote`).
8. 멈춘다. 다음 스텝의 후보를 한 줄로 말한다. 시작하지 않는다 (`principles/user-drives-the-pace.md`).

**보고:** `references/report-template.md`의 형식. 커밋했으면 커밋마다 내용을 한 줄로, 넣지 않은 파일과 이유.
