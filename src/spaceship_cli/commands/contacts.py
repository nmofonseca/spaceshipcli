"""
Contacts commands for the Spaceship CLI.
"""

import httpx
import typer
from rich.table import Table
from spaceship_cli.client import SpaceshipClient
from spaceship_cli.utils import print_output

app = typer.Typer()


@app.command()
def info(
    contact_id: str = typer.Argument(..., help="Contact ID to get attributes for"),
    output_format: str = typer.Option(
        "table", "--format", help="Output format: table or json"
    ),
) -> None:
    """
    Get detailed attributes for a specific contact.
    """
    client = SpaceshipClient()
    try:
        data = client.get_contact_attributes(contact_id)

        # Response is a list of {"name": "...", "value": "..."}
        if not data:
            print_output(
                "No attributes found for this contact.", output_format=output_format
            )
            return

        table = Table(title=f"Contact Attributes: {contact_id}")
        table.add_column("Attribute", style="cyan")
        table.add_column("Value", style="green")

        for item in data:
            attr_name = item.get("name", "N/A")
            attr_value = item.get("value", "N/A")
            table.add_row(attr_name, str(attr_value))

        print_output(data, output_format=output_format, table=table)

    except (httpx.HTTPStatusError, RuntimeError) as e:
        print_output(f"[red]Error fetching contact info:[/red] {e}")
