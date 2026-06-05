# ── Coder Buddy — Dockerfile ──────────────────────────────────────────────────
FROM python:3.11-slim

# Metadata
LABEL maintainer="Coder Buddy"
LABEL description="Autonomous AI Software Engineer — LangGraph + Groq"

# Install git (required by GitPython) and build essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Set working directory
WORKDIR /app

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY sample_repo/ ./sample_repo/

# Switch to non-root user
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Start the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
