import typer
from rich.console import Console
from rich.table import Table
from spaceship_cli.client import SpaceshipClient

app = typer.Typer()
console = Console()

@app.command(name="list")
def list_contacts(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of contacts to return"),
    offset: int = typer.Option(0, "--offset", "-o", help="Number of contacts to skip"),
):
    """
    List contacts.
    """
    client = SpaceshipClient()
    try:
        data = client.list_contacts(limit=limit, offset=offset)
        
        items = data.get("items", []) if isinstance(data, dict) else data

        if not items:
            console.print("No contacts found.")
            return

        table = Table(title="Contacts")
        table.add_column("ID", style="cyan")
        table.add_column("First Name", style="magenta")
        table.add_column("Last Name", style="magenta")
        table.add_column("Email", style="green")

        for item in items:
            table.add_row(
                str(item.get("id", "N/A")),
                item.get("firstName", "N/A"),
                item.get("lastName", "N/A"),
                item.get("email", "N/A")
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error fetching contacts:[/red] {e}")
