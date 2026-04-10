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
def test_list_domains_success():
    # Mock the API response
    route = respx.get("https://spaceship.dev/api/v1/domains").mock(
        return_value=Response(
            200, 
            json={
                "items": [
                    {"name": "example.com", "lifecycleStatus": "active", "expirationDate": "2027-01-01"},
                    {"name": "test.org", "lifecycleStatus": "expired", "expirationDate": "2025-01-01"}
                ]
            }
        )
    )

    result = runner.invoke(app, ["domains", "list", "--order-by", "name"])
    
    assert result.exit_code == 0
    assert "example.com" in result.stdout
    assert "test.org" in result.stdout
    assert route.called
    
    # Check that query params were passed
    request = route.calls.last.request
    from urllib.parse import parse_qs
    qs = parse_qs(request.url.query.decode())
    assert qs["orderBy"] == ["name"]
    assert qs["take"] == ["10"]  # default
    assert qs["skip"] == ["0"]   # default

@respx.mock
def test_list_domains_empty():
    respx.get("https://spaceship.dev/api/v1/domains").mock(
        return_value=Response(200, json={"items": []})
    )

    result = runner.invoke(app, ["domains", "list"])
    
    assert result.exit_code == 0
    assert "No domains found." in result.stdout

@respx.mock
def test_check_availability():
    # Mock the API response
    respx.post("https://spaceship.dev/api/v1/domains/available").mock(
        return_value=Response(
            200, 
            json={
                "domains": [
                    {"domain": "available.com", "result": "available", "premiumPricing": []},
                    {"domain": "taken.com", "result": "unavailable", "premiumPricing": []}
                ]
            }
        )
    )

    result = runner.invoke(app, ["domains", "check", "available.com", "taken.com"])
    
    assert result.exit_code == 0
    assert "available.com" in result.stdout
    assert "available" in result.stdout
    assert "taken.com" in result.stdout
    assert "unavailable" in result.stdout

@respx.mock
def test_get_personal_nameservers():
    domain = "example.com"
    # Mock the API response
    respx.get(f"https://spaceship.dev/api/v1/domains/{domain}/personal-nameservers").mock(
        return_value=Response(
            200, 
            json={
                "records": [
                    {"host": "ns1", "ips": ["1.2.3.4", "5.6.7.8"]},
                    {"host": "ns2", "ips": ["9.10.11.12"]}
                ]
            }
        )
    )

    result = runner.invoke(app, ["domains", "nameservers", domain])
    
    assert result.exit_code == 0
    assert "ns1" in result.stdout
    assert "1.2.3.4, 5.6.7.8" in result.stdout
    assert "ns2" in result.stdout
    assert "9.10.11.12" in result.stdout

@respx.mock
def test_get_domain_transfer():
    domain = "example.com"
    respx.get(f"https://spaceship.dev/api/v1/domains/{domain}/transfer").mock(
        return_value=Response(
            200, 
            json={
                "startedAt": "2024-01-01T00:00:00Z",
                "finishedAt": "2024-01-02T00:00:00Z",
                "direction": "in",
                "status": "success"
            }
        )
    )

    result = runner.invoke(app, ["domains", "transfer", domain])
    
    assert result.exit_code == 0
    assert "in" in result.stdout
    assert "success" in result.stdout

@respx.mock
def test_get_domain_auth_code():
    domain = "example.com"
    respx.get(f"https://spaceship.dev/api/v1/domains/{domain}/transfer/auth-code").mock(
        return_value=Response(
            200, 
            json={
                "authCode": "secret123",
                "expires": "2024-02-01T00:00:00Z"
            }
        )
    )

    result = runner.invoke(app, ["domains", "auth-code", domain])
    
    assert result.exit_code == 0
    assert "secret123" in result.stdout
    assert "2024-02-01" in result.stdout
