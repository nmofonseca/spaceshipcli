import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from spaceship_cli.client import SpaceshipClient

app = typer.Typer()
console = Console()

@app.command(name="list")
def list_dns(
    domain: str = typer.Option(..., "--domain", "-d", help="Domain to list records for"),
    limit: int = typer.Option(100, "--limit", "-l", help="Number of records to return"),
    offset: int = typer.Option(0, "--offset", "-o", help="Number of records to skip"),
    order_by: Optional[str] = typer.Option(None, "--order-by", help="Sort order (e.g., 'name', '-name', 'type', '-type')"),
    format: str = typer.Option("table", "--format", help="Output format: table or json"),
):
    """
    List DNS records for a domain.
    """
    client = SpaceshipClient()
    try:
        data = client.list_dns_records(domain=domain, limit=limit, offset=offset, order_by=order_by)
        
        if format == "json":
            console.print_json(data=data)
            return

        # Adjust based on response structure.
        items = data.get("items", []) if isinstance(data, dict) else data

        if not items:
            console.print(f"No DNS records found for {domain}.")
            return

        table = Table(title=f"DNS Records for {domain}")
        table.add_column("Type", style="cyan")
        table.add_column("Host", style="magenta")
        table.add_column("Value", style="green")
        table.add_column("TTL", style="yellow")

        for item in items:
            # Keys from API: type, name, value OR address, ttl, priority, etc.
            # It seems 'value' is used for TXT, but 'address' for A records.
            record_type = item.get("type", "N/A")
            host = item.get("name", "@") 
            value = item.get("value") or item.get("address") or "N/A"
            ttl = item.get("ttl", "N/A")
            
            table.add_row(str(record_type), str(host), str(value), str(ttl))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error fetching DNS records:[/red] {e}")
