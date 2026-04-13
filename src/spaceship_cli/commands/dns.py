"""
DNS commands for the Spaceship CLI.
"""

from typing import Optional
import httpx
import typer
from rich.table import Table
from spaceship_cli.client import SpaceshipClient
from spaceship_cli.utils import print_output

app = typer.Typer()


@app.command(name="list")
def list_dns(
    domain: str = typer.Option(
        ..., "--domain", "-d", help="Domain to list records for"
    ),
    limit: int = typer.Option(100, "--limit", "-l", help="Number of records to return"),
    offset: int = typer.Option(0, "--offset", "-o", help="Number of records to skip"),
    order_by: Optional[str] = typer.Option(
        None, "--order-by", help="Sort order (e.g., 'name', '-name', 'type', '-type')"
    ),
    output_format: str = typer.Option(
        "table", "--format", help="Output format: table or json"
    ),
) -> None:
    """
    List DNS records for a domain.
    """
    client = SpaceshipClient()
    try:
        data = client.list_dns_records(
            domain=domain, limit=limit, offset=offset, order_by=order_by
        )

        items = data.get("items", []) if isinstance(data, dict) else data

        if not items:
            print_output(
                f"No DNS records found for {domain}.", output_format=output_format
            )
            return

        table = Table(title=f"DNS Records for {domain}")
        table.add_column("Type", style="cyan")
        table.add_column("Host", style="magenta")
        table.add_column("Value", style="green")
        table.add_column("TTL", style="yellow")

        for item in items:
            record_type = item.get("type", "N/A")
            host = item.get("name", "@")
            value = item.get("value") or item.get("address") or "N/A"
            ttl = item.get("ttl", "N/A")

            table.add_row(str(record_type), str(host), str(value), str(ttl))

        print_output(data, output_format=output_format, table=table)

    except (httpx.HTTPStatusError, RuntimeError) as e:
        print_output(f"[red]Error fetching DNS records:[/red] {e}")
