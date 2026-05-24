"""Filter JSON log records by IP address field membership or CIDR range."""

from __future__ import annotations

import ipaddress
from typing import Iterable, List, Optional, Union


class IPFilterError(Exception):
    """Raised when IPFilter is misconfigured."""


def _get_nested(record: dict, field: str):
    """Retrieve a possibly dot-separated nested field value."""
    parts = field.split(".")
    node = record
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


class IPFilter:
    """Keep or drop records whose IP field falls within given addresses or CIDRs.

    Parameters
    ----------
    field:
        Dot-separated path to the IP address field in the record.
    networks:
        List of IP address strings or CIDR notation strings to match against.
    invert:
        When True, drop records that match instead of keeping them.
    """

    def __init__(
        self,
        field: str,
        networks: List[str],
        *,
        invert: bool = False,
    ) -> None:
        if not field or not field.strip():
            raise IPFilterError("field must be a non-empty string")
        if not networks:
            raise IPFilterError("at least one network or address must be provided")
        self._field = field.strip()
        self._invert = invert
        self._networks: List[Union[ipaddress.IPv4Network, ipaddress.IPv6Network]] = []
        for raw in networks:
            try:
                self._networks.append(ipaddress.ip_network(raw, strict=False))
            except ValueError as exc:
                raise IPFilterError(f"invalid network or address {raw!r}: {exc}") from exc

    @property
    def field(self) -> str:
        return self._field

    @property
    def networks(self) -> List[Union[ipaddress.IPv4Network, ipaddress.IPv6Network]]:
        return list(self._networks)

    @property
    def invert(self) -> bool:
        return self._invert

    def _matches_networks(self, ip_str: str) -> bool:
        try:
            addr = ipaddress.ip_address(ip_str)
        except ValueError:
            return False
        return any(addr in net for net in self._networks)

    def keep(self, record: dict) -> bool:
        """Return True if *record* should be kept."""
        if not isinstance(record, dict):
            raise IPFilterError("record must be a dict")
        value = _get_nested(record, self._field)
        if value is None:
            return False
        matched = self._matches_networks(str(value))
        return not matched if self._invert else matched

    def filter_many(self, records: Iterable[dict]) -> Iterable[dict]:
        """Yield records that pass the IP filter."""
        for record in records:
            if self.keep(record):
                yield record
