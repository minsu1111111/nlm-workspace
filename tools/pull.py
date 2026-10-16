"""NotebookLM 스튜디오 결과물(인포그래픽, 오디오, 슬라이드 등)을 종류별 폴더로 내려받는다.

사용: python tools/pull.py <노트북 제목|ID>
저장: 02_from-lm/<노트북>/{infographics,audio,video,slides,reports,study}/
이미 받은 결과물(파일 이름에 ID 앞 8자리)은 건너뛴다.
"""
import argparse

from _common import ensure_dirs, resolve_notebook, run_nlm

# 결과물 종류 → (nlm download 하위 명령, 저장 폴더, 확장자, 추가 옵션)
KINDS = {
    "infographic": ("infographic", "infographics", ".png", []),
    "audio": ("audio", "audio", ".m4a", []),
    "video": ("video", "video", ".mp4", []),
    "slide_deck": ("slide-deck", "slides", ".pdf", []),
    "report": ("report", "reports", ".md", []),
    "mind_map": ("mind-map", "study", ".json", []),
    "data_table": ("data-table", "study", ".csv", []),
    "quiz": ("quiz", "study", ".md", ["--format", "markdown"]),
    "flashcards": ("flashcards", "study", ".md", ["--format", "markdown"]),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook")
    args = parser.parse_args()

    nb = resolve_notebook(args.notebook)
    base = ensure_dirs(nb["title"])["from_lm"]
    artifacts = run_nlm("status", "artifacts", nb["id"], "--json")

    for art in artifacts:
        kind = (art.get("type") or "").replace("-", "_").lower()
        aid = art.get("id") or art.get("artifact_id")
        if art.get("status") != "completed":
            print(f"{kind} {aid[:8]}: 아직 {art.get('status')} - 건너뜀")
            continue
        if kind not in KINDS:
            print(f"{kind} {aid[:8]}: 지원하지 않는 종류 - 건너뜀")
            continue
        cmd, folder, ext, extra = KINDS[kind]
        out_dir = base / folder
        out_dir.mkdir(parents=True, exist_ok=True)
        if any(out_dir.glob(f"{kind}_{aid[:8]}*")):
            continue
        out = out_dir / f"{kind}_{aid[:8]}{ext}"
        try:
            run_nlm("download", cmd, nb["id"], "--id", aid, "--output", str(out), *extra,
                    *(["--no-progress"] if kind in ("infographic", "audio", "video", "slide_deck") else []),
                    parse_json=False)
            print(f"{kind} {aid[:8]}: 저장 → {out.relative_to(base.parent.parent)}")
        except RuntimeError as err:
            print(f"{kind} {aid[:8]}: 실패 - {err}")


if __name__ == "__main__":
    main()
