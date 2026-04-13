"""
Tests for DNS commands.
"""

import os
from urllib.parse import parse_qs
import respx
from httpx import Response
from typer.testing import CliRunner
from spaceship_cli.main import app

# Set dummy env vars for testing before importing the app
os.environ["SPACESHIP_API_KEY"] = "test_key"
os.environ["SPACESHIP_API_SECRET"] = "test_secret"

runner = CliRunner()


@respx.mock
def test_list_dns_records_success() -> None:
    """Test successful DNS record listing."""
    domain = "example.com"
    # Mock the API response
    route = respx.get(f"https://spaceship.dev/api/v1/dns/records/{domain}").mock(
        return_value=Response(
            200,
            json={
                "items": [
                    {"type": "A", "name": "@", "address": "1.2.3.4", "ttl": 3600},
                    {
                        "type": "CNAME",
                        "name": "www",
                        "value": "example.com",
                        "ttl": 3600,
                    },
                ]
            },
        )
    )

    result = runner.invoke(
        app, ["dns", "list", "--domain", domain, "--order-by", "name"]
    )

    assert result.exit_code == 0
    assert "example.com" in result.stdout
    assert "1.2.3.4" in result.stdout
    assert "CNAME" in result.stdout
    assert route.called
    # Check that query params were passed
    request = route.calls.last.request
    qs = parse_qs(request.url.query.decode())
    assert qs["take"] == ["100"]
    assert qs["skip"] == ["0"]
    assert qs["orderBy"] == ["name"]


@respx.mock
def test_list_dns_records_empty() -> None:
    """Test DNS record listing with no results."""
    domain = "nodata.com"
    respx.get(f"https://spaceship.dev/api/v1/dns/records/{domain}").mock(
        return_value=Response(200, json={"items": []})
    )

    result = runner.invoke(app, ["dns", "list", "--domain", domain])

    assert result.exit_code == 0
    assert f"No DNS records found for {domain}." in result.stdout


@respx.mock
def test_list_dns_records_json() -> None:
    """Test DNS record listing in JSON format."""
    domain = "example.com"
    respx.get(f"https://spaceship.dev/api/v1/dns/records/{domain}").mock(
        return_value=Response(
            200, json={"items": [{"type": "A", "address": "1.1.1.1"}], "total": 1}
        )
    )
    result = runner.invoke(app, ["dns", "list", "--domain", domain, "--format", "json"])
    assert result.exit_code == 0
    assert '"1.1.1.1"' in result.stdout
