#!/usr/bin/env bash
# nlm-workspace 설치 (macOS / Linux) — 이 저장소를 clone한 폴더에서 실행:  bash setup.sh
set -euo pipefail
cd "$(dirname "$0")"

PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)'; then PY="$c"; break; fi
done
[ -n "$PY" ] || { echo "파이썬 3.10 이상이 필요합니다."; exit 1; }
echo "파이썬: $($PY --version)"

"$PY" -m pip install --user --upgrade pip >/dev/null
"$PY" -m pip install --user -e ".[study]"

BIN="$("$PY" -c 'import sysconfig,os; print(sysconfig.get_path("scripts", os.name+"_user"))')"
case ":$PATH:" in *":$BIN:"*) ;; *) export PATH="$PATH:$BIN"; echo "참고: ~/.bashrc 또는 ~/.zshrc에 추가하세요 → export PATH=\"\$PATH:$BIN\"";; esac

nlmw init .
echo
echo "설치 완료. 다음:  nlm login  →  nlmw doctor  →  nlmw sync"
