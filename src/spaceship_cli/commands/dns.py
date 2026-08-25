"""
DNS commands for the Spaceship CLI.
"""

import json
from typing import Any, Optional
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


@app.command(name="add")
# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals,too-many-branches
def add_dns(
    domain: str = typer.Option(..., "--domain", "-d", help="Domain to add records for"),
    file: Optional[str] = typer.Option(
        None, "--file", "-f", help="Path to JSON file with records"
    ),
    record_type: Optional[str] = typer.Option(
        None, "--type", "-t", help="Record type (A, CNAME, TXT, etc.)"
    ),
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Host/name (e.g., '@', 'www')"
    ),
    value: Optional[str] = typer.Option(None, "--value", "-v", help="Value or address"),
    ttl: Optional[int] = typer.Option(3600, "--ttl", help="TTL in seconds"),
    output_format: str = typer.Option(
        "table", "--format", help="Output format: table or json"
    ),
) -> None:
    """
    Add DNS records for a domain without deleting existing records.
    Supports bulk additions via a JSON file.
    """
    new_records = []

    if file:
        try:
            with open(file, "r", encoding="utf-8") as f:
                new_records.extend(json.load(f))
        except Exception as e:
            typer.secho(
                f"Error reading file {file}: {e}", fg=typer.colors.RED, err=True
            )
            raise typer.Exit(code=1)

    if record_type and name and value:
        rec = {"type": record_type.upper(), "name": name, "ttl": ttl}
        if record_type.upper() in ["A", "AAAA"]:
            rec["address"] = value
        else:
            rec["value"] = value
        new_records.append(rec)

    if not new_records:
        typer.secho(
            "Error: You must provide either --file or --type, --name, and --value options.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    client = SpaceshipClient()
    try:
        # Fetch existing
        existing_items = client.get_all_dns_records(domain=domain)

        merged_records = []
        for er in existing_items:
            merged_records.append(er)

        for nr in new_records:
            duplicate = False
            for mr in merged_records:
                # Basic duplicate check
                mr_val = mr.get("value") or mr.get("address")
                nr_val = nr.get("value") or nr.get("address")
                if (
                    mr.get("type") == nr.get("type")
                    and mr.get("name") == nr.get("name")
                    and mr_val == nr_val
                ):
                    duplicate = True
                    break
            if not duplicate:
                merged_records.append(nr)

        client.replace_dns_records(domain, merged_records)

        table = Table(title=f"Successfully added DNS Records for {domain}")
        table.add_column("Type", style="cyan")
        table.add_column("Host", style="magenta")
        table.add_column("Value", style="green")
        table.add_column("TTL", style="yellow")
        table.add_column("Status", style="blue")

        for item in new_records:
            t = item.get("type", "N/A")
            h = item.get("name", "@")
            v = item.get("value") or item.get("address") or "N/A"
            tl = item.get("ttl", "N/A")
            table.add_row(str(t), str(h), str(v), str(tl), "Success")

        print_output(new_records, output_format=output_format, table=table)

    except (httpx.HTTPStatusError, RuntimeError) as e:
        print_output(f"[red]Error saving DNS records:[/red] {e}")


@app.command(name="delete")
# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals,too-many-branches,too-many-statements,too-many-nested-blocks
def delete_dns(
    domain: str = typer.Option(
        ..., "--domain", "-d", help="Domain to delete records from"
    ),
    file: Optional[str] = typer.Option(
        None, "--file", "-f", help="Path to JSON file with records to delete"
    ),
    record_type: Optional[str] = typer.Option(
        None, "--type", "-t", help="Record type (A, CNAME, TXT, etc.)"
    ),
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Host/name (e.g., '@', 'www')"
    ),
    value: Optional[str] = typer.Option(
        None, "--value", "-v", help="Value or address (optional, for exact match)"
    ),
    output_format: str = typer.Option(
        "table", "--format", help="Output format: table or json"
    ),
) -> None:
    """
    Delete DNS records for a domain.
    Supports bulk deletions via a JSON file.
    """
    records_to_delete = []

    if file:
        try:
            with open(file, "r", encoding="utf-8") as f:
                records_to_delete.extend(json.load(f))
        except Exception as e:
            typer.secho(
                f"Error reading file {file}: {e}", fg=typer.colors.RED, err=True
            )
            raise typer.Exit(code=1)

    if record_type and name:
        rec = {"type": record_type.upper(), "name": name}
        if value:
            if record_type.upper() in ["A", "AAAA"]:
                rec["address"] = value
            else:
                rec["value"] = value
        records_to_delete.append(rec)

    if not records_to_delete:
        typer.secho(
            "Error: You must provide either --file or --type and --name options.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    client = SpaceshipClient()
    try:
        # Fetch existing
        existing_items = client.get_all_dns_records(domain=domain)

        remaining_records = []
        deleted_records = []

        for er in existing_items:
            should_delete = False
            er_val = er.get("value") or er.get("address")
            for dr in records_to_delete:
                dr_val = dr.get("value") or dr.get("address")

                # Check for match (if dr_val is provided, it must match exactly)
                if er.get("type") == dr.get("type") and er.get("name") == dr.get(
                    "name"
                ):
                    if dr_val:
                        if er_val == dr_val:
                            should_delete = True
                            break
                    else:
                        should_delete = True
                        break

            if should_delete:
                deleted_records.append(er)
            else:
                remaining_records.append(er)

        if not deleted_records:
            typer.secho(
                f"No matching DNS records found to delete for {domain}.",
                fg=typer.colors.YELLOW,
            )
            raise typer.Exit(code=0)

        # Clean deleted records for the DELETE payload
        clean_deleted: list[dict[str, Any]] = []
        for dr in deleted_records:
            item: dict[str, Any] = {
                "type": dr["type"],
                "name": dr["name"],
            }
            if "address" in dr:
                item["address"] = dr["address"]
            if "value" in dr:
                item["value"] = dr["value"]
            clean_deleted.append(item)

        client.delete_dns_records(domain, clean_deleted)

        table = Table(title=f"Successfully deleted DNS Records for {domain}")
        table.add_column("Type", style="cyan")
        table.add_column("Host", style="magenta")
        table.add_column("Value", style="green")
        table.add_column("TTL", style="yellow")
        table.add_column("Status", style="red")

        for item in deleted_records:
            t = item.get("type", "N/A")
            h = item.get("name", "@")
            v = item.get("value") or item.get("address") or "N/A"
            tl = item.get("ttl", "N/A")
            table.add_row(str(t), str(h), str(v), str(tl), "Deleted")

        print_output(deleted_records, output_format=output_format, table=table)

    except typer.Exit:
        raise
    except (httpx.HTTPStatusError, RuntimeError) as e:
        print_output(f"[red]Error saving DNS records:[/red] {e}")


@app.command(name="update")
# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals,too-many-branches,too-many-statements
def update_dns(
    domain: str = typer.Option(
        ..., "--domain", "-d", help="Domain to update records for"
    ),
    record_type: str = typer.Option(
        ..., "--type", "-t", help="Record type (A, CNAME, TXT, etc.)"
    ),
    name: str = typer.Option(..., "--name", "-n", help="Host/name (e.g., '@', 'www')"),
    current_value: Optional[str] = typer.Option(
        None,
        "--current-value",
        help="Current value of the record to update (required if multiple exist)",
    ),
    new_value: Optional[str] = typer.Option(
        None, "--new-value", "-v", help="New value or address to set"
    ),
    new_ttl: Optional[int] = typer.Option(
        None, "--new-ttl", help="New TTL to set in seconds"
    ),
    output_format: str = typer.Option(
        "table", "--format", help="Output format: table or json"
    ),
) -> None:
    """
    Update an existing DNS record's value or TTL in-place.
    """
    if not new_value and not new_ttl:
        typer.secho(
            "Error: You must specify at least one property to update: "
            "--new-value or --new-ttl.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    client = SpaceshipClient()
    try:
        # Fetch existing records
        existing_items = client.get_all_dns_records(domain=domain)

        # Find matching records
        matches = []
        for er in existing_items:
            er_val = er.get("value") or er.get("address")
            if er.get("type") == record_type.upper() and er.get("name") == name:
                if current_value:
                    if er_val == current_value:
                        matches.append(er)
                else:
                    matches.append(er)

        if not matches:
            typer.secho(
                f"Error: No matching DNS record found for {domain} with "
                f"type={record_type.upper()}, name={name}"
                + (f", current_value={current_value}" if current_value else "")
                + ".",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=1)

        if len(matches) > 1:
            typer.secho(
                f"Error: Multiple matching DNS records found for {domain} "
                f"with type={record_type.upper()}, name={name}. "
                "Please specify --current-value to identify which record "
                "to update.",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=1)

        # Update the single matched record in-place in existing_items list
        matched_record = matches[0]
        old_val = matched_record.get("value") or matched_record.get("address")
        old_ttl = matched_record.get("ttl")

        # Delete old record if the value/address is changing
        if new_value:
            old_record_cleaned: dict[str, Any] = {
                "type": record_type.upper(),
                "name": name,
            }
            if record_type.upper() in ["A", "AAAA"]:
                old_record_cleaned["address"] = old_val
            else:
                old_record_cleaned["value"] = old_val
            client.delete_dns_records(domain, [old_record_cleaned])

        # Save/update new record
        new_record_cleaned: dict[str, Any] = {
            "type": record_type.upper(),
            "name": name,
            "ttl": new_ttl or old_ttl,
        }
        if record_type.upper() in ["A", "AAAA"]:
            new_record_cleaned["address"] = new_value or old_val
        else:
            new_record_cleaned["value"] = new_value or old_val

        client.replace_dns_records(domain, [new_record_cleaned])

        table = Table(title=f"Successfully updated DNS Record for {domain}")
        table.add_column("Type", style="cyan")
        table.add_column("Host", style="magenta")
        table.add_column("Old Value", style="red")
        table.add_column("New Value", style="green")
        table.add_column("Old TTL", style="yellow")
        table.add_column("New TTL", style="green")
        table.add_column("Status", style="blue")

        final_val = (
            new_record_cleaned.get("value")
            or new_record_cleaned.get("address")
            or "N/A"
        )
        final_ttl = new_record_cleaned.get("ttl", "N/A")

        table.add_row(
            record_type.upper(),
            name,
            str(old_val),
            str(final_val),
            str(old_ttl),
            str(final_ttl),
            "Updated",
        )

        print_output([new_record_cleaned], output_format=output_format, table=table)

    except typer.Exit:
        raise
    except (httpx.HTTPStatusError, RuntimeError) as e:
        print_output(f"[red]Error updating DNS record:[/red] {e}")
