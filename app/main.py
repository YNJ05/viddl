import asyncio
import json
import os
import re
import shutil
import uuid
from pathlib import Path

import yt_dlp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ── Paths ────────────────────────────────────────────────────────
# Resolve paths relative to project root so it works both locally
# (python -m uvicorn app.main:app) and inside Docker.
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "app" / "static"

DOWNLOADS_DIR = Path(os.environ.get("DOWNLOADS_DIR", str(BASE_DIR / "downloads")))
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

COOKIES_FILE = Path(
    os.environ.get("COOKIES_FILE", str(BASE_DIR / "cookies" / "cookies.txt"))
)

# ── App ──────────────────────────────────────────────────────────
app = FastAPI(title="VidDL", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Detect ffmpeg — needed for merging separate video+audio streams
HAS_FFMPEG = shutil.which("ffmpeg") is not None

# In-memory job tracker
jobs: dict[str, dict] = {}

# Shared yt-dlp base options — fixes YouTube 403 by using the Android
# player client, which doesn't require PO tokens or browser cookies.
def base_ydl_opts() -> dict:
    opts: dict = {
        "quiet": True,
        "no_warnings": True,
        # Use Android + web clients: avoids the bot-detection 403
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
                "player_skip": ["webpage", "configs"],
            }
        },
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 11; Pixel 5) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Mobile Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        # Retry on transient errors
        "retries": 5,
        "fragment_retries": 5,
        "file_access_retries": 3,
        "sleep_interval_requests": 1,
    }
    # If a cookies.txt is mounted at /cookies/cookies.txt, use it.
    # This unlocks age-restricted / member-only / private videos.
    if COOKIES_FILE.exists():
        opts["cookiefile"] = str(COOKIES_FILE)
    return opts


class DownloadRequest(BaseModel):
    url: str
    format: str = "best"
    audio_only: bool = False
    quality: str = "best"


class InfoRequest(BaseModel):
    url: str


def sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', name)


@app.get("/")
async def root():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.post("/api/info")
async def get_video_info(req: InfoRequest):
    ydl_opts = {**base_ydl_opts(), "extract_flat": False}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(req.url, download=False)
            formats = []
            seen = set()
            for f in (info.get("formats") or []):
                fid = f.get("format_id", "")
                ext = f.get("ext", "")
                height = f.get("height")
                acodec = f.get("acodec", "none")
                vcodec = f.get("vcodec", "none")

                if vcodec != "none" and height:
                    key = f"{height}p"
                    if key not in seen:
                        seen.add(key)
                        formats.append({
                            "id": fid,
                            "label": f"{height}p ({ext})",
                            "height": height,
                            "ext": ext,
                            "type": "video",
                        })
                elif vcodec == "none" and acodec != "none":
                    abr = f.get("abr", 0)
                    key = f"audio_{abr}"
                    if key not in seen:
                        seen.add(key)
                        formats.append({
                            "id": fid,
                            "label": f"Audio {int(abr or 0)}kbps ({ext})",
                            "abr": abr,
                            "ext": ext,
                            "type": "audio",
                        })

            formats.sort(key=lambda x: (x.get("height", 0) or x.get("abr", 0)), reverse=True)

            return {
                "title": info.get("title", "Unknown"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "uploader": info.get("uploader"),
                "view_count": info.get("view_count"),
                "formats": formats[:12],
                "platform": info.get("extractor_key", "Unknown"),
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/download")
async def start_download(req: DownloadRequest):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "speed": "",
        "eta": "",
        "filename": "",
        "error": None,
        "url": req.url,
    }
    asyncio.create_task(run_download(job_id, req))
    return {"job_id": job_id}


async def run_download(job_id: str, req: DownloadRequest):
    jobs[job_id]["status"] = "downloading"

    def progress_hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            pct = (downloaded / total * 100) if total else 0
            jobs[job_id].update({
                "progress": round(pct, 1),
                "speed": d.get("_speed_str", "").strip(),
                "eta": d.get("_eta_str", "").strip(),
                "status": "downloading",
            })
        elif d["status"] == "finished":
            jobs[job_id]["status"] = "processing"
            jobs[job_id]["progress"] = 99

    if req.audio_only:
        fmt = "bestaudio/best"
        if HAS_FFMPEG:
            postprocessors = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        else:
            postprocessors = []
    else:
        if HAS_FFMPEG:
            if req.quality and req.quality != "best":
                fmt = f"bestvideo[height<={req.quality}]+bestaudio/best[height<={req.quality}]/best"
            else:
                fmt = "bestvideo+bestaudio/best"
            postprocessors = [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}]
        else:
            # No ffmpeg: use pre-merged single-stream formats
            if req.quality and req.quality != "best":
                fmt = f"best[height<={req.quality}]/best"
            else:
                fmt = "best"
            postprocessors = []

    ydl_opts = {
        **base_ydl_opts(),
        "format": fmt,
        "outtmpl": str(DOWNLOADS_DIR / "%(title)s.%(ext)s"),
        "progress_hooks": [progress_hook],
        "postprocessors": postprocessors,
    }
    if HAS_FFMPEG:
        ydl_opts["merge_output_format"] = "mp4"

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _do_download, ydl_opts, req.url, job_id)
        jobs[job_id]["status"] = "done"
        jobs[job_id]["progress"] = 100
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


def _do_download(ydl_opts, url, job_id):
    class TitleCapture:
        def __init__(self):
            self.filename = None

        def __call__(self, d):
            if d.get("filename") and not self.filename:
                self.filename = d["filename"]

    capture = TitleCapture()
    original_hooks = ydl_opts.get("progress_hooks", [])
    ydl_opts["progress_hooks"] = original_hooks + [capture]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    if capture.filename:
        jobs[job_id]["filename"] = Path(capture.filename).name


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@app.get("/api/stream/{job_id}")
async def stream_status(job_id: str):
    async def event_generator():
        while True:
            if job_id not in jobs:
                yield f"data: {json.dumps({'error': 'not found'})}\n\n"
                break
            job = jobs[job_id]
            yield f"data: {json.dumps(job)}\n\n"
            if job["status"] in ("done", "error"):
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/files")
async def list_files():
    files = []
    for f in DOWNLOADS_DIR.iterdir():
        if f.is_file() and not f.name.startswith("."):
            stat = f.stat()
            files.append({
                "name": f.name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
            })
    files.sort(key=lambda x: x["modified"], reverse=True)
    return files


@app.get("/api/files/{filename}")
async def download_file(filename: str):
    path = DOWNLOADS_DIR / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, filename=filename)


@app.delete("/api/files/{filename}")
async def delete_file(filename: str):
    path = DOWNLOADS_DIR / filename
    if path.exists():
        path.unlink()
    return {"deleted": filename}


app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")