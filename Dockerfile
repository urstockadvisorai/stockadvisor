# Multi-stage Docker build for StockPlayer
# -------------------------------------------------
# 1️⃣ Build the frontend (Vite + React)
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
# -------------------------------------------------
# 2️⃣ Build the backend (FastAPI)
FROM python:3.11-slim AS backend-builder
WORKDIR /app/backend
# Install OS build deps (only if needed for wheels)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
# -------------------------------------------------
# 3️⃣ Runtime image (tiny)
# 3️⃣ Runtime image (tiny)
FROM python:3.11-slim

# OS runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*

# Create non‑root user
RUN useradd -m appuser
WORKDIR /home/appuser

# Install python dependencies globally in the final stage
# (We copy requirements from builder to keep cache, but install here to ensure they are in the path)
COPY --from=backend-builder /app/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

USER appuser

# Copy built assets
COPY --from=frontend-builder /app/frontend/dist ./frontend
COPY --from=backend-builder /app/backend .

# Expose FastAPI port
EXPOSE 8000
# Entry point
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
