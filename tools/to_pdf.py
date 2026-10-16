"""HTML 페이지를 Edge(headless)로 PDF로 만든다. 페이지 크기는 HTML의 @page 설정을 따른다.

사용: python tools/to_pdf.py <html 파일> [--out 결과.pdf]
기본 저장 위치: html과 같은 폴더, 같은 이름의 .pdf
"""
import argparse
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import _common  # noqa: F401  (콘솔 UTF-8 설정)

EDGE_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("html")
    parser.add_argument("--out")
    args = parser.parse_args()

    html = Path(args.html).resolve()
    if not html.exists():
        sys.exit(f"파일이 없습니다: {html}")
    out = Path(args.out).resolve() if args.out else html.with_suffix(".pdf")
    edge = next((p for p in EDGE_CANDIDATES if p.exists()), None)
    if edge is None:
        sys.exit("Microsoft Edge를 찾을 수 없습니다.")

    # 이미 열린 Edge 창이 있으면 요청이 그쪽으로 넘어가 비동기로(이전 내용으로) 저장될 수 있어서
    # 매번 임시 프로필로 독립 실행하고, 이전 결과물은 먼저 지운다.
    out.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        subprocess.run(
            [str(edge), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
             f"--user-data-dir={profile}", f"--print-to-pdf={out}", html.as_uri()],
            capture_output=True,
        )
        # msedge.exe는 PDF를 다 쓰기 전에 반환하므로 파일 크기가 멈출 때까지 기다린다.
        last = -1
        for _ in range(120):
            size = out.stat().st_size if out.exists() else -1
            if size > 0 and size == last:
                break
            last = size
            time.sleep(0.5)
    if not out.exists():
        sys.exit("PDF를 만들지 못했습니다.")
    pages = len(re.findall(rb"/Type\s*/Page[^s]", out.read_bytes()))
    print(f"저장: {out} ({pages}페이지)")


if __name__ == "__main__":
    main()
