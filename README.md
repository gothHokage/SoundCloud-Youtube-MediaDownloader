# Emo Media Downloader — YouTube & SoundCloud
> Built with Opencode CLI

<p align="center">
  <img src="static/logo.png" alt="MEDIA DOWNLOADER" width="400">
</p>

Downloads audio and video from YouTube and SoundCloud. Runs locally in your browser.

<p align="center">
  <img src="screenshots/searchfull.jpg" alt="Main screen" width="720">
</p>

## Features

- Search YouTube & SoundCloud from the browser (up to 50 results, pagination)
- Audio: downloads as MP3 320kbps (requires ffmpeg) or native format (opus/m4a without ffmpeg)
- Video: downloads as MP4 up to 4K (requires ffmpeg) or single stream (without ffmpeg)
- SoundCloud: search + audio only (no video)
- Paste a link — auto-detects YouTube video/playlist, SoundCloud track/playlist
- Logs tab shows real-time download progress
- Recent tab lists downloaded files
- ffmpeg auto-detected, auto-downloaded on install

## Quick start (Windows)

```cmd
install.bat
run.bat
```

`install.bat` sets up venv, installs deps (FastAPI, yt-dlp), and downloads ffmpeg (~10MB) into `app/ffmpeg.exe`.

`run.bat` starts the server at **http://127.0.0.1:8080**

### ffmpeg

If `install.bat` couldn't download ffmpeg:
- Run `install-ffmpeg.bat`
- Or put `ffmpeg.exe` manually into `app/ffmpeg.exe`
- Or add it to system PATH

Without ffmpeg, audio stays in native format (m4a/opus) and video is limited to single-stream quality (~720p).

## Usage

**Search tab** (bottom nav) — enter a query, choose YouTube or SoundCloud, press Enter. Click Audio or Video on any result. Use arrows to flip pages.

**Download by link** — paste a YouTube or SoundCloud URL in the top field, select Audio or Video mode, click Download. Progress shows in Logs tab. Finished files appear in Recent tab.

**Audio mode** — output is MP3 320kbps (with ffmpeg) or best available audio stream (without ffmpeg).

**Video mode** — choose MP4 (full video) or MP3 (extract audio from video). With ffmpeg you get best video+audio merged, up to 4K.

## Config

`.env` in project root:

```env
HOST=127.0.0.1
PORT=8080
DOWNLOAD_DIR=downloads
```

## Project structure

```
MediaDownloader/
  app/main.py          # FastAPI server
  static/              # Frontend (HTML, CSS, JS, images)
  design/              # Source design assets
  downloads/           # Downloaded files (created on first use)
  venv/                # Virtual environment
  .env                 # Config
  install.bat          # Setup script
  run.bat              # Start script
  requirements.txt     # Python deps
```

All downloads go to `downloads/<job_id>/` with the file and a `download.log`.

## Updating yt-dlp

```cmd
.\venv\Scripts\python.exe -m pip install -U yt-dlp
```

## Requirements

- Python 3.11 or 3.12
- ffmpeg (optional, auto-downloaded by install.bat)

## Screenshots

| # | What | File |
|---|------|------|
| 1 | Full UI — logo, search, controls | `screenshots/searchfull.jpg` |
| 2 | Logs / Download progress | `screenshots/logs.png` |
| 3 | ffmpeg badge | `screenshots/ffmpeg.png` |

## License

MIT
