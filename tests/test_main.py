from typer.testing import CliRunner
from spaceship_cli.main import app

runner = CliRunner()

def test_app_no_args_shows_help():
    """Test that running the app without arguments shows the help/usage."""
    result = runner.invoke(app, [])
    # Since no_args_is_help=True, it will exit with code 0 or 2 depending on typer version
    # The output should contain the CLI usage message
    assert "Usage:" in result.stdout
    assert "Spaceship.com CLI Tool" in result.stdout
    assert "Options" in result.stdout
    assert "Commands" in result.stdout
