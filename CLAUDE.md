# NotebookLM 작업 폴더

NotebookLM(`nlm` CLI, notebooklm-mcp-cli)과 Claude Code를 같이 쓰는 작업 폴더다. 강의·업무 자료를 NotebookLM 노트북에 올리고, 요약·질문은 NotebookLM에, 풀이·검산·정리 자료 만들기는 Claude가 맡는다.

개인 설정(답변 언어, 소속, 과목, 과제 방식)은 이 파일이 아니라 아래 파일에 있다. 있으면 먼저 따른다.
@CLAUDE.local.md

## 폴더 규칙 (데이터 흐름 순서)

| 폴더 | 넣는 것 |
|---|---|
| `01_upload/<노트북>/` | NotebookLM에 올릴 파일. `nlmw upload <노트북>`으로 올리면 `_uploaded/`로 이동 |
| `02_from-lm/<노트북>/` | NotebookLM에서 받은 것: `sources/`(소스 텍스트), `images/`(소스 속 원본 그림), `infographics/`, `audio/`, `video/`, `slides/`, `reports/`, `study/` |
| `03_work/<노트북>/<작업명>/` | Claude 작업물: 풀이, 정리, 계산, html 페이지, 캡처 |
| `04_final/<노트북>/` | 제출·공유용 최종본 (PDF 등) |
| `inbox/` | 분류 전 파일 |

- `<노트북>` 폴더 이름은 NotebookLM 노트북 제목 그대로다. 목록과 ID는 `notebooks.md` (`nlmw sync`로 갱신).
- 결과물을 임시 폴더에 남기지 말고 위 규칙대로 저장한다.
- 노트북별 특이사항(표기법, 과목 정보)이 `03_work/<노트북>/README.md`에 있으면 먼저 읽는다. 작업을 하면 그 README에 한 줄 기록한다.

## 도구 (`nlmw`)

```
nlmw doctor                              설치·로그인·브라우저 점검
nlmw sync [--no-dirs]                    노트북 목록 → notebooks.md (+ 노트북별 폴더)
nlmw upload <노트북> [--dry-run]          01_upload 파일을 소스로 올리기
nlmw restore <노트북>|--all [--images] [--studio]   소스 텍스트(+그림, 스튜디오 결과물) 받기
nlmw images <노트북> [--source 이름]      소스 속 원본 그림 받기
nlmw pull <노트북>                        완료된 인포그래픽·오디오·슬라이드 등 받기
nlmw pdf <html> [--out x.pdf]             HTML → PDF (Chrome/Edge headless, 페이지 수 출력)
nlmw nlm <nlm 명령...>                    nlm을 그대로 실행 (PATH에 없어도 됨)
```
`<노트북>`은 제목, 제목 일부, ID 모두 된다.

## nlm 사용 메모
- 인증: `nlm login` (브라우저 쿠키). 명령이 인증 오류를 내면 사용자에게 `nlm login`을 다시 하라고 안내한다.
- 자주 쓰는 명령: `nlm list sources <id> --json`, `nlm query notebook <id> "<질문>" --source-ids "<id1>,<id2>"`(쉼표로 이은 한 문자열), `nlm content source <source_id>`, `nlm status artifacts <id> --json`.
- 스튜디오 생성(인포그래픽, 오디오 등)은 비동기다. `nlm status artifacts`의 해당 ID `status`가 `completed`인지 JSON으로 확인한 뒤 받는다(다른 결과물의 상태를 잘못 읽지 않게).

## NotebookLM 결과 검증 규칙
- NotebookLM 요약은 문제 개수를 틀리거나 그림 설명을 지어낼 수 있다. 문제 수·그림·수치는 `nlmw images`로 받은 원본으로 확인한다.
- 손글씨 필기는 OCR 텍스트만 읽힌다. 인용할 때 "OCR 기준"임을 밝히고 앞뒤가 안 맞는 식은 짚어 준다.
- 인포그래픽은 결과 식·요약은 쓸 만하지만 기하 그림(축 방향 등)은 자주 틀린다. 사용자에게 줄 때 틀린 부분을 표로 알려준다.
- 수치 계산은 numpy·sympy 등으로 검산한 뒤 전달한다.
- 노트북에 Claude가 만든 자료를 올릴 때는 제목에 "(Claude 정리)"를 붙인다.

## 과제 도움 방식
- 답만 주기보다 옮겨 쓸 수 있는 풀이 흐름(근거 한 줄씩)으로 정리하고, 강의·필기의 표기법을 따른다.
- 평가 기준에 "AI 결과 직접 검증"이 있는 과목이 있으니, 사용자가 본인 말로 쓸 수 있게 초안으로 제시한다.
