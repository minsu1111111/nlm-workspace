# nlm-workspace

Google **NotebookLM**(`nlm` CLI)과 **Claude Code**를 같이 써서 대학 과목 자료를 정리하고 공부·과제에 쓰는 작업 폴더입니다. 강의 자료를 NotebookLM 노트북에 올리고, 요약·질문은 NotebookLM에, 풀이·검산·정리 페이지 만들기는 Claude Code에 맡깁니다.

> 이 저장소에는 **도구와 폴더 구조만** 있습니다. 강의 원본, 과제, 풀이 결과물은 저작권·개인정보 때문에 올리지 않았습니다(`.gitignore`). 새 PC에서는 아래 「다른 PC에서 이어서 쓰기」로 NotebookLM에서 다시 받습니다.

## 설치 (Windows, 한 번에)

```powershell
git clone https://github.com/minsu1111111/nlm-workspace.git
cd nlm-workspace
powershell -ExecutionPolicy Bypass -File .\setup.ps1
nlm login
```

`setup.ps1`이 하는 일:
1. 파이썬 3.10 이상 확인 (`py -3.11` 우선)
2. `requirements.txt` 설치: `notebooklm-mcp-cli`(nlm), `httpx`, `pymupdf`, `numpy`, `sympy`, `matplotlib`
3. 작업 폴더 `01_upload` ~ `04_final`, `inbox` 만들기
4. `nlm` 실행 파일 위치 확인, PDF 변환용 Microsoft Edge 확인

`nlm login`은 브라우저로 Google 계정에 로그인해 쿠키를 `~/.notebooklm-mcp-cli`에 저장합니다. 명령이 인증 오류를 내면 다시 `nlm login` 하세요.

## 폴더 규칙 (데이터 흐름 순서)

| 폴더 | 넣는 것 |
|---|---|
| `01_upload/<노트북>/` | NotebookLM에 올릴 파일. 올리면 `_uploaded/`로 이동 |
| `02_from-lm/<노트북>/` | NotebookLM에서 받은 것: `sources/`(소스 텍스트), `images/`(소스 속 원본 그림), `infographics/`, `audio/`, `slides/`, `reports/`, `study/` |
| `03_work/<노트북>/<작업명>/` | Claude 작업물: 풀이, 정리, 계산, html 페이지 |
| `04_final/<노트북>/` | 제출·공유용 최종본 (PDF 등) |
| `inbox/` | 분류 전 파일 |

`<노트북>` 폴더 이름은 NotebookLM 노트북 제목 그대로입니다. 목록과 ID는 `notebooks.md`.

## 도구 (`tools/`)

```
python tools/sync.py                          노트북 목록 → notebooks.md, 노트북별 폴더 생성
python tools/upload.py <노트북> [--dry-run]    01_upload 파일을 소스로 올리기
python tools/restore.py <노트북>|--all [--images] [--studio]
                                              NotebookLM 소스 텍스트(+그림, 스튜디오 결과물) 다시 받기
python tools/fetch_images.py <노트북> [--source 이름]   소스 속 원본 그림 받기
python tools/pull.py <노트북>                   완료된 인포그래픽·오디오·슬라이드 등 받기
python tools/to_pdf.py <html> [--out x.pdf]    HTML → PDF (Edge headless)
```

`<노트북>`은 제목, 제목 일부, ID 모두 됩니다. PowerShell에서 `nlm`을 직접 쓸 때는 먼저 `. .\tools\env.ps1`.

## 다른 PC에서 이어서 쓰기

NotebookLM은 **올린 원본 파일(pdf·pptx)을 그대로 돌려주지 않습니다.** 대신 아래는 다시 받을 수 있습니다.

| 받을 수 있는 것 | 명령 | 저장 위치 |
|---|---|---|
| 소스별 추출 텍스트 (슬라이드·PDF 글자, 그림 링크 포함) | `python tools/restore.py --all` | `02_from-lm/<노트북>/sources/` |
| 소스 속 원본 그림 | `python tools/restore.py <노트북> --images` | `02_from-lm/<노트북>/images/` |
| 스튜디오 결과물 (인포그래픽, 오디오, 슬라이드, 보고서 등) | `python tools/restore.py <노트북> --studio` | `02_from-lm/<노트북>/...` |

원본 파일 자체가 필요하면 Google Drive·OneDrive 같은 곳에 `01_upload`를 따로 백업해 두세요(강의 자료는 공개 저장소에 올리지 않기).

## Claude Code와 같이 쓰기

`CLAUDE.md`에 이 폴더의 규칙(저장 위치, NotebookLM 결과 검증 규칙, 과제 도움 방식)이 있어서 Claude Code가 작업할 때 자동으로 따릅니다. 핵심 규칙:
- NotebookLM 요약은 문제 수·그림·수치를 틀릴 수 있으니 원본으로 확인
- 수치 계산은 numpy·sympy로 검산한 뒤 전달
- 노트북에 Claude가 만든 자료를 올릴 때는 제목에 "(Claude 정리)"
