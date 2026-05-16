@echo off
REM Open a new cmd window that runs run.bat and stays open so errors are visible
setlocal
set "SCRIPT=%~dp0run.bat"
if not exist "%SCRIPT%" (
  echo run.bat not found in %~dp0
  pause
  exit /b 1
)
start "MediaDownloader" cmd /k "%SCRIPT%"
exit /b 0
