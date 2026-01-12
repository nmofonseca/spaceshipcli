import os

# Set dummy env vars for testing before importing the app
os.environ["SPACESHIP_API_KEY"] = "test_key"
os.environ["SPACESHIP_API_SECRET"] = "test_secret"

import pytest
import respx
from httpx import Response
from typer.testing import CliRunner
from spaceship_cli.main import app

runner = CliRunner()

@respx.mock
def test_list_dns_records_success():
    domain = "example.com"
    # Mock the API response
    route = respx.get(f"https://spaceship.dev/api/v1/dns/records/{domain}").mock(
        return_value=Response(
            200, 
            json={
                "items": [
                    {"type": "A", "name": "@", "address": "1.2.3.4", "ttl": 3600},
                    {"type": "CNAME", "name": "www", "value": "example.com", "ttl": 3600}
                ]
            }
        )
    )

    result = runner.invoke(app, ["dns", "list", "--domain", domain, "--order-by", "name"])
    
    assert result.exit_code == 0
    assert "example.com" in result.stdout
    assert "1.2.3.4" in result.stdout
    assert "CNAME" in result.stdout
    assert route.called
    # Check that query params were passed
    request = route.calls.last.request
    from urllib.parse import parse_qs
    qs = parse_qs(request.url.query.decode())
    assert qs["take"] == ["100"]
    assert qs["skip"] == ["0"]
    assert qs["orderBy"] == ["name"]

@respx.mock
def test_list_dns_records_empty():
    domain = "nodata.com"
    respx.get(f"https://spaceship.dev/api/v1/dns/records/{domain}").mock(
        return_value=Response(200, json={"items": []})
    )

    result = runner.invoke(app, ["dns", "list", "--domain", domain])
    
    assert result.exit_code == 0
    assert f"No DNS records found for {domain}." in result.stdout
