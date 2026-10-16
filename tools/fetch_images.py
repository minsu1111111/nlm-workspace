"""NotebookLM 소스(PDF, 슬라이드 등) 속 원본 그림을 내려받는다.

NotebookLM의 요약·그림 설명은 틀릴 때가 있어서, 문제 그림은 원본으로 확인해야 한다.
nlm 로그인 쿠키(~/.notebooklm-mcp-cli)를 써서 이미지 URL을 받는다.

사용: python tools/fetch_images.py <노트북 제목|ID> [--source 소스 제목 일부]
저장: 02_from-lm/<노트북>/images/<소스 이름>/01.jpg ...
"""
import argparse
import json
import re
from pathlib import Path

import httpx

from _common import ensure_dirs, resolve_notebook, run_nlm, safe_name

COOKIE_FILE = Path.home() / ".notebooklm-mcp-cli/profiles/default/cookies.json"
EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}


def load_cookies() -> httpx.Cookies:
    raw = json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
    items = raw if isinstance(raw, list) else raw.get("cookies", raw)
    jar = httpx.Cookies()
    if isinstance(items, dict):
        for name, value in items.items():
            jar.set(name, value, domain=".google.com")
    else:
        for c in items:
            jar.set(c["name"], c["value"], domain=c.get("domain", ".google.com"))
    return jar


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook")
    parser.add_argument("--source", help="소스 제목의 일부 (생략하면 전체 소스)")
    args = parser.parse_args()

    nb = resolve_notebook(args.notebook)
    out_root = ensure_dirs(nb["title"])["from_lm"] / "images"
    sources = run_nlm("list", "sources", nb["id"], "--json")
    if args.source:
        sources = [s for s in sources if args.source.lower() in s["title"].lower()]
    if not sources:
        print("해당하는 소스가 없습니다.")
        return

    with httpx.Client(cookies=load_cookies(), follow_redirects=True, timeout=30) as client:
        for src in sources:
            content = run_nlm("content", "source", src["id"]).get("content", "")
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
                    print(f"  {src['title']} #{i}: 받지 못함 ({resp.status_code}, {ctype}) - nlm login을 다시 해보세요")
                    continue
                (folder / f"{i:02d}{EXT.get(ctype, '.img')}").write_bytes(resp.content)
                saved += 1
            print(f"{src['title']}: 그림 {len(urls)}개 중 새로 {saved}개 저장 → {folder}")


if __name__ == "__main__":
    main()
