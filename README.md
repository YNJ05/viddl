# VidDL 🎬

A powerful, modern video downloader with a sleek web UI.

Built with **FastAPI** + **yt-dlp** — deployable on **Vercel**, **Docker**, or **locally**.

---

### 🐳 Docker

```bash
git clone https://github.com/<your-username>/viddl.git
cd viddl
docker compose up --build
# → http://localhost:8000
```

### 💻 Local (without Docker)

> Requires Python 3.12+ and [ffmpeg](https://ffmpeg.org/) (optional, for merging streams).

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000
```

Downloads are saved to `./downloads/`.

---

## Features

- 🌐 **1000+ supported sites** — YouTube, Twitter/X, Instagram, TikTok, Vimeo, Reddit, Twitch, and more
- 🎥 **Quality selection** — Best, 1080p, 720p, 480p, 360p
- 🎵 **Audio-only mode** — Extract MP3 directly
- 📊 **Real-time progress** — Speed, ETA, live progress bar
- 📁 **Library tab** — Browse, download, and delete your files
- 🐳 **Multi-platform** — Vercel, Docker, or local
- ⚡ **ffmpeg included** (Docker) — Automatic merging of video+audio streams
- 🚀 **CI/CD ready** — GitHub Actions → Vercel deployment

---

## Usage

1. Paste a video URL into the input box
2. Click **Fetch Info** to preview the video
3. Choose quality and format
4. Click **Download Now**
5. Monitor progress in real-time
6. Switch to **Library** to access your files
