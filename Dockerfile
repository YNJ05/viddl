FROM python:3.12-slim

# Install system dependencies (ffmpeg for merging/converting, curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /viddl

# Install Python dependencies — always upgrade yt-dlp to latest
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir --upgrade yt-dlp

# Copy application source
COPY app/ ./app/

# Create downloads directory
RUN mkdir -p /downloads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]