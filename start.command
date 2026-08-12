#!/bin/bash
# ─────────────────────────────────────────────
#  AI 면접 시스템 실행 (macOS)
#  이 파일을 더블클릭하면 브라우저가 열립니다.
#  종료할 때는 이 검은 창에서 Control + C
# ─────────────────────────────────────────────
cd "$(dirname "$0")/deploy"
PORT=8000

open_browser () { sleep 1; open "http://localhost:$PORT"; }

if command -v python3 >/dev/null 2>&1; then
  open_browser &
  echo "서버 실행 중 ...  http://localhost:$PORT"
  python3 -m http.server $PORT
elif command -v python >/dev/null 2>&1; then
  open_browser &
  echo "서버 실행 중 ...  http://localhost:$PORT"
  python -m SimpleHTTPServer $PORT
elif command -v npx >/dev/null 2>&1; then
  open_browser &
  echo "서버 실행 중 ...  http://localhost:$PORT"
  npx --yes serve -l $PORT .
else
  echo ""
  echo "  Python 또는 Node가 설치되어 있지 않습니다."
  echo "  터미널에 아래 명령을 붙여넣어 설치한 뒤 다시 실행해 주세요."
  echo ""
  echo "      xcode-select --install"
  echo ""
  read -n 1 -s -r -p "  아무 키나 누르면 닫힙니다."
fi
