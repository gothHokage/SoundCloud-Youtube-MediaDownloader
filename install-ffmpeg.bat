@echo off
chcp 65001 >nul
title Media Downloader — Install ffmpeg
echo ========================================
echo  Installing ffmpeg for Media Downloader
echo ========================================
echo.

set "FFMPEG_URL=https://github.com/ffbinaries/ffbinaries-prebuilt/releases/download/v6.1/ffmpeg-6.1-win-64.zip"
set "ZIP_FILE=%TEMP%\ffmpeg.zip"
set "APP_DIR=%~dp0app"

echo Downloading ffmpeg (~10MB)...
powershell -Command "& {try{Invoke-WebRequest -Uri '%FFMPEG_URL%' -OutFile '%ZIP_FILE%' -UseBasicParsing; Write-Host 'OK'}catch{Write-Host 'FAILED: '+$_.Exception.Message; exit 1}}"

if not exist "%ZIP_FILE%" (
    echo Download failed. Trying alternative source...
    set "FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    powershell -Command "& {try{Invoke-WebRequest -Uri '%FFMPEG_URL%' -OutFile '%ZIP_FILE%' -UseBasicParsing; Write-Host 'OK'}catch{Write-Host 'FAILED: '+$_.Exception.Message; exit 1}}"
    if not exist "%ZIP_FILE%" (
        echo.
        echo Failed to download ffmpeg. Install manually:
        echo  1. Download ffmpeg.exe from: https://www.gyan.dev/ffmpeg/builds/
        echo  2. Place ffmpeg.exe in: %APP_DIR%
        echo.
        pause
        exit /b 1
    )
)

echo Extracting ffmpeg.exe...
powershell -Command "& {try{$zip=[System.IO.Compression.ZipFile]::OpenRead('%ZIP_FILE%');$entry=$zip.Entries|Where-Object{$_.Name -eq 'ffmpeg.exe'}|Select-Object -First 1;if($entry -eq $null){$entry=$zip.Entries|Where-Object{$_.FullName -like '*/bin/ffmpeg.exe'}|Select-Object -First 1}[System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry,'%APP_DIR%\ffmpeg.exe',$true);$zip.Dispose();Write-Host 'OK'}catch{Write-Host 'FAILED: '+$_.Exception.Message; exit 1}}"

if exist "%APP_DIR%\ffmpeg.exe" (
    echo ffmpeg installed to: %APP_DIR%\ffmpeg.exe
) else (
    echo Failed to extract ffmpeg.exe
    pause
    exit /b 1
)

del "%ZIP_FILE%" 2>nul

echo.
echo ffmpeg installed. Ready for maximum quality downloads.
echo.
pause
