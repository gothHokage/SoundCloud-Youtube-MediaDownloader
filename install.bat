@echo off
setlocal enabledelayedexpansion

echo Creating virtual environment (venv)...
if not exist venv (
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment. Ensure Python 3.11+ is installed and on PATH.
        exit /b 1
    )
)

echo Installing dependencies into venv...
if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe -m pip install --upgrade pip
    venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo pip install failed. Try running the following manually:
        echo venv\Scripts\python.exe -m pip install -r requirements.txt
        exit /b 1
    )
) else (
    echo venv\Scripts\python.exe not found. Virtual environment may not have been created.
    exit /b 1
)

echo.
echo Checking ffmpeg...
where ffmpeg >nul 2>nul
if %errorlevel% equ 0 (
    echo ffmpeg found on PATH.
) else if exist app\ffmpeg.exe (
    echo ffmpeg found in app\ffmpeg.exe
) else (
    echo ffmpeg not found. Downloading...
    set "FFMPEG_URL=https://github.com/ffbinaries/ffbinaries-prebuilt/releases/download/v6.1/ffmpeg-6.1-win-64.zip"
    set "ZIP=%TEMP%\ffmpeg.zip"
    powershell -Command "try{Invoke-WebRequest -Uri '%FFMPEG_URL%' -OutFile '%ZIP%' -UseBasicParsing;Write-Host Downloaded}catch{Write-Host 'Download failed: '+$_.Exception.Message;exit 1}"
    if exist "%ZIP%" (
        powershell -Command "try{$z=[System.IO.Compression.ZipFile]::OpenRead('%ZIP%');$e=$z.Entries|Where{$_.Name -eq 'ffmpeg.exe'}|Select-Object -First 1;[System.IO.Compression.ZipFileExtensions]::ExtractToFile($e,'app\ffmpeg.exe',$true);$z.Dispose();Write-Host Extracted}catch{Write-Host 'Extract failed: '+$_.Exception.Message;exit 1}"
        del "%ZIP%" 2>nul
    )
    if exist app\ffmpeg.exe (
        echo ffmpeg installed to app\ffmpeg.exe
    ) else (
        echo.
        echo WARNING: Could not download ffmpeg. Some features will be limited.
        echo To install manually, run: install-ffmpeg.bat
        echo.
    )
)

echo.
echo Installation complete.
echo To run the app: call run.bat
