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

Run the CLI using `spaceship`.

### 🔍 Quick Commands

| Task | Command |
| :--- | :--- |
| **Check Version** | `spaceship --version` |
| **Get Help** | `spaceship --help` |
| **List Domains** | `spaceship domains list` |
| **Check Domain** | `spaceship domains check example.com` |
| **List DNS** | `spaceship dns list --domain example.com` |

### 📄 Output Formatting

By default, all commands output data as formatted, human-readable terminal tables.
You can output raw JSON instead by passing the `--format json` option:

```bash
spaceship domains list --format json
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
- **List domains**: 
  - `spaceship domains list`
  - *Example with options*: `spaceship domains list --limit 20 --offset 10 --order-by expirationDate --format json`
- **Info**: 
  - `spaceship domains info example.com`
- **Availability**: 
  - `spaceship domains check example.com`
  - *Example for multiple domains*: `spaceship domains check example.com example.org example.net`
- **Nameservers**: 
  - `spaceship domains nameservers example.com`
- **Transfer details**: 
  - `spaceship domains transfer example.com`
- **Auth code**: 
  - `spaceship domains auth-code example.com`

#### DNS
- **List records**: 
  - `spaceship dns list --domain example.com`
  - *Example with options*: `spaceship dns list --domain example.com --limit 50 --order-by name`
- **Add DNS records**: Adds or updates records without deleting existing ones by automatically fetching the current records, merging them (skipping exact duplicates), and updating the DNS zone.
  - **Single Record**:
    ```bash
    spaceship dns add --domain example.com --type A --name www --value 1.2.3.4 --ttl 3600
    ```
  - **Bulk Upload via JSON File**:
    ```bash
    spaceship dns add --domain example.com --file records.json
    ```
    *Example `records.json`*:
    ```json
    [
      {
        "type": "TXT",
        "name": "@",
        "value": "v=spf1 include:_spf.example.com ~all",
        "ttl": 3600
      },
      {
        "type": "A",
        "name": "api",
        "address": "1.2.3.4",
        "ttl": 3600
      }
    ]
    ```
- **Delete DNS records**: Deletes specific records by automatically fetching the current records, filtering out the ones to delete, and updating the DNS zone.
  - **Single Record**:
    ```bash
    spaceship dns delete --domain example.com --type A --name www --value 1.2.3.4
    ```
  - **Bulk Delete via JSON File**:
    ```bash
    spaceship dns delete --domain example.com --file delete_records.json
    ```
- **Update DNS record**: Updates an existing DNS record's value or TTL in-place.
  - **Update Value**:
    ```bash
    spaceship dns update --domain example.com --type A --name www --new-value 2.2.2.2
    ```
  - **Update TTL**:
    ```bash
    spaceship dns update --domain example.com --type A --name www --new-ttl 600
    ```
  - **Specify Current Value (for resolving ambiguity)**:
    ```bash
    spaceship dns update --domain example.com --type A --name www --current-value 1.1.1.1 --new-value 2.2.2.2
    ```
    > [!IMPORTANT]
    > If a domain has multiple records with the same type and host name (e.g. multiple `A` records), you **must** specify the `--current-value` option. This ensures the CLI updates the exact record intended and prevents ambiguity. If omitted in this scenario, the CLI will exit with an error.

#### Contacts
- **Contact info**: 
  - `spaceship contacts info 12345678-1234-1234-1234-123456789012`
