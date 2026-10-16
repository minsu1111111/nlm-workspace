"""공용: 작업 폴더 찾기, 설정, nlm 실행, 노트북 찾기."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

CONFIG_NAME = "nlmw.json"
DEFAULT_FOLDERS = {
    "upload": "01_upload",     # NotebookLM에 올릴 파일
    "from_lm": "02_from-lm",   # NotebookLM에서 받은 것
    "work": "03_work",         # Claude 작업물
    "final": "04_final",       # 제출·공유용 최종본
    "inbox": "inbox",          # 분류 전
}


class NlmwError(Exception):
    """사용자에게 그대로 보여 줄 오류."""


def setup_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


# ---------------- 작업 폴더 ----------------
class Workspace:
    def __init__(self, root: Path, config: dict):
        self.root = root
        self.config = config
        folders = {**DEFAULT_FOLDERS, **config.get("folders", {})}
        self.upload = root / folders["upload"]
        self.from_lm = root / folders["from_lm"]
        self.work = root / folders["work"]
        self.final = root / folders["final"]
        self.inbox = root / folders["inbox"]
        self.profile = config.get("profile")  # nlm 프로필 (여러 계정일 때)

    def notebook_dirs(self, title: str) -> dict[str, Path]:
        name = safe_name(title)
        dirs = {
            "upload": self.upload / name,
            "uploaded": self.upload / name / "_uploaded",
            "from_lm": self.from_lm / name,
            "work": self.work / name,
            "final": self.final / name,
        }
        for d in dirs.values():
            d.mkdir(parents=True, exist_ok=True)
        return dirs


def find_workspace(start: Path | None = None) -> Workspace:
    """NLMW_ROOT 환경 변수, 또는 현재 폴더에서 위로 올라가며 nlmw.json을 찾는다."""
    env = os.environ.get("NLMW_ROOT")
    candidates = [Path(env)] if env else [p for p in [(start or Path.cwd()).resolve(), *(start or Path.cwd()).resolve().parents]]
    for p in candidates:
        cfg = p / CONFIG_NAME
        if cfg.exists():
            return Workspace(p, json.loads(cfg.read_text(encoding="utf-8")))
    raise NlmwError("작업 폴더를 찾지 못했습니다. 작업할 폴더에서 `nlmw init`을 먼저 실행하세요.")


# ---------------- 이름·경로 ----------------
def safe_name(title: str) -> str:
    """노트북·소스 제목을 폴더/파일 이름으로 쓸 수 있게 정리 (Windows 금지 문자 제거)."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title).strip().rstrip(".")
    return name[:80] or "untitled"


def unique_path(path: Path) -> Path:
    """같은 이름이 있으면 ' (2)', ' (3)'을 붙인다."""
    if not path.exists():
        return path
    n = 2
    while True:
        candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
        if not candidate.exists():
            return candidate
        n += 1


# ---------------- nlm 실행 ----------------
def nlm_exe() -> str:
    found = shutil.which("nlm")
    if found:
        return found
    # pip install --user로 설치하면 사용자 Scripts/bin 폴더가 PATH에 없을 수 있다
    for scheme in (f"{os.name}_user", "nt_user", "posix_user", "osx_framework_user"):
        try:
            scripts = Path(sysconfig.get_path("scripts", scheme))
        except KeyError:
            continue
        for exe in ("nlm.exe", "nlm"):
            if (scripts / exe).exists():
                return str(scripts / exe)
    raise NlmwError("nlm을 찾을 수 없습니다. `python -m pip install notebooklm-mcp-cli`로 설치한 뒤 다시 실행하세요.")


def nlm_env() -> dict:
    return dict(os.environ, PYTHONIOENCODING="utf-8")


def run_nlm(*args: str, parse_json: bool = True, profile: str | None = None):
    cmd = [nlm_exe(), *args]
    if profile:
        cmd += ["--profile", profile]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=nlm_env())
    if proc.returncode != 0:
        msg = (proc.stderr.strip() or proc.stdout.strip())
        hint = "\n→ 로그인이 만료됐을 수 있습니다. `nlm login`을 다시 하세요." if re.search(r"auth|login|cookie|401|403", msg, re.I) else ""
        raise NlmwError(f"nlm {' '.join(args)} 실패:\n{msg[-800:]}{hint}")
    out = proc.stdout.lstrip("﻿").strip()
    if not parse_json:
        return out
    starts = [i for i in (out.find("["), out.find("{")) if i != -1]
    if not starts:
        raise NlmwError(f"JSON 응답이 아닙니다:\n{out[:500]}")
    return json.loads(out[min(starts):])


# ---------------- 노트북 ----------------
def list_notebooks(ws: Workspace | None = None) -> list[dict]:
    return run_nlm("list", "notebooks", profile=ws.profile if ws else None)


def resolve_notebook(query: str, ws: Workspace | None = None) -> dict:
    """ID, 정확한 제목, 폴더 이름, 제목 일부 순으로 노트북을 찾는다."""
    notebooks = list_notebooks(ws)
    for nb in notebooks:
        if query in (nb["id"], nb["title"], safe_name(nb["title"])):
            return nb
    matches = [nb for nb in notebooks if query.lower() in nb["title"].lower()]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise NlmwError(f"'{query}'에 해당하는 노트북이 없습니다. `nlmw sync`로 목록을 확인하세요.")
    names = "\n  ".join(nb["title"] for nb in matches)
    raise NlmwError(f"'{query}'에 해당하는 노트북이 여러 개입니다:\n  {names}")


def cookie_file(profile: str | None) -> Path:
    return Path.home() / ".notebooklm-mcp-cli" / "profiles" / (profile or "default") / "cookies.json"
