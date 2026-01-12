# Spaceship.com CLI Tool

This is a command-line interface for managing Spaceship.com resources (Domains, DNS, Contacts) using the public API.

## Development Environment

### Using Devbox (Recommended)

This project uses [Devbox](https://www.jetify.com/devbox) to manage its development environment. It ensures that everyone has the same versions of `uv` and other tools installed.

The configuration is defined in `devbox.json`. To start the development shell:

```bash
devbox shell
```

Once inside the shell, you can proceed with the standard installation.

## Installation

This project is managed with `uv`.

```bash
uv sync
```

## Configuration

The CLI requires your Spaceship API credentials. You can provide them in two ways:

### 1. Environment Variables
Set them directly in your shell:
```bash
export SPACESHIP_API_KEY=your_api_key
export SPACESHIP_API_SECRET=your_api_secret
```

### 2. .env File
Create a `.env` file in the root directory:
```ini
SPACESHIP_API_KEY=your_api_key
SPACESHIP_API_SECRET=your_api_secret
```

## Usage

Run the CLI using `uv run spaceship`.

### Building Standalone Binary

To build a standalone executable that doesn't require Python or `uv` to be installed on the target machine:

```bash
uv run pyinstaller --onefile --name spaceship --clean src/spaceship_cli/main.py
```

The binary will be created in the `dist/` directory.

### Domains

List domains:
```bash
uv run spaceship domains list
```

Get domain info:
```bash
uv run spaceship domains info example.com
```

Check domain availability:
```bash
uv run spaceship domains check example.com another-domain.net
```

### DNS

List DNS records for a domain:
```bash
uv run spaceship dns list --domain example.com
```

**Options:**
- `-d, --domain TEXT`: The domain name to list records for. [required]
- `-l, --limit INTEGER`: Number of records to return (default: 100).
- `-o, --offset INTEGER`: Number of records to skip (default: 0).
- `--order-by TEXT`: Sort order. Supported values: `type`, `-type`, `name`, `-name`.

**Example with sorting and pagination:**
```bash
uv run spaceship dns list -d example.com --limit 20 --order-by -name
```

### Contacts

List contacts:
```bash
uv run spaceship contacts list
```

## Development

Run tests:
```bash
uv run pytest
```