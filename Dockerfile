# Atlas-G Protocol - Production Dockerfile
# Multi-stage build for Cloud Run deployment

# ============================================================================
# Stage 1: Frontend Builder
# ============================================================================
FROM node:20-slim as frontend-builder

WORKDIR /app/frontend

# Copy frontend dependency files
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build

# ============================================================================
# Stage 2: Python Backend Builder
# ============================================================================
FROM python:3.11-slim as backend-builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy configuration and source for build
COPY pyproject.toml README.md ./
COPY backend/ ./backend/

# Install the package
RUN pip install --no-cache-dir .

# ============================================================================
# Stage 3: Production Runtime
# ============================================================================
FROM python:3.11-slim as production

WORKDIR /app

# Create non-root user for security
RUN groupadd -r atlas && useradd -r -g atlas atlas

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy application code and data
COPY backend/ ./backend/
COPY data/ ./data/
COPY mcp_config.json ./

# Copy frontend build from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Set ownership
RUN chown -R atlas:atlas /app

# Switch to non-root user
USER atlas

# Environment
ENV PORT=8080
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose Cloud Run port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "backend.main:application", "--host", "0.0.0.0", "--port", "8080"]
