"""nlmw 하위 명령 구현."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from importlib import resources
from pathlib import Path

from . import __version__
from .core import (CONFIG_NAME, DEFAULT_FOLDERS, NlmwError, Workspace, cookie_file, find_workspace,
                   list_notebooks, nlm_env, nlm_exe, resolve_notebook, run_nlm, safe_name, unique_path)


def _template(name: str) -> str:
    return resources.files("nlm_workspace").joinpath("templates", name).read_text(encoding="utf-8")


# ---------------- init ----------------
def cmd_init(args) -> None:
    root = Path(args.dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    cfg = root / CONFIG_NAME
    if cfg.exists():
        print(f"이미 작업 폴더입니다: {cfg}")
    else:
        conf = {"version": 1, "folders": DEFAULT_FOLDERS, "profile": args.profile}
        cfg.write_text(json.dumps(conf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"만듦: {cfg}")
    ws = find_workspace(root)
    for d in (ws.upload, ws.from_lm, ws.work, ws.final, ws.inbox):
        d.mkdir(parents=True, exist_ok=True)
        (d / ".gitkeep").touch()
    for src, dst in (("CLAUDE.md", "CLAUDE.md"), ("CLAUDE.local.md", "CLAUDE.local.md"), ("gitignore", ".gitignore")):
        path = root / dst
        if path.exists():
            print(f"있음(그대로 둠): {dst}")
        else:
            path.write_text(_template(src), encoding="utf-8")
            print(f"만듦: {dst}")
    print("\n다음: `nlm login` → `nlmw doctor` → `nlmw sync`")


# ---------------- doctor ----------------
def cmd_doctor(args) -> None:
    ok = True
    print(f"nlmw {__version__}, Python {sys.version.split()[0]}")
    try:
        exe = nlm_exe()
        ver = subprocess.run([exe, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace", env=nlm_env()).stdout.strip()
        print(f"[OK] nlm: {exe} ({ver})")
    except NlmwError as e:
        print(f"[X]  {e}"); ok = False
    try:
        ws = find_workspace()
        print(f"[OK] 작업 폴더: {ws.root}" + (f" (nlm 프로필 {ws.profile})" if ws.profile else ""))
    except NlmwError as e:
        ws = None; print(f"[!]  {e}")
    if ok:
        try:
            n = len(list_notebooks(ws))
            print(f"[OK] NotebookLM 로그인: 노트북 {n}개")
        except NlmwError as e:
            print(f"[X]  NotebookLM 접속 실패 → `nlm login`\n     {str(e).splitlines()[-1][:160]}"); ok = False
    b = find_browser()
    print(f"[OK] PDF 변환 브라우저: {b}" if b else "[!]  Chrome/Edge/Chromium이 없어 `nlmw pdf`를 쓸 수 없습니다.")
    missing = [m for m in ("pymupdf", "numpy", "sympy", "matplotlib") if not _has(m)]
    print("[OK] 검산 라이브러리(study) 설치됨" if not missing else f"[!]  선택 라이브러리 없음: {', '.join(missing)} → pip install \"nlm-workspace[study]\"")
    if not ok:
        sys.exit(1)


def _has(mod: str) -> bool:
    try:
        __import__(mod); return True
    except Exception:
        return False


# ---------------- nlm (그대로 전달) ----------------
def cmd_nlm(args) -> None:
    """PATH에 nlm이 없어도 쓸 수 있게 nlm을 대신 실행한다 (UTF-8 출력)."""
    sys.exit(subprocess.call([nlm_exe(), *args.rest], env=nlm_env()))


# ---------------- sync ----------------
def cmd_sync(args) -> None:
    ws = find_workspace()
    notebooks = sorted(list_notebooks(ws), key=lambda nb: nb.get("updated_at") or "", reverse=True)
    if args.only:
        notebooks = [nb for nb in notebooks if args.only.lower() in nb["title"].lower()]
    lines = ["# NotebookLM 노트북 목록", "", f"마지막 동기화: {datetime.now():%Y-%m-%d %H:%M} (`nlmw sync`로 갱신)", "",
             "| 제목 | 폴더 이름 | 소스 | 마지막 수정 | ID |", "|---|---|---|---|---|"]
    for nb in notebooks:
        if not args.no_dirs:
            ws.notebook_dirs(nb["title"])
        lines.append(f"| {nb['title']} | {safe_name(nb['title'])} | {nb.get('source_count', '')} | {(nb.get('updated_at') or '')[:10]} | `{nb['id']}` |")
    (ws.root / "notebooks.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"노트북 {len(notebooks)}개를 notebooks.md에 기록했습니다" + ("." if args.no_dirs else " (노트북별 폴더도 만듦)."))


# ---------------- upload ----------------
def cmd_upload(args) -> None:
    ws = find_workspace()
    nb = resolve_notebook(args.notebook, ws)
    dirs = ws.notebook_dirs(nb["title"])
    files = sorted(p for p in dirs["upload"].iterdir() if p.is_file() and not p.name.startswith("."))
    if not files:
        print(f"올릴 파일이 없습니다: {dirs['upload']}"); return
    for path in files:
        if args.dry_run:
            print(f"[올릴 예정] {path.name}"); continue
        print(f"올리는 중: {path.name} ...", flush=True)
        try:
            result = run_nlm("source", "add", nb["id"], "--file", str(path), "--title", path.stem, "--wait", "--json", profile=ws.profile)
        except NlmwError as err:
            print(f"  실패: {err}"); continue
        dest = unique_path(dirs["uploaded"] / path.name)
        shutil.move(str(path), dest)
        print(f"  완료 (source_id {result.get('source_id', '?')}) → _uploaded/{dest.name}")


# ---------------- restore (소스 텍스트) ----------------
def cmd_restore(args) -> None:
    ws = find_workspace()
    targets = list_notebooks(ws) if args.all else [resolve_notebook(args.notebook, ws)] if args.notebook else None
    if targets is None:
        raise NlmwError("노트북 이름(또는 --all)을 주세요.")
    for nb in targets:
        out = ws.notebook_dirs(nb["title"])["from_lm"] / "sources"
        out.mkdir(parents=True, exist_ok=True)
        sources = run_nlm("list", "sources", nb["id"], "--json", profile=ws.profile)
        print(f"\n== {nb['title']} ({len(sources)}개 소스)")
        manifest = []
        for s in sources:
            path = out / f"{safe_name(s['title'])}.txt"
            manifest.append({"id": s["id"], "title": s["title"], "type": s.get("type"), "file": path.name})
            if path.exists():
                print(f"  있음: {path.name}"); continue
            try:
                run_nlm("content", "source", s["id"], "--output", str(path), parse_json=False, profile=ws.profile)
                print(f"  받음: {path.name}")
            except NlmwError as e:
                print(f"  실패: {s['title']} ({str(e).splitlines()[-1][:120]})")
        (out / "_sources.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.images:
            _images(ws, nb, None)
        if args.studio:
            _pull(ws, nb)


# ---------------- images (소스 속 원본 그림) ----------------
IMG_EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}


def cmd_images(args) -> None:
    ws = find_workspace()
    _images(ws, resolve_notebook(args.notebook, ws), args.source)


def _images(ws: Workspace, nb: dict, source_filter: str | None) -> None:
    import httpx
    cf = cookie_file(ws.profile)
    if not cf.exists():
        raise NlmwError(f"nlm 로그인 쿠키가 없습니다({cf}). `nlm login`을 먼저 하세요.")
    raw = json.loads(cf.read_text(encoding="utf-8"))
    items = raw if isinstance(raw, list) else raw.get("cookies", raw)
    jar = httpx.Cookies()
    if isinstance(items, dict):
        for k, v in items.items():
            jar.set(k, v, domain=".google.com")
    else:
        for c in items:
            jar.set(c["name"], c["value"], domain=c.get("domain", ".google.com"))
    out_root = ws.notebook_dirs(nb["title"])["from_lm"] / "images"
    sources = run_nlm("list", "sources", nb["id"], "--json", profile=ws.profile)
    if source_filter:
        sources = [s for s in sources if source_filter.lower() in s["title"].lower()]
    with httpx.Client(cookies=jar, follow_redirects=True, timeout=30) as client:
        for src in sources:
            content = run_nlm("content", "source", src["id"], "--json", profile=ws.profile).get("content", "")
            urls = re.findall(r"https://lh3\.googleusercontent\.com/\S+", content)
            if not urls:
                continue
            folder = out_root / safe_name(Path(src["title"]).stem)
            folder.mkdir(parents=True, exist_ok=True)
            saved = 0
            for i, url in enumerate(urls, 1):
                if any(folder.glob(f"{i:02d}.*")):
                    continue
                resp = client.get(url)
                ctype = resp.headers.get("content-type", "").split(";")[0]
                if resp.status_code != 200 or not ctype.startswith("image"):
                    print(f"  {src['title']} #{i}: 받지 못함 ({resp.status_code}, {ctype}) - `nlm login`을 다시 해보세요"); continue
                (folder / f"{i:02d}{IMG_EXT.get(ctype, '.img')}").write_bytes(resp.content)
                saved += 1
            print(f"{src['title']}: 그림 {len(urls)}개 중 새로 {saved}개 → {folder}")


# ---------------- pull (스튜디오 결과물) ----------------
KINDS = {  # 종류 → (nlm download 하위 명령, 폴더, 확장자, 추가 옵션)
    "infographic": ("infographic", "infographics", ".png", []), "audio": ("audio", "audio", ".m4a", []),
    "video": ("video", "video", ".mp4", []), "slide_deck": ("slide-deck", "slides", ".pdf", []),
    "report": ("report", "reports", ".md", []), "mind_map": ("mind-map", "study", ".json", []),
    "data_table": ("data-table", "study", ".csv", []), "quiz": ("quiz", "study", ".md", ["--format", "markdown"]),
    "flashcards": ("flashcards", "study", ".md", ["--format", "markdown"]),
}


def cmd_pull(args) -> None:
    ws = find_workspace()
    _pull(ws, resolve_notebook(args.notebook, ws))


def _pull(ws: Workspace, nb: dict) -> None:
    base = ws.notebook_dirs(nb["title"])["from_lm"]
    for art in run_nlm("status", "artifacts", nb["id"], "--json", profile=ws.profile):
        kind = (art.get("type") or "").replace("-", "_").lower()
        aid = art.get("id") or art.get("artifact_id") or ""
        if art.get("status") != "completed":
            print(f"{kind} {aid[:8]}: 아직 {art.get('status')} - 건너뜀"); continue
        if kind not in KINDS:
            print(f"{kind} {aid[:8]}: 지원하지 않는 종류 - 건너뜀"); continue
        sub, folder, ext, extra = KINDS[kind]
        out_dir = base / folder
        out_dir.mkdir(parents=True, exist_ok=True)
        if any(out_dir.glob(f"{kind}_{aid[:8]}*")):
            continue
        out = out_dir / f"{kind}_{aid[:8]}{ext}"
        try:
            run_nlm("download", sub, nb["id"], "--id", aid, "--output", str(out), *extra,
                    *(["--no-progress"] if kind in ("infographic", "audio", "video", "slide_deck") else []),
                    parse_json=False, profile=ws.profile)
            print(f"{kind} {aid[:8]}: 저장 → {out}")
        except NlmwError as err:
            print(f"{kind} {aid[:8]}: 실패 - {err}")


# ---------------- pdf ----------------
def find_browser() -> str | None:
    cands = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for c in cands:
        if Path(c).exists():
            return c
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "msedge", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    return None


def cmd_pdf(args) -> None:
    html = Path(args.html).resolve()
    if not html.exists():
        raise NlmwError(f"파일이 없습니다: {html}")
    out = Path(args.out).resolve() if args.out else html.with_suffix(".pdf")
    browser = find_browser()
    if not browser:
        raise NlmwError("Chrome, Edge, Chromium 중 하나가 필요합니다.")
    # 이미 열린 브라우저로 요청이 넘어가지 않게 매번 임시 프로필로 독립 실행
    out.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--user-data-dir={profile}",
                        f"--virtual-time-budget={args.wait * 1000}", f"--print-to-pdf={out}", html.as_uri()], capture_output=True)
        last = -1
        for _ in range(120):  # 브라우저가 PDF를 다 쓰기 전에 반환할 수 있어 크기가 멈출 때까지 대기
            size = out.stat().st_size if out.exists() else -1
            if size > 0 and size == last:
                break
            last = size
            time.sleep(0.5)
    if not out.exists():
        raise NlmwError("PDF를 만들지 못했습니다.")
    pages = len(re.findall(rb"/Type\s*/Page[^s]", out.read_bytes()))
    print(f"저장: {out} ({pages}페이지)")
