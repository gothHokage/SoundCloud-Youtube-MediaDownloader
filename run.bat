@echo off
setlocal enabledelayedexpansion

if not exist venv (
    echo venv not found. Running install.bat...
    call install.bat
    if errorlevel 1 exit /b 1
)

if exist venv\Scripts\python.exe (
    set PYTHONPATH=%CD%
    REM load HOST and PORT from .env using findstr
    if exist .env (
        for /f "usebackq tokens=1* delims==" %%A in (`findstr /b "HOST=" .env`) do set HOST=%%B
        for /f "usebackq tokens=1* delims==" %%A in (`findstr /b "PORT=" .env`) do set PORT=%%B
    )
    REM For reliability we start server on 127.0.0.1:8080 by default.
    REM If you need to change host/port, set environment variables before running.
    set HOST_TO_USE=127.0.0.1
    set PORT=8080
    echo Starting server on !HOST_TO_USE!:!PORT!
    echo Checking host resolution...
    venv\Scripts\python.exe app\check_host.py !HOST_TO_USE!
    if errorlevel 1 (
      echo Host resolution failed. Check .env HOST value or network/DNS settings.
      pause
      exit /b 1
    )
    echo Starting server on !HOST_TO_USE!:!PORT!
    venv\Scripts\python.exe -m uvicorn app.main:app --host !HOST_TO_USE! --port !PORT! --reload
) else (
    echo venv not found or broken. Run install.bat first.
    exit /b 1
)
