"""
Vercel serverless entry point.

Vercel looks for a WSGI/ASGI app named `app` in this file.
We simply re-export the FastAPI app from the main module after
configuring the environment for serverless (ephemeral /tmp storage).
"""

import os

# On Vercel, the only writable directory is /tmp.
# Set before importing app.main so the downloads dir is created there.
os.environ.setdefault("DOWNLOADS_DIR", "/tmp/downloads")

from app.main import app  # noqa: E402, F401
