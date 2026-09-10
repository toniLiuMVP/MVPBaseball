@echo off
REM  Double-click this file. A window will open and ask you questions.
REM  (This file must stay ASCII: Windows reads .bat as cp950 and Chinese
REM   comments can shift the decoder and break the script.)
setlocal
cd /d "%~dp0"
cls

REM  The Microsoft Store ships a fake "python3" that only opens the Store.
REM  So try "python" first and check it really prints a version.
set PY=
for %%C in (python py python3) do (
  if not defined PY (
    %%C --version >nul 2>&1 && set PY=%%C
  )
)

if not defined PY (
  echo.
  echo   This computer does not have Python yet.
  echo   Get it from https://www.python.org/downloads/
  echo   During install, tick "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)

%PY% mvp_player.py
echo.
pause
