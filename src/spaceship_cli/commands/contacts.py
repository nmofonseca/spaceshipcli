import typer
from rich.console import Console
from rich.table import Table
from spaceship_cli.client import SpaceshipClient

app = typer.Typer()
console = Console()

@app.command()
def info(
    contact_id: str = typer.Argument(..., help="Contact ID to get attributes for"),
):
    """
    Get detailed attributes for a specific contact.
    """
    client = SpaceshipClient()
    try:
        data = client.get_contact_attributes(contact_id)
        
        # Response is a list of {"name": "...", "value": "..."}
        if not data:
            console.print("No attributes found for this contact.")
            return

        table = Table(title=f"Contact Attributes: {contact_id}")
        table.add_column("Attribute", style="cyan")
        table.add_column("Value", style="green")

        for item in data:
            attr_name = item.get("name", "N/A")
            attr_value = item.get("value", "N/A")
            table.add_row(attr_name, str(attr_value))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error fetching contact info:[/red] {e}")