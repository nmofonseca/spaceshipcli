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
def test_list_contacts_success():
    # Mock the API response
    route = respx.get("https://spaceship.dev/api/v1/contacts").mock(
        return_value=Response(
            200, 
            json={
                "items": [
                    {"id": "c1", "firstName": "John", "lastName": "Doe", "email": "john@example.com"},
                    {"id": "c2", "firstName": "Jane", "lastName": "Smith", "email": "jane@example.com"}
                ]
            }
        )
    )

    result = runner.invoke(app, ["contacts", "list"])
    
    assert result.exit_code == 0
    assert "John" in result.stdout
    assert "jane@example.com" in result.stdout
    assert route.called
