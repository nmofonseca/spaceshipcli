"""
Helpers for Spaceship DNS resource-record field shapes.

The Spaceship API uses type-specific value fields (e.g. ``cname`` for CNAME,
``address`` for A/AAAA, ``exchange`` for MX). See:
https://docs.spaceship.dev/ and the DNS records OpenAPI schema.
"""

from __future__ import annotations

from typing import Any, Optional

# Primary scalar field mapped from CLI ``--value`` per record type.
PRIMARY_VALUE_FIELD: dict[str, str] = {
    "A": "address",
    "AAAA": "address",
    "ALIAS": "aliasName",
    "CAA": "value",
    "CNAME": "cname",
    "HTTPS": "targetName",
    "MX": "exchange",
    "NS": "nameserver",
    "PTR": "pointer",
    "SRV": "target",
    "SVCB": "targetName",
    "TLSA": "associationData",
    "TXT": "value",
}

# Type-specific fields included on create/update/delete payloads.
TYPE_SPECIFIC_FIELDS: dict[str, tuple[str, ...]] = {
    "A": ("address",),
    "AAAA": ("address",),
    "ALIAS": ("aliasName",),
    "CAA": ("flag", "tag", "value"),
    "CNAME": ("cname",),
    "HTTPS": ("port", "scheme", "svcPriority", "targetName", "svcParams"),
    "MX": ("exchange", "preference"),
    "NS": ("nameserver",),
    "PTR": ("pointer",),
    "SRV": ("service", "protocol", "priority", "weight", "port", "target"),
    "SVCB": ("port", "scheme", "svcPriority", "targetName", "svcParams"),
    "TLSA": (
        "port",
        "protocol",
        "usage",
        "selector",
        "matching",
        "associationData",
    ),
    "TXT": ("value",),
}

# Fields that must not be sent on PUT create/update payloads.
_READ_ONLY_FIELDS = frozenset({"group"})


def primary_value_field(record_type: str) -> str:
    """Return the API field name for a record type's primary value."""
    return PRIMARY_VALUE_FIELD.get(record_type.upper(), "value")


def get_record_value(record: dict[str, Any]) -> Any:
    """
    Extract a comparable/display value from a DNS record.

    Prefers the type-specific primary field, then common fallbacks.
    """
    record_type = str(record.get("type", "")).upper()
    field = primary_value_field(record_type)
    if field in record and record[field] is not None:
        return record[field]

    for key in (
        "address",
        "cname",
        "exchange",
        "nameserver",
        "pointer",
        "aliasName",
        "target",
        "targetName",
        "associationData",
        "value",
    ):
        if key in record and record[key] is not None:
            return record[key]
    return None


def build_record_from_cli(
    record_type: str,
    name: str,
    value: str,
    ttl: Optional[int] = None,
    preference: Optional[int] = None,
) -> dict[str, Any]:
    """
    Build an API-shaped create/update record from simple CLI flags.

    Maps ``--value`` onto the type-specific field expected by Spaceship.
    """
    rtype = record_type.upper()
    field = primary_value_field(rtype)
    record: dict[str, Any] = {"type": rtype, "name": name, field: value}
    if ttl is not None:
        record["ttl"] = ttl
    if rtype == "MX":
        record["preference"] = 10 if preference is None else preference
    elif preference is not None:
        record["preference"] = preference
    return record


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize a user/file-supplied record to Spaceship's type-specific fields.

    If a generic ``value`` is present but the type-specific primary field is
    missing, remap ``value`` to that field (except for TXT/CAA which use
    ``value`` natively).
    """
    normalized = dict(record)
    rtype = str(normalized.get("type", "")).upper()
    if rtype:
        normalized["type"] = rtype

    primary = primary_value_field(rtype)
    if (
        primary != "value"
        and "value" in normalized
        and primary not in normalized
        and normalized.get("value") is not None
    ):
        normalized[primary] = normalized.pop("value")

    return normalized


def strip_read_only_fields(record: dict[str, Any]) -> dict[str, Any]:
    """Remove read-only fields (e.g. ``group``) before PUT."""
    return {k: v for k, v in record.items() if k not in _READ_ONLY_FIELDS}


def clean_record_for_put(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize and strip read-only fields for a PUT create/update item."""
    return strip_read_only_fields(normalize_record(record))


def clean_record_for_delete(record: dict[str, Any]) -> dict[str, Any]:
    """
    Build a DELETE payload item with type, name, and type-specific fields.
    """
    normalized = normalize_record(record)
    rtype = str(normalized.get("type", "")).upper()
    cleaned: dict[str, Any] = {
        "type": rtype,
        "name": normalized["name"],
    }
    for field in TYPE_SPECIFIC_FIELDS.get(rtype, ()):
        if field in normalized and normalized[field] is not None:
            cleaned[field] = normalized[field]
    return cleaned


def records_match(
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    require_value: bool = True,
) -> bool:
    """
    Return True when two records refer to the same DNS entry.

    Matching is by type + name, and by primary value when
    ``require_value`` is True and the right-hand record has a value.
    """
    if left.get("type") != right.get("type") or left.get("name") != right.get("name"):
        return False

    right_val = get_record_value(right)
    if not require_value or right_val is None:
        return True

    left_val = get_record_value(left)
    if left_val != right_val:
        return False

    # MX preference distinguishes otherwise identical exchanges.
    if str(left.get("type", "")).upper() == "MX":
        left_pref = left.get("preference")
        right_pref = right.get("preference")
        if right_pref is not None and left_pref is not None:
            return left_pref == right_pref
    return True
