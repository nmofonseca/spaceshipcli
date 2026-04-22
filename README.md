# 🚀 Spaceship.com CLI Tool 🛸

[![Tests](https://github.com/nmofonseca/spaceshipcli/actions/workflows/test_and_build.yml/badge.svg)](https://github.com/nmofonseca/spaceshipcli/actions/workflows/test_and_build.yml)
[![GitHub Super-Linter](https://github.com/nmofonseca/spaceshipcli/actions/workflows/linting.yml/badge.svg)](https://github.com/marketplace/actions/super-linter)

> **A powerful, human-friendly command-line interface for managing your Spaceship.com resources (Domains, DNS, Contacts) directly from your terminal.** 💻✨

---

## ✨ Features

- 🌐 **Domain Management**: List, check availability, and retrieve detailed domain info.
- 🔐 **DNS Control**: Full management of resource records.
- 👤 **Contact Details**: Quickly access and manage your contact information.
- 📄 **Flexible Output**: Human-readable rich tables by default, or raw JSON for automation.
- 🏗️ **Portable**: Run via Python, as a standalone binary, or inside a Docker container.

---

## 🛠️ Development Environment

### Using Devbox (Recommended) 📦

This project uses [Devbox](https://www.jetify.com/devbox) to manage its development environment. It ensures that everyone has the same versions of `uv` and other tools installed.

```bash
# Start the development shell
devbox shell
```

---

## 📦 Installation

This project is managed with `uv`.

```bash
# Sync dependencies
uv sync
```

---

## ⚙️ Configuration

The CLI requires your Spaceship API credentials. You can provide them in two ways:

### 1. 🔑 Environment Variables
Set them directly in your shell:
```bash
export SPACESHIP_API_KEY=your_api_key
export SPACESHIP_API_SECRET=your_api_secret
```

### 2. 📝 .env File
Create a `.env` file in the root directory:
```ini
SPACESHIP_API_KEY=your_api_key
SPACESHIP_API_SECRET=your_api_secret
```

---

## 🚀 Usage

Run the CLI using `uv run spaceship`.

### 🔍 Quick Commands

| Task | Command |
| :--- | :--- |
| **Check Version** | `uv run spaceship --version` |
| **Get Help** | `uv run spaceship --help` |
| **List Domains** | `uv run spaceship domains list` |
| **Check Domain** | `uv run spaceship domains check example.com` |
| **List DNS** | `uv run spaceship dns list --domain example.com` |

### 📄 Output Formatting

By default, all commands output data as formatted, human-readable terminal tables.
You can output raw JSON instead by passing the `--format json` option:

```bash
uv run spaceship domains list --format json
```

---

## 🏗️ Building & Deployment

### 🔨 Standalone Binary
To build a standalone executable (no Python/uv required):

```bash
uv run pyinstaller --onefile --name "spaceshipcli-v$(uv run spaceship --version | cut -d ' ' -f 2)-linux-amd64" --clean src/spaceship_cli/main.py
```

### 🐳 Running via Docker
Build the Docker image:

```bash
docker build -t spaceshipcli --build-arg VERSION=$(uv run spaceship --version | cut -d ' ' -f 2) .
```

Run the container:

```bash
docker run --rm -e SPACESHIP_API_KEY=your_api_key -e SPACESHIP_API_SECRET=your_api_secret spaceshipcli domains list
```

---

## 🧪 Development

### 🧹 Linting
We use `super-linter` to maintain high standards. Run it locally:

```bash
# Run the full linting suite via Docker
docker run --rm \
  -e RUN_LOCAL=true \
  -e VALIDATE_PYTHON_BLACK=true \
  -e VALIDATE_PYTHON_RUFF=true \
  -e VALIDATE_PYTHON_PYLINT=true \
  -e VALIDATE_PYTHON_MYPY=true \
  -e VALIDATE_DOCKERFILE_HADOLINT=true \
  -e VALIDATE_MARKDOWN=true \
  -e VALIDATE_YAML=true \
  -e VALIDATE_JSON=true \
  -e DEFAULT_BRANCH="develop" \
  -v "$PWD":/tmp/lint \
  ghcr.io/super-linter/super-linter:slim-v8.6.0
```

### 🚥 Running Tests
```bash
uv run pytest
```

---

### 📦 Command Reference Details

#### Domains
- **List domains**: `uv run spaceship domains list`
- **Info**: `uv run spaceship domains info example.com`
- **Availability**: `uv run spaceship domains check example.com`
- **Nameservers**: `uv run spaceship domains nameservers example.com`
- **Transfer details**: `uv run spaceship domains transfer example.com`
- **Auth code**: `uv run spaceship domains auth-code example.com`

#### DNS
- **List records**: `uv run spaceship dns list --domain example.com`

#### Contacts
- **Contact info**: `uv run spaceship contacts info [CONTACT_ID]`
