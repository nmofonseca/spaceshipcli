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
def test_get_contact_attributes():
    contact_id = "test_id_123"
    # Mock the API response
    route = respx.get(f"https://spaceship.dev/api/v1/contacts/attributes/{contact_id}").mock(
        return_value=Response(
            200, 
            json=[
                {"name": "firstName", "value": "Alice"},
                {"name": "lastName", "value": "Wonderland"},
                {"name": "email", "value": "alice@example.com"}
            ]
        )
    )

    result = runner.invoke(app, ["contacts", "info", contact_id])
    
    assert result.exit_code == 0
    assert "Alice" in result.stdout
    assert "Wonderland" in result.stdout
    assert "alice@example.com" in result.stdout
    assert route.called