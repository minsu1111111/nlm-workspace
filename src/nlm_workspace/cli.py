"""nlmw 명령줄 진입점."""
from __future__ import annotations

import argparse
import sys

from . import __version__, commands
from .core import NlmwError, setup_console

HELP = """NotebookLM(nlm CLI) 작업 폴더 도구

처음 한 번:  nlm login  →  nlmw init  →  nlmw doctor  →  nlmw sync
"""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="nlmw", description=HELP, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version=f"nlmw {__version__}")
    sub = p.add_subparsers(dest="cmd", metavar="<명령>")

    s = sub.add_parser("init", help="작업 폴더 만들기 (폴더 구조, nlmw.json, CLAUDE.md, .gitignore)")
    s.add_argument("dir", nargs="?", default=".", help="작업 폴더 (기본: 현재 폴더)")
    s.add_argument("--profile", help="nlm 프로필 이름 (Google 계정 여러 개일 때)")
    s.set_defaults(func=commands.cmd_init)

    s = sub.add_parser("doctor", help="설치·로그인·브라우저 점검")
    s.set_defaults(func=commands.cmd_doctor)

    s = sub.add_parser("sync", help="노트북 목록 → notebooks.md, 노트북별 폴더 만들기")
    s.add_argument("--only", help="제목에 이 글자가 든 노트북만")
    s.add_argument("--no-dirs", action="store_true", help="목록만 기록하고 폴더는 만들지 않음")
    s.set_defaults(func=commands.cmd_sync)

    s = sub.add_parser("upload", help="01_upload/<노트북>/ 파일을 소스로 올리고 _uploaded/로 이동")
    s.add_argument("notebook", help="노트북 제목, 제목 일부, 또는 ID")
    s.add_argument("--dry-run", action="store_true", help="올릴 파일만 보여 줌")
    s.set_defaults(func=commands.cmd_upload)

    s = sub.add_parser("restore", help="소스 텍스트 다시 받기 (새 PC에서 이어서 쓸 때)")
    s.add_argument("notebook", nargs="?")
    s.add_argument("--all", action="store_true", help="모든 노트북")
    s.add_argument("--images", action="store_true", help="소스 속 원본 그림도")
    s.add_argument("--studio", action="store_true", help="스튜디오 결과물도")
    s.set_defaults(func=commands.cmd_restore)

    s = sub.add_parser("images", help="소스 속 원본 그림 받기 (NotebookLM 그림 설명 검증용)")
    s.add_argument("notebook")
    s.add_argument("--source", help="소스 제목 일부")
    s.set_defaults(func=commands.cmd_images)

    s = sub.add_parser("pull", help="완료된 스튜디오 결과물(인포그래픽·오디오·슬라이드 등) 받기")
    s.add_argument("notebook")
    s.set_defaults(func=commands.cmd_pull)

    s = sub.add_parser("pdf", help="HTML → PDF (Chrome/Edge headless, @page 설정 따름)")
    s.add_argument("html")
    s.add_argument("--out", help="저장할 PDF 경로 (기본: 같은 이름 .pdf)")
    s.add_argument("--wait", type=int, default=3, help="스크립트·수식 렌더링을 기다릴 초 (기본 3)")
    s.set_defaults(func=commands.cmd_pdf)

    s = sub.add_parser("nlm", help="nlm 명령을 그대로 실행 (PATH에 nlm이 없을 때)")
    s.add_argument("rest", nargs=argparse.REMAINDER)
    s.set_defaults(func=commands.cmd_nlm)
    return p


def main(argv: list[str] | None = None) -> None:
    setup_console()
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["nlm"]:  # nlm 옵션(--version 등)을 argparse가 가로채지 않게 그대로 넘긴다
        try:
            commands.cmd_nlm(argparse.Namespace(rest=argv[1:]))
        except NlmwError as e:
            print(f"오류: {e}", file=sys.stderr); sys.exit(1)
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help(); return
    try:
        args.func(args)
    except NlmwError as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
