import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from spaceship_cli.client import SpaceshipClient

app = typer.Typer()
console = Console()

@app.command(name="list")
def list_domains(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of domains to return"),
    offset: int = typer.Option(0, "--offset", "-o", help="Number of domains to skip"),
):
    """
    List domains.
    """
    client = SpaceshipClient()
    try:
        data = client.list_domains(limit=limit, offset=offset)
        
        # Assuming the response has a structure like {'items': [...], 'totalCount': ...}
        # or it is a list. I will handle generic json first.
        # Docs usually specify a wrapper.
        
        items = data.get("items", []) if isinstance(data, dict) else data

        if not items:
            console.print("No domains found.")
            return

        table = Table(title="Domains")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Expiration", style="green")

        for item in items:
            # Adjust keys based on actual response payload.
            # Common keys: name, status, expirationDate
            name = item.get("name", "N/A")
            status = item.get("status", "N/A") 
            expiration = item.get("expirationDate", "N/A")
            table.add_row(name, str(status), str(expiration))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error fetching domains:[/red] {e}")

@app.command()
def info(
    domain: str = typer.Argument(..., help="Domain name to get info for"),
):
    """
    Get detailed information for a specific domain.
    """
    client = SpaceshipClient()
    try:
        data = client.get_domain_info(domain)
        
        table = Table(title=f"Domain Info: {domain}", show_header=False)
        table.add_column("Property", style="bold cyan")
        table.add_column("Value")

        # Dynamically add rows based on available data
        for key, value in data.items():
            table.add_row(key, str(value))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error fetching domain info for {domain}:[/red] {e}")

@app.command()
def check(
    names: list[str] = typer.Argument(..., help="Domain names to check availability for"),
):
    """
    Check if one or more domains are available for registration.
    """
    client = SpaceshipClient()
    try:
        data = client.check_availability(names)
        
        # Response structure: {"domains": [{"domain": "name", "result": "available", ...}]}
        items = data.get("domains", []) if isinstance(data, dict) else data

        if not items:
            console.print("No availability data returned.")
            return

        table = Table(title="Domain Availability")
        table.add_column("Domain", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Premium Pricing", style="green")

        for item in items:
            domain = item.get("domain", "N/A")
            result = item.get("result", "unknown")
            premium = item.get("premiumPricing", [])
            
            status_style = "green" if result == "available" else "red"
            status = f"[{status_style}]{result}[/{status_style}]"
            
            table.add_row(domain, status, str(premium) if premium else "None")

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error checking availability:[/red] {e}")
