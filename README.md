# VidDL 🎬

A powerful, modern video downloader with a sleek web UI.

Built with **FastAPI** + **yt-dlp** — deployable on **Vercel**, **Docker**, or **locally**.

---

## Quick Start

### 🚀 Deploy to Vercel (one click)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/<your-username>/viddl)

Or manually:
```bash
npm i -g vercel
vercel
```

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

---

## Project Structure

```
viddl/
├── .github/workflows/
│   └── deploy.yml           # CI/CD: lint → deploy to Vercel
├── api/
│   └── index.py             # Vercel serverless entry point
├── app/
│   ├── main.py              # FastAPI backend
│   └── static/
│       └── index.html       # Web UI
├── downloads/               # Local downloads (gitignored)
├── cookies/                 # Optional cookies.txt (gitignored)
├── vercel.json              # Vercel configuration
├── Dockerfile               # Docker build
├── docker-compose.yml       # Docker Compose setup
├── requirements.txt
└── README.md
```

---

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/deploy.yml`) runs on every push to `main`:

1. **Lint** — Validates code with [Ruff](https://github.com/astral-sh/ruff)
2. **Deploy** — Pushes to Vercel production

### Setup Vercel secrets in GitHub

1. Go to [Vercel Tokens](https://vercel.com/account/tokens) → create a token
2. Run `vercel link` locally to get your Org ID and Project ID
3. Add these secrets to your GitHub repo (`Settings → Secrets → Actions`):

| Secret | Description |
|--------|-------------|
| `VERCEL_TOKEN` | Your Vercel API token |
| `VERCEL_ORG_ID` | Your Vercel Org/Team ID |
| `VERCEL_PROJECT_ID` | Your Vercel Project ID |

---

## ⚠️ Vercel Limitations

Vercel runs **serverless functions** with these constraints:

| Limit | Free | Pro |
|-------|------|-----|
| Max execution time | 10s | 60s |
| Storage | `/tmp` only (ephemeral) | `/tmp` only |
| ffmpeg | ❌ Not available | ❌ Not available |

- **Video info/fetch** works great on Vercel ✅
- **Short downloads** (~10s) may work on free tier
- **Long downloads** will timeout — use Docker or local for heavy use
- **Library tab** won't persist files (serverless = ephemeral `/tmp`)

For full functionality, use **Docker** or run **locally**.

---

## Stop / Restart (Docker)

```bash
docker compose down          # Stop
docker compose up -d         # Restart
docker compose logs -f       # View logs
```

## Update yt-dlp

```bash
# Docker
docker compose exec viddl yt-dlp -U

# Local
pip install --upgrade yt-dlp
```
