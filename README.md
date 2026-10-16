# nlm-workspace

**Google NotebookLM**과 **Claude Code**로 강의·업무 자료를 정리하고 공부·과제에 쓰기 위한 작업 폴더 도구입니다.
자료를 NotebookLM 노트북에 올리고, 요약·질문은 NotebookLM에, 풀이·검산·정리 자료 만들기는 Claude Code에 맡기는 흐름을 폴더 규칙과 명령 하나(`nlmw`)로 묶었습니다.

```
01_upload  ──nlmw upload──▶  NotebookLM  ──nlmw restore / images / pull──▶  02_from-lm
                                                                              │
                                     Claude Code가 풀이·정리·검산  ◀───────────┘
                                              ▼
                                  03_work (작업물)  ──nlmw pdf──▶  04_final (제출본)
```

- NotebookLM 접속은 [notebooklm-mcp-cli](https://pypi.org/project/notebooklm-mcp-cli/)(`nlm` 명령)를 씁니다.
- Windows, macOS, Linux 모두 됩니다. 파이썬 3.10 이상.

## 설치

**A. 명령만 설치** (원하는 폴더를 작업 폴더로 만들어 쓰기)
```bash
python -m pip install --user "nlm-workspace[study] @ git+https://github.com/minsu1111111/nlm-workspace"
nlm login                 # 브라우저로 Google 로그인 (쿠키 저장)
nlmw init ~/study         # 작업 폴더 만들기
cd ~/study && nlmw doctor
```

**B. 저장소를 받아서 그 폴더를 작업 폴더로 쓰기**
```bash
git clone https://github.com/minsu1111111/nlm-workspace.git
cd nlm-workspace
powershell -ExecutionPolicy Bypass -File .\setup.ps1     # Windows
bash setup.sh                                            # macOS / Linux
nlm login
nlmw doctor
```

`[study]`는 풀이 검산·그림에 쓰는 `pymupdf`, `numpy`, `sympy`, `matplotlib`을 같이 설치합니다. 명령만 필요하면 `[study]` 없이 설치해도 됩니다.
`nlm`/`nlmw`를 찾을 수 없다고 나오면 파이썬 사용자 Scripts(bin) 폴더를 PATH에 추가하세요(`setup` 스크립트가 경로를 알려 줍니다).

## 빠른 시작

```bash
nlmw sync                         # 내 노트북 목록 → notebooks.md, 노트북별 폴더 생성
# 01_upload/<노트북 제목>/ 에 pdf·pptx를 넣고
nlmw upload "로봇공학"             # NotebookLM에 소스로 올리고 _uploaded/로 이동
nlmw images "로봇공학"             # 소스 속 원본 그림 받기 (문제 그림 확인용)
nlmw pull "로봇공학"               # 만들어 둔 인포그래픽·오디오·슬라이드 받기
nlmw pdf 03_work/로봇공학/HW2/풀이.html   # HTML 풀이 노트 → PDF
```
`<노트북>` 자리에는 제목, 제목 일부, ID 모두 됩니다.

## 명령

| 명령 | 하는 일 |
|---|---|
| `nlmw init [폴더] [--profile 이름]` | 작업 폴더 만들기: 폴더 구조, `nlmw.json`, `CLAUDE.md`, `CLAUDE.local.md`, `.gitignore` |
| `nlmw doctor` | 설치·로그인·PDF 변환 브라우저 점검 |
| `nlmw sync [--no-dirs] [--only 글자]` | 노트북 목록 → `notebooks.md` (+ 노트북별 폴더) |
| `nlmw upload <노트북> [--dry-run]` | `01_upload/<노트북>/` 파일을 소스로 올리고 `_uploaded/`로 이동 |
| `nlmw restore <노트북>\|--all [--images] [--studio]` | 소스 텍스트(+그림, 스튜디오 결과물) 받기 |
| `nlmw images <노트북> [--source 이름]` | 소스 속 원본 그림 받기 |
| `nlmw pull <노트북>` | 완료된 스튜디오 결과물(인포그래픽, 오디오, 영상, 슬라이드, 보고서, 퀴즈 등) 받기 |
| `nlmw pdf <html> [--out x.pdf] [--wait 초]` | HTML → PDF (Chrome/Edge/Chromium headless, `@page` 따름) |
| `nlmw nlm <nlm 명령...>` | `nlm`을 그대로 실행 (PATH에 없어도, UTF-8 출력) |

## 작업 폴더 구조

| 폴더 | 넣는 것 |
|---|---|
| `01_upload/<노트북>/` | NotebookLM에 올릴 파일. 올리면 `_uploaded/`로 이동 |
| `02_from-lm/<노트북>/` | NotebookLM에서 받은 것: `sources/`, `images/`, `infographics/`, `audio/`, `video/`, `slides/`, `reports/`, `study/` |
| `03_work/<노트북>/<작업명>/` | 풀이, 정리, 계산, html 페이지 |
| `04_final/<노트북>/` | 제출·공유용 최종본 |
| `inbox/` | 분류 전 파일 |

폴더 이름은 `nlmw.json`에서 바꿀 수 있습니다. Google 계정이 여러 개면 `nlm login --profile 이름`으로 로그인하고 `nlmw.json`의 `"profile"`에 그 이름을 적으세요.

## Claude Code와 같이 쓰기

`nlmw init`이 만드는 두 파일을 Claude Code가 자동으로 읽습니다.

- **`CLAUDE.md`** (공유용): 폴더 규칙, `nlmw` 명령, **NotebookLM 결과 검증 규칙**
  - NotebookLM 요약은 문제 수·그림 설명을 틀릴 수 있으니 `nlmw images`로 받은 원본으로 확인
  - 수치는 numpy·sympy로 검산한 뒤 전달
  - Claude가 만든 자료를 노트북에 올릴 때는 제목에 "(Claude 정리)"
- **`CLAUDE.local.md`** (개인용, git 제외): 답변 언어, 소속·과목, 과제 제출 방식, 파일 이름 규칙 등을 적어 두세요.

Claude Code에게 "로봇공학 HW2 풀어서 PDF로 만들어줘"처럼 말하면 위 규칙대로 자료를 읽고, 검산하고, `03_work`·`04_final`에 저장합니다.

## 다른 PC에서 이어서 쓰기

NotebookLM은 **올린 원본 파일(pdf·pptx)을 그대로 돌려주지 않습니다.** 대신 아래는 다시 받을 수 있습니다.

| 받을 수 있는 것 | 명령 |
|---|---|
| 소스별 추출 텍스트 (글자 + 그림 링크) | `nlmw restore --all` |
| 소스 속 원본 그림 | `nlmw restore <노트북> --images` |
| 스튜디오 결과물 | `nlmw restore <노트북> --studio` |

원본 파일이 필요하면 `01_upload`를 Google Drive·OneDrive 등에 따로 백업하세요.

## 주의

- 기본 `.gitignore`는 `01_upload`~`04_final`, `inbox`의 내용물, `CLAUDE.local.md`, `notebooks.md`를 제외합니다. **강의 자료(저작권)와 과제(학번·이름)를 공개 저장소에 올리지 마세요.**
- `nlm`은 NotebookLM 웹 쿠키로 동작하는 비공식 도구입니다. 쿠키는 `~/.notebooklm-mcp-cli`에 저장되며 이 저장소에는 들어가지 않습니다. 로그인이 만료되면 `nlm login`을 다시 하세요.
- 과제에 AI 사용 규정이 있는지 확인하고, 결과는 직접 검증해서 쓰세요.

---

### English summary

`nlmw` is a small CLI that turns a folder into a NotebookLM + Claude Code study workspace: upload files as NotebookLM sources, sync your notebook list, download source text / embedded figures / Studio artifacts, and print HTML notes to PDF. Install with `pip install "nlm-workspace[study] @ git+https://github.com/minsu1111111/nlm-workspace"`, then `nlm login`, `nlmw init`, `nlmw doctor`. Personal settings live in the git-ignored `CLAUDE.local.md`.

## License

MIT
