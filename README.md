# second-brain-kit

옵시디언(Obsidian) 노트 폴더를 AI 에이전트가 직접 읽고 쓰게 해 "스스로 정리되는 제2의 뇌"로 운영하기 위한 견본 모음입니다.
Karpathy의 [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 구상과 Forte의 *Building a Second Brain*을 참고해, 실제 운영하며 다듬은 구조·규칙·양식을 일반화했습니다.

해설 글: [제2의 뇌 구축하기: 옵시디언과 AI 에이전트 기반 개인 지식 체계](https://jason-log.github.io/2026/10/16/obsidian-ai-second-brain/)

## 들어 있는 것

| 경로 | 내용 |
|---|---|
| `docs/structure.md` | 층 설계(누가 썼고 얼마나 믿는가), 세 연산, 권한 3단계, 세션 운용 |
| `docs/agents.md` | 역할 분담과 검수 원칙(새 맥락 검수, 에이전트 산출물 비승격, brief 작성) |
| `templates/CLAUDE.md` | 폴더 맨 위에 두는 진입 문서(스키마) 견본 |
| `templates/rules.md` | 운용 규칙 견본 — 정정에서 생기고 안 쓰이면 사라지는 규칙 |
| `templates/handoff.md`, `templates/state.json` | 세션 간 이어 쓰기 양식 |
| `templates/brief.md` | 서브에이전트에 일을 맡길 때 쓰는 지시서 양식 |
| `agents/` | 일반 역할 5종: explorer·analyst·writer·verifier·critic |
| `tools/safe_edit.py` | 기존 파일을 안전하게 고치는 도구(판본 확인·줄바꿈 보존·전부 아니면 전무·쓰기 후 검증) |

## 시작하는 법

1. 옵시디언을 설치하고 노트 폴더(볼트)를 하나 만듭니다.
2. 파일을 다룰 수 있는 AI 에이전트(Claude Cowork, Claude Code, Codex 등)에 그 폴더를 연결합니다.
3. `templates/CLAUDE.md`와 `templates/rules.md`를 볼트 맨 위에 복사하고 내 상황에 맞게 고칩니다. 에이전트에게 "이 견본을 내 볼트에 맞게 고쳐 줘"라고 맡겨도 됩니다.
4. 자료를 한 건씩 넣으며 AI의 정리를 직접 확인합니다. 대량 위임은 익숙해진 뒤에 합니다.
5. 볼트를 git 저장소로 두고 작업 단위로 커밋합니다.

견본은 출발점일 뿐입니다. 규칙은 처음부터 다 정하지 말고, 정정이 반복될 때 추가하고 쓰이지 않으면 지웁니다.

## 주의

- AI는 그럴듯하게 틀립니다. 남에게 내는 글의 수치·인용은 위키가 아니라 원문으로 다시 확인합니다.
- 에이전트가 읽은 내용은 클라우드 모델로 전송됩니다. 민감한 자료는 읽기 대상에서 빼는 규칙을 먼저 둡니다.

## 참고

- Karpathy, A. (2026). *LLM Wiki* [GitHub Gist].
- Forte, T. (2022). *Building a second brain*. Atria Books.

## 라이선스

MIT
