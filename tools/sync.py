"""NotebookLM 노트북 목록을 notebooks.md에 기록하고 노트북별 01~04 폴더를 만든다.

사용: python tools/sync.py
"""
from datetime import datetime

from _common import ROOT, ensure_dirs, list_notebooks, safe_name


def main() -> None:
    notebooks = sorted(list_notebooks(), key=lambda nb: nb.get("updated_at") or "", reverse=True)
    lines = [
        "# NotebookLM 노트북 목록",
        "",
        f"마지막 동기화: {datetime.now():%Y-%m-%d %H:%M} (`python tools/sync.py`로 갱신)",
        "",
        "| 제목 | 폴더 이름 | 소스 | 마지막 수정 | ID |",
        "|---|---|---|---|---|",
    ]
    for nb in notebooks:
        ensure_dirs(nb["title"])
        updated = (nb.get("updated_at") or "")[:10]
        lines.append(
            f"| {nb['title']} | {safe_name(nb['title'])} | {nb.get('source_count', '')} "
            f"| {updated} | `{nb['id']}` |"
        )
    (ROOT / "notebooks.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"노트북 {len(notebooks)}개를 notebooks.md에 기록하고 폴더를 만들었습니다.")


if __name__ == "__main__":
    main()
