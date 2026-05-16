from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import subprocess
import uuid
import json
import shutil
import sys
import logging
import zipfile
import io
import requests
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

HOST = os.getenv('HOST') or '127.0.0.1'
try:
    PORT = int(os.getenv('PORT') or 8080)
except Exception:
    PORT = 8080
DOWNLOAD_DIR = Path(os.getenv('DOWNLOAD_DIR', 'downloads'))

app = FastAPI(title="Local Media Downloader")

# Serve static UI
app.mount('/static', StaticFiles(directory='static'), name='static')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def check_ffmpeg():
    """Quick check for ffmpeg on PATH or next to app."""
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception:
        pass
    local_ffmpeg = Path(__file__).parent / 'ffmpeg.exe'
    if local_ffmpeg.exists():
        try:
            subprocess.run([str(local_ffmpeg), '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            os.environ['PATH'] = str(local_ffmpeg.parent) + os.pathsep + os.environ.get('PATH', '')
            return True
        except Exception:
            local_ffmpeg.unlink(missing_ok=True)
    return False


FFMPEG_DL_LOCK = False

def ensure_ffmpeg():
    """Returns True if ffmpeg available. Tries auto-download once."""
    if check_ffmpeg():
        return True
    global FFMPEG_DL_LOCK
    if FFMPEG_DL_LOCK:
        return False
    FFMPEG_DL_LOCK = True
    try:
        local_ffmpeg = Path(__file__).parent / 'ffmpeg.exe'
        logger.info('Downloading ffmpeg (~10MB)...')
        # Try ffbinaries (smaller build) first
        urls = [
            'https://github.com/ffbinaries/ffbinaries-prebuilt/releases/download/v6.1/ffmpeg-6.1-win-64.zip',
            'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip',
        ]
        for url in urls:
            try:
                resp = requests.get(url, stream=True, timeout=60)
                resp.raise_for_status()
                data = resp.content
                with zipfile.ZipFile(io.BytesIO(data)) as zf:
                    # Try ffbinaries format (flat), then gyan format (nested)
                    if 'ffmpeg.exe' in zf.namelist():
                        with zf.open('ffmpeg.exe') as src, open(str(local_ffmpeg), 'wb') as dst:
                            shutil.copyfileobj(src, dst)
                    else:
                        for name in zf.namelist():
                            if name.endswith('/bin/ffmpeg.exe'):
                                with zf.open(name) as src, open(str(local_ffmpeg), 'wb') as dst:
                                    shutil.copyfileobj(src, dst)
                                break
                if local_ffmpeg.exists():
                    os.environ['PATH'] = str(local_ffmpeg.parent) + os.pathsep + os.environ.get('PATH', '')
                    logger.info(f'ffmpeg downloaded to {local_ffmpeg}')
                    return True
            except Exception:
                continue
        logger.warning('All ffmpeg download sources failed')
    except Exception as e:
        logger.error(f'ffmpeg download error: {e}')
    finally:
        FFMPEG_DL_LOCK = False
    return False


def ensure_download_dir():
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get('/', response_class=HTMLResponse)
async def index():
    html = Path('static/index.html').read_text(encoding='utf-8')
    return HTMLResponse(content=html)


@app.get('/api/ffmpeg')
async def ffmpeg_status():
    return {'available': check_ffmpeg()}


@app.post('/api/download')
async def download_endpoint(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    url = data.get('url')
    mode = data.get('mode', 'audio')
    audio_format = data.get('audio_format', 'mp3')
    video_format = data.get('video_format', 'mp4')
    if not url:
        raise HTTPException(status_code=400, detail='Missing url')
    job_id = str(uuid.uuid4())
    ensure_download_dir()
    background_tasks.add_task(download_job, job_id, url, mode, audio_format, video_format)
    return {'job_id': job_id}


def download_job(job_id: str, url: str, mode: str, audio_format: str = 'mp3', video_format: str = 'mp4'):
    job_dir = DOWNLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    log_path = job_dir / 'download.log'

    ffmpeg_ok = ensure_ffmpeg()
    log = lambda msg: open(log_path, 'a', encoding='utf-8').write(msg + '\n')

    if ffmpeg_ok:
        log('ffmpeg ✓ — maximum quality enabled')
    else:
        log('ffmpeg not found — quality limited. Install: run install-ffmpeg.bat')

    base = [sys.executable, '-m', 'yt_dlp', url, '--no-warnings', '--no-progress', '--print-json']

    if mode == 'audio':
        # Audio: best quality, convert to mp3 if ffmpeg available
        chosen = (audio_format or 'mp3').lower()
        outtmpl = str(job_dir / '%(title)s.%(ext)s')
        if ffmpeg_ok:
            opts = base + ['-f', 'bestaudio', '--extract-audio', '--audio-format', chosen, '--add-metadata', '-o', outtmpl, '--no-keep-video']
            if chosen == 'mp3':
                opts += ['--audio-quality', '0', '--postprocessor-args', 'ffmpeg:-codec:a libmp3lame -b:a 320k']
        else:
            opts = base + ['-f', 'bestaudio', '-o', outtmpl]
    else:
        # Video: best quality, prefer h264 for MP4 compatibility
        chosen = (video_format or 'mp4').lower()
        outtmpl = str(job_dir / '%(title)s.%(ext)s')

        if chosen == 'mp3':
            # Extract audio from video at max quality
            if ffmpeg_ok:
                opts = base + ['-f', 'bestaudio', '--extract-audio', '--audio-format', 'mp3', '--add-metadata', '-o', outtmpl, '--no-keep-video']
                opts += ['--audio-quality', '0', '--postprocessor-args', 'ffmpeg:-codec:a libmp3lame -b:a 320k']
            else:
                opts = base + ['-f', 'bestaudio', '-o', outtmpl]
        else:
            # Max quality video: bestvideo (prefer h264 for mp4) + bestaudio
            if ffmpeg_ok:
                opts = base + ['-f', 'bestvideo[vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo+bestaudio/best', '--merge-output-format', chosen, '-o', outtmpl]
            else:
                opts = base + ['-f', 'best', '-o', outtmpl]

    log('Running: ' + ' '.join(opts))
    try:
        proc = subprocess.Popen(opts, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    except FileNotFoundError as e:
        log('FileNotFoundError: ' + repr(e))
        return
    except Exception as e:
        log('Exception on start: ' + repr(e))
        return
    try:
        for line in proc.stdout:
            log(line.rstrip())
        proc.wait()
        log(f'Exit code: {proc.returncode}')
    except Exception as e:
        log('Exception during run: ' + repr(e))
    finally:
        # List downloaded files
        for f in job_dir.iterdir():
            if f.is_file() and f.name != 'download.log':
                log(f'Output: {f.name}')


@app.get('/api/log/{job_id}')
async def get_log(job_id: str):
    path = DOWNLOAD_DIR / job_id / 'download.log'
    if not path.exists():
        raise HTTPException(status_code=404, detail='Log not found')
    return StreamingResponse(path.open('r', encoding='utf-8'), media_type='text/plain')


@app.get('/api/list')
async def list_downloads():
    ensure_download_dir()
    items = []
    for d in DOWNLOAD_DIR.iterdir():
        if d.is_dir():
            items.append({
                'id': d.name,
                'files': [f.name for f in d.iterdir() if f.is_file() and f.name != 'download.log']
            })
    return {'items': items}


@app.get('/api/file/{job_id}/{filename}')
async def get_file(job_id: str, filename: str):
    path = DOWNLOAD_DIR / job_id / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail='File not found')
    return FileResponse(path)


@app.post('/api/search')
async def search(request: Request):
    try:
        data = await request.json()
        engine = data.get('engine', 'youtube')
        query = data.get('query', '')
        limit = int(data.get('limit', 5))
        if not query:
            raise HTTPException(status_code=400, detail='Missing query')
        if engine == 'youtube':
            prefix = f'ytsearch{limit}:'
        elif engine == 'soundcloud':
            prefix = f'scsearch{limit}:'
        else:
            raise HTTPException(status_code=400, detail='Unsupported engine')

        cmd = [sys.executable, '-m', 'yt_dlp', prefix + query, '--print-json', '--no-warnings', '--no-progress', '--flat-playlist', '--ignore-errors']
        logger.info(f'Search cmd: {cmd}')
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            out, err = proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            raise HTTPException(status_code=500, detail='Search timed out')

        if err:
            logger.warning(f'Search stderr: {err[:500]}')

        results = []
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                # Skip non-video entries (channels, playlists)
                ie_key = obj.get('ie_key', '')
                if ie_key not in ('Youtube', 'Soundcloud', 'YoutubeSearch', 'SoundcloudSearch'):
                    # Also keep entries without ie_key that have a watch URL
                    video_url = obj.get('webpage_url') or obj.get('url', '')
                    if '/watch?v=' not in video_url and '/shorts/' not in video_url and 'soundcloud.com' not in video_url:
                        continue
                # Extract thumbnail from thumbnails array if available
                thumbnail = obj.get('thumbnail')
                if not thumbnail and obj.get('thumbnails'):
                    thumbs = obj.get('thumbnails')
                    if isinstance(thumbs, list) and len(thumbs) > 0:
                        first = thumbs[0]
                        thumbnail = first.get('url') if isinstance(first, dict) else None
                item = {
                    'id': obj.get('id'),
                    'title': obj.get('title'),
                    'url': obj.get('webpage_url') or obj.get('url'),
                    'uploader': obj.get('uploader') or obj.get('channel'),
                    'duration': obj.get('duration'),
                    'thumbnail': thumbnail,
                    'description': obj.get('description'),
                }
                results.append(item)
            except Exception as e:
                logger.warning(f'Search parse error: {e}')
                continue

        logger.info(f'Search returned {len(results)} results')
        return {'results': results}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Search error: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=f'Search failed: {str(e)}')
