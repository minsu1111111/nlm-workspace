"""01_upload/<노트북>/ 에 넣어 둔 파일을 NotebookLM 소스로 올리고 _uploaded/ 로 옮긴다.

사용: python tools/upload.py <노트북 제목|ID> [--dry-run]
"""
import argparse
import shutil

from _common import ensure_dirs, resolve_notebook, run_nlm, unique_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook")
    parser.add_argument("--dry-run", action="store_true", help="올릴 파일만 보여주고 올리지 않음")
    args = parser.parse_args()

    nb = resolve_notebook(args.notebook)
    dirs = ensure_dirs(nb["title"])
    files = sorted(p for p in dirs["upload"].iterdir() if p.is_file() and not p.name.startswith("."))
    if not files:
        print(f"올릴 파일이 없습니다: {dirs['upload']}")
        return

    for path in files:
        if args.dry_run:
            print(f"[올릴 예정] {path.name}")
            continue
        print(f"올리는 중: {path.name} ...", flush=True)
        try:
            result = run_nlm("source", "add", nb["id"], "--file", str(path),
                             "--title", path.stem, "--wait", "--json")
        except RuntimeError as err:
            print(f"  실패: {err}")
            continue
        dest = unique_path(dirs["uploaded"] / path.name)
        shutil.move(str(path), dest)
        print(f"  완료 (source_id {result.get('source_id', '?')}) → _uploaded/{dest.name}")


if __name__ == "__main__":
    main()
