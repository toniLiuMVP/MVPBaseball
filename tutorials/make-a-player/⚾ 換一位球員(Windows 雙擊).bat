@echo off
REM TOOL_DATE = '2026-09-24'
REM  Double-click this file. A window will open and ask you questions.
REM  (This file must stay ASCII: Windows reads .bat as cp950 and Chinese
REM   comments can shift the decoder and break the script.)
setlocal
cd /d "%~dp0"
cls

REM  The Microsoft Store ships a fake "python3" that only opens the Store,
REM  and an old Python 2 or 3.6 also answers to these names.
REM  So really run each one and keep the first that is Python 3.7 or newer
REM  (the tool needs 3.7). The check below exits 0 only on 3.7 or newer.
set PY=
for %%C in (python py python3) do (
  if not defined PY (
    %%C -c "import sys; raise SystemExit(sys.version_info < (3,7))" >nul 2>&1 && set PY=%%C
  )
)

if not defined PY (
  echo.
  echo   This computer does not have Python 3.7 or newer yet.
  echo   An older Python does not count: this tool needs 3.7 or newer.
  echo   Get it from https://www.python.org/downloads/
  echo   If the installer shows "Add python.exe to PATH", tick it.
  echo.
  pause
  exit /b 1
)

%PY% mvp_player.py
echo.
pause
