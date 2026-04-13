# Project: Spaceship.com DNS and Domain management tool

## General Instructions

- Documentation for spaceship.com public API should be read from here: <https://docs.spaceship.dev/>
- The online public API documentation should be the source in how to interact with the api's for different action, e.g. list domains, create DNS records, update DNS records, etc..
- Python Language should be used to create the tool or cli for interacting with the api
- Follow the existing condig style for all modifications
- Ensure all new code has comprehesive unit tests

## Python coding standards

- **PEP 8 Compliance**: Adhere to PEP 8 style guidelines for code formatting.
- **Type Hinting**: Use type hints (PEP 484) for function arguments and return values to improve code clarity and enable static analysis.
- **Docstrings**: Include docstrings for all modules, classes, and functions following PEP 257 conventions (e.g., Google or NumPy style).
- **Error Handling**: Use specific exception handling (`try/except`) rather than catching broad `Exception` classes. Define custom exception classes for domain-specific errors.
- **Logging**: Use the standard `logging` library instead of `print` statements. Log errors with stack traces and use appropriate log levels (INFO, DEBUG, ERROR).
- **Modern String Formatting**: Prefer f-strings over `%` formatting or `.format()`.
- **Linting and Formatting**: Use tools like `black` for formatting and `pylint` or `ruff` for linting.
- **Virtual Environments**: Always use a virtual environment for dependency management, use uv for virtual environment management.
- **Compatibility**: Should target Python 3.10 and higher versions.
- **Imports**: Organize imports according to PEP 8 (standard library, third-party, local application).
- **Complexity**: Keep functions small and focused on a single task.

## Docker Best Practices

- **Multi-stage Builds**: The `Dockerfile` employs a two-stage build process to keep the final image size minimal.
  - **Stage 1 (Builder)**: Uses `python:3.12-slim-bookworm` to install dependencies via `uv`, sync the project, and compile the application into a standalone binary using PyInstaller.
  - **Stage 2 (Runtime)**: Uses a minimal `debian:bookworm-slim` base image.
- **Security**: The runtime container operates under a dedicated, non-root user (`spaceshipcli`) to adhere to the principle of least privilege.
- **Minimal Footprint**: Only the compiled PyInstaller binary and necessary `ca-certificates` (for secure API requests) are copied to the runtime stage.
- **Build Caching**: The `uv` dependency installation is separated from the source code copy (`uv sync --frozen --no-install-project` run beforehand) to leverage Docker layer caching efficiently.

## Description of Project

I would like to create a cli tool in Python to interact with the api of spaceship.com a domain registration and web services platform, they have an API that can be used to interact with their service, unfortunately there is no cli to interact with the API's

The API documentation is available here which you can read: <https://docs.spaceship.dev/>, this has documentation about the API.

## Requirements

The cli should do the following:

- Read API keys either from the .env file or from environment variables, SPACESHIP_API_KEY and SPACESHIP_API_SECRET, if not set provide return informing the user the fact SECRET and KEY are not ser, more information <https://docs.spaceship.dev/#section/Spaceship-API/Authentication>
- Include a help command that outputs information on how to use the cli
- Commands must support output formatting. The default format should be human-readable rich tables. A `--format json` flag must be available on all commands to output raw JSON responses.
- I want to be able to do the following actions using the cli:
  - Get/List operations to implement:
    - Get a list of domains
    - Get information for 1 domain or all domains
    - Check domains availability for registration
    - Get personal nameservers on a domain
    - Get personal nameservers configuration (This is not available yet, currently returns HTTP 501, so please ignore)
    - Get the details of the domain transfer
    - Get domain auth code
    - Get domain resource records list
- The cli should be an executable in the end, compiled binary
- Please create tests that allow to test cli functionality every code change.
