# Stage 1: Build the React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend with Static Files
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies (libgomp1 required for PyTorch & SentenceTransformers, curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    libfontconfig1 \
    libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch first to prevent multi-gigabyte CUDA wheel bloat and memory exhaustion
RUN pip install --no-cache-dir torch --extra-index-url https://download.pytorch.org/whl/cpu

# Install remaining Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Alembic config & backend application
COPY alembic.ini .
COPY backend/ ./backend/
COPY data/ ./data/
COPY .env.example .env

# Create required runtime directories for file uploads and vector store
RUN mkdir -p uploads chroma_data data

# Copy built frontend assets to be served by FastAPI
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose server port
EXPOSE 8000

ENV PORT=8000

CMD ["sh", "-c", "uvicorn app.main:app --app-dir ./backend --host 0.0.0.0 --port ${PORT:-8000}"]


