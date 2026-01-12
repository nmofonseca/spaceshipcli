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
                    {"name": "example.com", "status": "active", "expirationDate": "2027-01-01"},
                    {"name": "test.org", "status": "expired", "expirationDate": "2025-01-01"}
                ]
            }
        )
    )

    result = runner.invoke(app, ["domains", "list"])
    
    assert result.exit_code == 0
    assert "example.com" in result.stdout
    assert "test.org" in result.stdout
    assert route.called

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
