# tstack

문서를 먼저 쓰고, 테스트를 먼저 쓰고, 스텝마다 일지를 쓰는 개발 워크플로의 스킬 세트다. Lauren Tan의 pstack의 원리를 따른다: 입구는 하나, 색인과 본문은 따로, 검증은 구조의 안에.

## 설치

```text
/plugin install tstack --marketplace tobyilee/trealworld
```

저장소를 받은 폴더에서 바로 써 보려면 `claude --plugin-dir ./tstack`으로 시작한다.

사용법은 저장소의 [`tstack-guide.md`](../tstack-guide.md)에 있다.

| 부품 | 위치 | 역할 |
|---|---|---|
| 라우터 | `skills/t-mode/SKILL.md` | 입구. 항상의 규칙, 원칙의 색인, 자율성, playbook의 색인 |
| playbook 10개 | `skills/t-mode/playbooks/` | 작업의 유형마다 단계의 목록 |
| principle 12개 | `skills/t-mode/principles/` | 판단의 규칙. 적용할 때 읽는다 |
| reference 6개 | `skills/t-mode/references/` | 일지, 문서, 리뷰 메모, 보고의 형식 |
| 검사 | `skills/t-mode/scripts/tstack-check.py` | `trace`, `keywords`, `journal`, `self` |
| 회고 | `skills/t-reflect/SKILL.md` | 일지에서 반복된 교정을 찾아 스킬을 고친다 |
| 리뷰어 | `agents/t-reviewer.md` | 쓴 사람이 아닌 agent의 리뷰 |
