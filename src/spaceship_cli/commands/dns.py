"""
DNS commands for the Spaceship CLI.
"""

import json
from typing import Any, Optional
import httpx
import typer
from rich.table import Table
from spaceship_cli.client import SpaceshipClient
from spaceship_cli.dns_records import (
    build_record_from_cli,
    clean_record_for_delete,
    clean_record_for_put,
    get_record_value,
    normalize_record,
    records_match,
)
from spaceship_cli.utils import print_output

app = typer.Typer()


def _format_record_value(item: dict[str, Any]) -> str:
    value = get_record_value(item)
    return str(value) if value is not None else "N/A"


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
            value = _format_record_value(item)
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
    preference: Optional[int] = typer.Option(
        None, "--preference", help="MX preference / priority (MX records)"
    ),
    output_format: str = typer.Option(
        "table", "--format", help="Output format: table or json"
    ),
) -> None:
    """
    Add DNS records for a domain without deleting existing records.
    Supports bulk additions via a JSON file.

    Simple CLI flags map --value to the Spaceship type-specific field
    (e.g. CNAME -> cname, A/AAAA -> address, MX -> exchange).
    """
    new_records: list[dict[str, Any]] = []

    if file:
        try:
            with open(file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if not isinstance(loaded, list):
                raise ValueError("JSON file must contain an array of records")
            new_records.extend(normalize_record(item) for item in loaded)
        except Exception as e:
            typer.secho(
                f"Error reading file {file}: {e}", fg=typer.colors.RED, err=True
            )
            raise typer.Exit(code=1)

    if record_type and name and value:
        new_records.append(
            build_record_from_cli(
                record_type=record_type,
                name=name,
                value=value,
                ttl=ttl,
                preference=preference,
            )
        )

    if not new_records:
        typer.secho(
            "Error: You must provide either --file or --type, --name, and --value options.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    client = SpaceshipClient()
    try:
        existing_items = client.get_all_dns_records(domain=domain)

        merged_records = [clean_record_for_put(er) for er in existing_items]

        for nr in new_records:
            candidate = clean_record_for_put(nr)
            duplicate = any(
                records_match(mr, candidate, require_value=True)
                for mr in merged_records
            )
            if not duplicate:
                merged_records.append(candidate)

        client.replace_dns_records(domain, merged_records)

        table = Table(title=f"Successfully added DNS Records for {domain}")
        table.add_column("Type", style="cyan")
        table.add_column("Host", style="magenta")
        table.add_column("Value", style="green")
        table.add_column("TTL", style="yellow")
        table.add_column("Status", style="blue")

        for item in new_records:
            cleaned = clean_record_for_put(item)
            table.add_row(
                str(cleaned.get("type", "N/A")),
                str(cleaned.get("name", "@")),
                _format_record_value(cleaned),
                str(cleaned.get("ttl", "N/A")),
                "Success",
            )

        print_output(
            [clean_record_for_put(r) for r in new_records],
            output_format=output_format,
            table=table,
        )

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
    preference: Optional[int] = typer.Option(
        None, "--preference", help="MX preference (optional, for exact MX match)"
    ),
    output_format: str = typer.Option(
        "table", "--format", help="Output format: table or json"
    ),
) -> None:
    """
    Delete DNS records for a domain.
    Supports bulk deletions via a JSON file.
    """
    records_to_delete: list[dict[str, Any]] = []

    if file:
        try:
            with open(file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if not isinstance(loaded, list):
                raise ValueError("JSON file must contain an array of records")
            records_to_delete.extend(normalize_record(item) for item in loaded)
        except Exception as e:
            typer.secho(
                f"Error reading file {file}: {e}", fg=typer.colors.RED, err=True
            )
            raise typer.Exit(code=1)

    if record_type and name:
        if value is not None:
            rec = build_record_from_cli(
                record_type=record_type,
                name=name,
                value=value,
                preference=preference,
            )
            rec.pop("ttl", None)
        else:
            rec = {"type": record_type.upper(), "name": name}
            if preference is not None:
                rec["preference"] = preference
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
        existing_items = client.get_all_dns_records(domain=domain)

        deleted_records: list[dict[str, Any]] = []

        for er in existing_items:
            should_delete = any(
                records_match(
                    er,
                    dr,
                    require_value=get_record_value(dr) is not None,
                )
                for dr in records_to_delete
            )
            if should_delete:
                deleted_records.append(er)

        if not deleted_records:
            typer.secho(
                f"No matching DNS records found to delete for {domain}.",
                fg=typer.colors.YELLOW,
            )
            raise typer.Exit(code=0)

        clean_deleted = [clean_record_for_delete(dr) for dr in deleted_records]
        client.delete_dns_records(domain, clean_deleted)

        table = Table(title=f"Successfully deleted DNS Records for {domain}")
        table.add_column("Type", style="cyan")
        table.add_column("Host", style="magenta")
        table.add_column("Value", style="green")
        table.add_column("TTL", style="yellow")
        table.add_column("Status", style="red")

        for item in deleted_records:
            table.add_row(
                str(item.get("type", "N/A")),
                str(item.get("name", "@")),
                _format_record_value(item),
                str(item.get("ttl", "N/A")),
                "Deleted",
            )

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
    preference: Optional[int] = typer.Option(
        None, "--preference", help="MX preference (kept/updated for MX records)"
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
        existing_items = client.get_all_dns_records(domain=domain)
        rtype = record_type.upper()

        matcher: dict[str, Any] = {"type": rtype, "name": name}
        if current_value is not None:
            matcher = build_record_from_cli(
                record_type=rtype,
                name=name,
                value=current_value,
                preference=preference,
            )
            matcher.pop("ttl", None)

        matches = [
            er
            for er in existing_items
            if records_match(
                er,
                matcher,
                require_value=current_value is not None,
            )
        ]

        if not matches:
            typer.secho(
                f"Error: No matching DNS record found for {domain} with "
                f"type={rtype}, name={name}"
                + (f", current_value={current_value}" if current_value else "")
                + ".",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=1)

        if len(matches) > 1:
            typer.secho(
                f"Error: Multiple matching DNS records found for {domain} "
                f"with type={rtype}, name={name}. "
                "Please specify --current-value to identify which record "
                "to update.",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=1)

        matched_record = matches[0]
        old_val = get_record_value(matched_record)
        old_ttl = matched_record.get("ttl")

        if new_value:
            client.delete_dns_records(
                domain, [clean_record_for_delete(matched_record)]
            )

        new_record = clean_record_for_put(matched_record)
        new_record["ttl"] = new_ttl if new_ttl is not None else old_ttl
        if new_value is not None:
            rebuilt = build_record_from_cli(
                record_type=rtype,
                name=name,
                value=new_value,
                ttl=new_record["ttl"],
                preference=(
                    preference
                    if preference is not None
                    else matched_record.get("preference")
                ),
            )
            new_record = clean_record_for_put(rebuilt)
        elif preference is not None and rtype == "MX":
            new_record["preference"] = preference

        client.replace_dns_records(domain, [new_record])

        table = Table(title=f"Successfully updated DNS Record for {domain}")
        table.add_column("Type", style="cyan")
        table.add_column("Host", style="magenta")
        table.add_column("Old Value", style="red")
        table.add_column("New Value", style="green")
        table.add_column("Old TTL", style="yellow")
        table.add_column("New TTL", style="green")
        table.add_column("Status", style="blue")

        final_val = get_record_value(new_record)
        final_ttl = new_record.get("ttl", "N/A")

        table.add_row(
            rtype,
            name,
            str(old_val),
            str(final_val if final_val is not None else "N/A"),
            str(old_ttl),
            str(final_ttl),
            "Updated",
        )

        print_output([new_record], output_format=output_format, table=table)

    except typer.Exit:
        raise
    except (httpx.HTTPStatusError, RuntimeError) as e:
        print_output(f"[red]Error updating DNS record:[/red] {e}")
