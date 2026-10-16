"""nlm-workspace 공용 헬퍼: 경로, nlm 실행, 노트북 찾기."""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPLOAD = ROOT / "01_upload"
FROM_LM = ROOT / "02_from-lm"
WORK = ROOT / "03_work"
FINAL = ROOT / "04_final"

# Microsoft Store Python의 Scripts 폴더 (PATH에 없을 때 대비)
_STORE_SCRIPTS = Path.home() / (
    "AppData/Local/Packages/PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0"
    "/LocalCache/local-packages/Python311/Scripts"
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def nlm_exe() -> str:
    found = shutil.which("nlm")
    if found:
        return found
    candidate = _STORE_SCRIPTS / "nlm.exe"
    if candidate.exists():
        return str(candidate)
    sys.exit("nlm을 찾을 수 없습니다. pip install notebooklm-mcp-cli 후 다시 실행하세요.")


def run_nlm(*args: str, parse_json: bool = True):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    proc = subprocess.run(
        [nlm_exe(), *args], capture_output=True, text=True, encoding="utf-8", env=env
    )
    if proc.returncode != 0:
        raise RuntimeError(f"nlm {' '.join(args)} 실패:\n{proc.stderr.strip() or proc.stdout.strip()}")
    out = proc.stdout.lstrip("﻿").strip()
    if not parse_json:
        return out
    start = min((i for i in (out.find("["), out.find("{")) if i != -1), default=-1)
    if start == -1:
        raise RuntimeError(f"JSON 응답이 아닙니다:\n{out[:500]}")
    return json.loads(out[start:])


def safe_name(title: str) -> str:
    """노트북 제목을 Windows 폴더 이름으로 쓸 수 있게 정리."""
    name = re.sub(r'[<>:"/\\|?*]', "_", title).strip().rstrip(".")
    return name[:80] or "untitled"


def list_notebooks() -> list[dict]:
    return run_nlm("list", "notebooks")


def resolve_notebook(query: str) -> dict:
    """ID, 정확한 제목, 폴더 이름, 제목 일부 순으로 노트북을 찾는다."""
    notebooks = list_notebooks()
    for nb in notebooks:
        if query in (nb["id"], nb["title"], safe_name(nb["title"])):
            return nb
    matches = [nb for nb in notebooks if query.lower() in nb["title"].lower()]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        sys.exit(f"'{query}'에 해당하는 노트북이 없습니다. python tools/sync.py로 목록을 확인하세요.")
    names = "\n  ".join(nb["title"] for nb in matches)
    sys.exit(f"'{query}'에 해당하는 노트북이 여러 개입니다:\n  {names}")


def ensure_dirs(title: str) -> dict[str, Path]:
    name = safe_name(title)
    dirs = {
        "upload": UPLOAD / name,
        "uploaded": UPLOAD / name / "_uploaded",
        "from_lm": FROM_LM / name,
        "work": WORK / name,
        "final": FINAL / name,
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


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
