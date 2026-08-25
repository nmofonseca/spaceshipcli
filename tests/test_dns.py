"""
Tests for DNS commands.
"""

import os
import json
from urllib.parse import parse_qs
import respx
from httpx import Response
from typer.testing import CliRunner
from spaceship_cli.main import app

# Set dummy env vars for testing before importing the app
os.environ["SPACESHIP_API_KEY"] = "test_key"
os.environ["SPACESHIP_API_SECRET"] = "test_secret"

runner = CliRunner()


@respx.mock
def test_list_dns_records_success() -> None:
    """Test successful DNS record listing."""
    domain = "example.com"
    # Mock the API response
    route = respx.get(f"https://spaceship.dev/api/v1/dns/records/{domain}").mock(
        return_value=Response(
            200,
            json={
                "items": [
                    {"type": "A", "name": "@", "address": "1.2.3.4", "ttl": 3600},
                    {
                        "type": "CNAME",
                        "name": "www",
                        "value": "example.com",
                        "ttl": 3600,
                    },
                ]
            },
        )
    )

    result = runner.invoke(
        app, ["dns", "list", "--domain", domain, "--order-by", "name"]
    )

    assert result.exit_code == 0
    # Use count() > 0 to avoid CodeQL incomplete-url-substring-sanitization false positive
    assert result.stdout.count("example.com") > 0
    assert "1.2.3.4" in result.stdout
    assert "CNAME" in result.stdout
    assert route.called
    # Check that query params were passed
    request = route.calls.last.request
    qs = parse_qs(request.url.query.decode())
    assert qs["take"] == ["100"]
    assert qs["skip"] == ["0"]
    assert qs["orderBy"] == ["name"]


@respx.mock
def test_list_dns_records_empty() -> None:
    """Test DNS record listing with no results."""
    domain = "nodata.com"
    respx.get(f"https://spaceship.dev/api/v1/dns/records/{domain}").mock(
        return_value=Response(200, json={"items": []})
    )

    result = runner.invoke(app, ["dns", "list", "--domain", domain])

    assert result.exit_code == 0
    assert f"No DNS records found for {domain}." in result.stdout


@respx.mock
def test_list_dns_records_json() -> None:
    """Test DNS record listing in JSON format."""
    domain = "example.com"
    respx.get(f"https://spaceship.dev/api/v1/dns/records/{domain}").mock(
        return_value=Response(
            200, json={"items": [{"type": "A", "address": "1.1.1.1"}], "total": 1}
        )
    )
    result = runner.invoke(app, ["dns", "list", "--domain", domain, "--format", "json"])
    assert result.exit_code == 0
    assert '"1.1.1.1"' in result.stdout


@respx.mock
def test_add_dns_records_single() -> None:
    """Test adding a single DNS record."""
    domain = "example.com"
    route_get = respx.get(f"https://spaceship.dev/api/v1/dns/records/{domain}").mock(
        return_value=Response(
            200,
            json={
                "items": [{"type": "A", "name": "@", "address": "1.2.3.4", "ttl": 3600}]
            },
        )
    )
    route_put = respx.put(f"https://spaceship.dev/api/v1/dns/records/{domain}").mock(
        return_value=Response(204)
    )

    result = runner.invoke(
        app,
        [
            "dns",
            "add",
            "--domain",
            domain,
            "--type",
            "CNAME",
            "--name",
            "www",
            "--value",
            "example.com",
            "--ttl",
            "1800",
        ],
    )

    assert result.exit_code == 0
    assert "Successfully added DNS Records for example.com" in result.stdout
    assert "CNAME" in result.stdout
    assert "www" in result.stdout
    assert "example.com" in result.stdout

    assert route_get.called
    assert route_put.called

    put_request = route_put.calls.last.request
    payload = json.loads(put_request.content)
    assert payload["force"] is False
    assert len(payload["items"]) == 2
    assert payload["items"][1]["type"] == "CNAME"
    assert payload["items"][1]["name"] == "www"
    assert payload["items"][1]["value"] == "example.com"


@respx.mock
def test_add_dns_records_bulk(tmp_path) -> None:
    """Test bulk adding DNS records via a JSON file."""
    domain = "example.com"
    json_file = tmp_path / "records.json"
    records = [
        {
            "type": "TXT",
            "name": "@",
            "value": "v=spf1 include:_spf.example.com ~all",
            "ttl": 3600,
        }
    ]
    json_file.write_text(json.dumps(records))

    respx.get(f"https://spaceship.dev/api/v1/dns/records/{domain}").mock(
        return_value=Response(
            200,
            json={
                "items": [{"type": "A", "name": "@", "address": "1.2.3.4", "ttl": 3600}]
            },
        )
    )
    route_put = respx.put(f"https://spaceship.dev/api/v1/dns/records/{domain}").mock(
        return_value=Response(204)
    )

    result = runner.invoke(
        app, ["dns", "add", "--domain", domain, "--file", str(json_file)]
    )

    assert result.exit_code == 0
    assert "TXT" in result.stdout
    assert "v=spf1" in result.stdout

    put_request = route_put.calls.last.request
    payload = json.loads(put_request.content)
    assert len(payload["items"]) == 2
    assert payload["items"][1]["type"] == "TXT"


@respx.mock
def test_add_dns_duplicate() -> None:
    """Test adding a duplicate DNS record is ignored."""
    domain = "example.com"
    respx.get(f"https://spaceship.dev/api/v1/dns/records/{domain}").mock(
        return_value=Response(
            200,
            json={
                "items": [{"type": "A", "name": "@", "address": "1.2.3.4", "ttl": 3600}]
            },
        )
    )
    route_put = respx.put(f"https://spaceship.dev/api/v1/dns/records/{domain}").mock(
        return_value=Response(204)
    )

    result = runner.invoke(
        app,
        [
            "dns",
            "add",
            "--domain",
            domain,
            "--type",
            "A",
            "--name",
            "@",
            "--value",
            "1.2.3.4",
        ],
    )

    assert result.exit_code == 0

    put_request = route_put.calls.last.request
    payload = json.loads(put_request.content)
    assert len(payload["items"]) == 1


@respx.mock
def test_delete_dns_records_single() -> None:
    """Test deleting a single DNS record."""
    domain = "example.com"
    route_get = respx.get(f"https://spaceship.dev/api/v1/dns/records/{domain}").mock(
        return_value=Response(
            200,
            json={
                "items": [
                    {"type": "A", "name": "@", "address": "1.2.3.4", "ttl": 3600},
                    {"type": "TXT", "name": "@", "value": "v=spf1", "ttl": 3600},
                ]
            },
        )
    )
    route_delete = respx.delete(
        f"https://spaceship.dev/api/v1/dns/records/{domain}"
    ).mock(return_value=Response(204))

    result = runner.invoke(
        app,
        [
            "dns",
            "delete",
            "--domain",
            domain,
            "--type",
            "TXT",
            "--name",
            "@",
            "--value",
            "v=spf1",
        ],
    )

    assert result.exit_code == 0
    assert "Successfully deleted DNS Records" in result.stdout
    assert "example.com" in result.stdout
    assert "TXT" in result.stdout

    assert route_get.called
    assert route_delete.called

    delete_request = route_delete.calls.last.request
    payload = json.loads(delete_request.content)
    assert len(payload) == 1
    assert payload[0]["type"] == "TXT"


@respx.mock
def test_delete_dns_records_bulk(tmp_path) -> None:
    """Test bulk deleting DNS records via a JSON file."""
    domain = "example.com"
    json_file = tmp_path / "delete_records.json"
    records = [{"type": "A", "name": "www", "address": "1.1.1.1"}]
    json_file.write_text(json.dumps(records))

    respx.get(f"https://spaceship.dev/api/v1/dns/records/{domain}").mock(
        return_value=Response(
            200,
            json={
                "items": [
                    {"type": "A", "name": "@", "address": "1.2.3.4", "ttl": 3600},
                    {"type": "A", "name": "www", "address": "1.1.1.1", "ttl": 3600},
                ]
            },
        )
    )
    route_delete = respx.delete(
        f"https://spaceship.dev/api/v1/dns/records/{domain}"
    ).mock(return_value=Response(204))

    result = runner.invoke(
        app, ["dns", "delete", "--domain", domain, "--file", str(json_file)]
    )

    assert result.exit_code == 0
    assert "Deleted" in result.stdout

    delete_request = route_delete.calls.last.request
    payload = json.loads(delete_request.content)
    assert len(payload) == 1
    assert payload[0]["name"] == "www"


@respx.mock
def test_update_dns_success() -> None:
    """Test updating a DNS record's value and TTL successfully."""
    domain = "example.com"
    respx.get(f"https://spaceship.dev/api/v1/dns/records/{domain}").mock(
        return_value=Response(
            200,
            json={
                "items": [
                    {"type": "A", "name": "@", "address": "1.2.3.4", "ttl": 3600},
                    {
                        "type": "CNAME",
                        "name": "www",
                        "value": "old.example.com",
                        "ttl": 1800,
                    },
                ]
            },
        )
    )
    route_delete = respx.delete(
        f"https://spaceship.dev/api/v1/dns/records/{domain}"
    ).mock(return_value=Response(204))
    route_put = respx.put(f"https://spaceship.dev/api/v1/dns/records/{domain}").mock(
        return_value=Response(204)
    )

    result = runner.invoke(
        app,
        [
            "dns",
            "update",
            "--domain",
            domain,
            "--type",
            "CNAME",
            "--name",
            "www",
            "--new-value",
            "new.example.com",
            "--new-ttl",
            "3600",
        ],
    )

    assert result.exit_code == 0
    assert "Successfully updated DNS Record" in result.stdout
    assert "new.example" in result.stdout

    assert route_delete.called
    assert route_put.called

    delete_req = route_delete.calls.last.request
    del_payload = json.loads(delete_req.content)
    assert len(del_payload) == 1
    assert del_payload[0]["value"] == "old.example.com"

    put_req = route_put.calls.last.request
    put_payload = json.loads(put_req.content)
    assert len(put_payload["items"]) == 1
    assert put_payload["items"][0]["value"] == "new.example.com"
    assert put_payload["items"][0]["ttl"] == 3600


@respx.mock
def test_update_dns_no_changes() -> None:
    """Test updating a DNS record fails when no changes are specified."""
    domain = "example.com"
    result = runner.invoke(
        app,
        ["dns", "update", "--domain", domain, "--type", "A", "--name", "www"],
    )
    assert result.exit_code == 1
    assert "Error: You must specify at least one property to update" in (
        result.stdout + result.stderr
    )


@respx.mock
def test_update_dns_not_found() -> None:
    """Test updating a DNS record fails when no matching record is found."""
    domain = "example.com"
    respx.get(f"https://spaceship.dev/api/v1/dns/records/{domain}").mock(
        return_value=Response(
            200,
            json={
                "items": [{"type": "A", "name": "@", "address": "1.2.3.4", "ttl": 3600}]
            },
        )
    )

    result = runner.invoke(
        app,
        [
            "dns",
            "update",
            "--domain",
            domain,
            "--type",
            "A",
            "--name",
            "www",
            "--new-value",
            "2.2.2.2",
        ],
    )
    assert result.exit_code == 1
    assert "Error: No matching DNS record found" in (result.stdout + result.stderr)


@respx.mock
def test_update_dns_ambiguous() -> None:
    """Test updating fails when multiple matches are found and current_value is not specified."""
    domain = "example.com"
    respx.get(f"https://spaceship.dev/api/v1/dns/records/{domain}").mock(
        return_value=Response(
            200,
            json={
                "items": [
                    {"type": "A", "name": "@", "address": "1.1.1.1", "ttl": 3600},
                    {"type": "A", "name": "@", "address": "2.2.2.2", "ttl": 3600},
                ]
            },
        )
    )

    result = runner.invoke(
        app,
        [
            "dns",
            "update",
            "--domain",
            domain,
            "--type",
            "A",
            "--name",
            "@",
            "--new-ttl",
            "600",
        ],
    )
    assert result.exit_code == 1
    assert "Error: Multiple matching DNS records found" in (
        result.stdout + result.stderr
    )

    # Now specify --current-value to resolve ambiguity
    route_put = respx.put(f"https://spaceship.dev/api/v1/dns/records/{domain}").mock(
        return_value=Response(204)
    )
    result_resolved = runner.invoke(
        app,
        [
            "dns",
            "update",
            "--domain",
            domain,
            "--type",
            "A",
            "--name",
            "@",
            "--current-value",
            "1.1.1.1",
            "--new-ttl",
            "600",
        ],
    )
    assert result_resolved.exit_code == 0
    assert "Successfully updated DNS Record" in result_resolved.stdout
    assert route_put.called
