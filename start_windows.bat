@echo off
chcp 65001 >nul
REM ─────────────────────────────────────────────
REM  AI 면접 시스템 실행 (Windows)
REM  이 파일을 더블클릭하세요.
REM  검은 창은 면접이 끝날 때까지 닫지 마세요.
REM ─────────────────────────────────────────────
cd /d "%~dp0deploy"
set PORT=8000

REM 1순위: 진짜 Python 이 설치돼 있는 경우
REM (스토어 연결용 가짜 python 은 --version 에서 실패하므로 걸러집니다)
python --version >nul 2>nul
if %errorlevel%==0 (
  echo.
  echo   서버 실행 중 ...  http://localhost:%PORT%
  echo   이 창을 닫으면 면접 프로그램이 중단됩니다.
  echo.
  start "" http://localhost:%PORT%
  python -m http.server %PORT%
  goto :end
)

REM 2순위: py 런처
py --version >nul 2>nul
if %errorlevel%==0 (
  echo.
  echo   서버 실행 중 ...  http://localhost:%PORT%
  echo   이 창을 닫으면 면접 프로그램이 중단됩니다.
  echo.
  start "" http://localhost:%PORT%
  py -m http.server %PORT%
  goto :end
)

REM 3순위: 윈도우 기본 내장 PowerShell (설치 불필요)
if exist "%~dp0server.ps1" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0server.ps1"
  goto :end
)

echo.
echo   실행 환경을 찾지 못했습니다.
echo   server.ps1 파일이 이 폴더에 함께 있는지 확인해 주세요.
echo.
pause

:end
