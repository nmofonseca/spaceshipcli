"""
Unit tests for Spaceship DNS record field helpers.
"""

from spaceship_cli.dns_records import (
    build_record_from_cli,
    clean_record_for_delete,
    clean_record_for_put,
    get_record_value,
    normalize_record,
    primary_value_field,
    records_match,
)


def test_primary_value_field_mapping() -> None:
    assert primary_value_field("A") == "address"
    assert primary_value_field("AAAA") == "address"
    assert primary_value_field("CNAME") == "cname"
    assert primary_value_field("TXT") == "value"
    assert primary_value_field("MX") == "exchange"
    assert primary_value_field("NS") == "nameserver"
    assert primary_value_field("PTR") == "pointer"
    assert primary_value_field("ALIAS") == "aliasName"
    assert primary_value_field("SRV") == "target"


def test_build_record_from_cli_simple_types() -> None:
    assert build_record_from_cli("A", "@", "1.2.3.4", ttl=300) == {
        "type": "A",
        "name": "@",
        "address": "1.2.3.4",
        "ttl": 300,
    }
    assert build_record_from_cli("AAAA", "www", "2001:db8::1", ttl=300) == {
        "type": "AAAA",
        "name": "www",
        "address": "2001:db8::1",
        "ttl": 300,
    }
    assert build_record_from_cli("CNAME", "www", "example.com", ttl=300) == {
        "type": "CNAME",
        "name": "www",
        "cname": "example.com",
        "ttl": 300,
    }
    assert build_record_from_cli("TXT", "@", "v=spf1 -all", ttl=300) == {
        "type": "TXT",
        "name": "@",
        "value": "v=spf1 -all",
        "ttl": 300,
    }
    assert build_record_from_cli("NS", "@", "ns1.example.com", ttl=300) == {
        "type": "NS",
        "name": "@",
        "nameserver": "ns1.example.com",
        "ttl": 300,
    }
    assert build_record_from_cli("MX", "@", "mail.example.com", ttl=300) == {
        "type": "MX",
        "name": "@",
        "exchange": "mail.example.com",
        "ttl": 300,
        "preference": 10,
    }
    assert build_record_from_cli(
        "MX", "@", "mail.example.com", ttl=300, preference=20
    ) == {
        "type": "MX",
        "name": "@",
        "exchange": "mail.example.com",
        "ttl": 300,
        "preference": 20,
    }


def test_normalize_record_remaps_generic_value() -> None:
    assert normalize_record(
        {"type": "cname", "name": "www", "value": "example.com", "ttl": 300}
    ) == {
        "type": "CNAME",
        "name": "www",
        "cname": "example.com",
        "ttl": 300,
    }
    # TXT keeps value
    assert normalize_record(
        {"type": "TXT", "name": "@", "value": "hello", "ttl": 300}
    ) == {
        "type": "TXT",
        "name": "@",
        "value": "hello",
        "ttl": 300,
    }


def test_clean_record_for_put_strips_group() -> None:
    record = {
        "type": "CNAME",
        "name": "www",
        "cname": "example.com",
        "ttl": 300,
        "group": {"type": "custom"},
    }
    assert clean_record_for_put(record) == {
        "type": "CNAME",
        "name": "www",
        "cname": "example.com",
        "ttl": 300,
    }


def test_clean_record_for_delete_keeps_type_fields() -> None:
    assert clean_record_for_delete(
        {
            "type": "CNAME",
            "name": "www",
            "cname": "example.com",
            "ttl": 300,
            "group": {"type": "custom"},
        }
    ) == {
        "type": "CNAME",
        "name": "www",
        "cname": "example.com",
    }
    assert clean_record_for_delete(
        {
            "type": "MX",
            "name": "@",
            "exchange": "mail.example.com",
            "preference": 10,
            "ttl": 300,
        }
    ) == {
        "type": "MX",
        "name": "@",
        "exchange": "mail.example.com",
        "preference": 10,
    }


def test_get_record_value_and_match() -> None:
    cname = {"type": "CNAME", "name": "www", "cname": "example.com"}
    assert get_record_value(cname) == "example.com"
    assert records_match(
        cname,
        {"type": "CNAME", "name": "www", "cname": "example.com"},
        require_value=True,
    )
    assert not records_match(
        cname,
        {"type": "CNAME", "name": "www", "cname": "other.com"},
        require_value=True,
    )
    assert records_match(
        cname,
        {"type": "CNAME", "name": "www"},
        require_value=False,
    )
