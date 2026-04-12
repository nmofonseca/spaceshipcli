# Stage 1: Build the standalone Python binary
FROM python:3.12-slim-bookworm AS builder

# Required for PyInstaller and some python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution and installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Enable byte-compilation for uv
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files and README (required by hatchling for metadata)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies without the project itself (for cache optimization)
RUN uv sync --frozen --no-install-project

# Copy the rest of the application source code
COPY src/ ./src/

# Sync again to install the project
RUN uv sync --frozen

# Build the standalone binary using PyInstaller
RUN uv run pyinstaller --onefile --name spaceshipcli --clean src/spaceship_cli/main.py

# Stage 2: Create the minimal runtime image
FROM debian:bookworm-slim

# Create a non-root user for security
RUN groupadd -r spaceshipcli && useradd -r -g spaceshipcli spaceshipcli

# Install ca-certificates to ensure httpx can make HTTPS requests to the Spaceship API
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the compiled binary from the builder stage
COPY --from=builder /app/dist/spaceshipcli /usr/local/bin/spaceshipcli

# Set proper permissions
RUN chmod +x /usr/local/bin/spaceshipcli && \
    chown spaceshipcli:spaceshipcli /usr/local/bin/spaceshipcli

# Switch to the non-root user
USER spaceshipcli

# Execute the binary as the entrypoint
ENTRYPOINT ["spaceshipcli"]
