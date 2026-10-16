"""새 PC에서 NotebookLM에 올려 둔 소스를 다시 불러온다.

NotebookLM은 올린 원본 파일(pdf, pptx 등)을 그대로 돌려주지 않는다. 대신 다음을 받는다.
  - 소스별 추출 텍스트  → 02_from-lm/<노트북>/sources/<소스 제목>.txt
  - (--images) 소스 속 원본 그림 → tools/fetch_images.py와 같은 폴더
  - (--studio) 스튜디오 결과물(인포그래픽·오디오·슬라이드 등) → tools/pull.py와 같은 폴더

사용: python tools/restore.py <노트북 제목|ID>  [--images] [--studio]
      python tools/restore.py --all               (모든 노트북의 텍스트)
이미 받은 텍스트 파일은 건너뛴다.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from _common import ensure_dirs, list_notebooks, resolve_notebook, run_nlm, safe_name

HERE = Path(__file__).resolve().parent


def restore(nb: dict, images: bool, studio: bool) -> None:
    dirs = ensure_dirs(nb["title"])
    out = dirs["from_lm"] / "sources"
    out.mkdir(parents=True, exist_ok=True)
    sources = run_nlm("list", "sources", nb["id"], "--json")
    manifest = []
    print(f"\n== {nb['title']} ({len(sources)}개 소스)")
    for s in sources:
        path = out / f"{safe_name(s['title'])}.txt"
        manifest.append({"id": s["id"], "title": s["title"], "type": s.get("type"), "file": path.name})
        if path.exists():
            print(f"  있음: {path.name}")
            continue
        try:
            run_nlm("content", "source", s["id"], "--output", str(path), parse_json=False)
            print(f"  받음: {path.name}")
        except RuntimeError as e:
            print(f"  실패: {s['title']} ({str(e).splitlines()[-1][:120]})")
    (out / "_sources.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    if images:
        subprocess.run([sys.executable, str(HERE / "fetch_images.py"), nb["id"]])
    if studio:
        subprocess.run([sys.executable, str(HERE / "pull.py"), nb["id"]])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook", nargs="?")
    parser.add_argument("--all", action="store_true", help="모든 노트북")
    parser.add_argument("--images", action="store_true", help="소스 속 원본 그림도 받기")
    parser.add_argument("--studio", action="store_true", help="스튜디오 결과물도 받기")
    args = parser.parse_args()
    if args.all:
        targets = list_notebooks()
    elif args.notebook:
        targets = [resolve_notebook(args.notebook)]
    else:
        parser.error("노트북 이름(또는 --all)을 주세요")
    for nb in targets:
        restore(nb, args.images, args.studio)
    print("\n완료. 텍스트는 02_from-lm/<노트북>/sources/ 에 있습니다.")


if __name__ == "__main__":
    main()
