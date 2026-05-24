"""Tests for IPFilter and its CLI."""

from __future__ import annotations

import json
import io

import pytest

from logslice.ip_filter import IPFilter, IPFilterError
from logslice.ip_filter_cli import build_ip_filter_parser, run_ip_filter_cli


# ---------------------------------------------------------------------------
# IPFilter unit tests
# ---------------------------------------------------------------------------

def test_empty_field_raises():
    with pytest.raises(IPFilterError, match="field"):
        IPFilter("", ["10.0.0.0/8"])


def test_blank_field_raises():
    with pytest.raises(IPFilterError, match="field"):
        IPFilter("   ", ["10.0.0.0/8"])


def test_no_networks_raises():
    with pytest.raises(IPFilterError, match="at least one"):
        IPFilter("ip", [])


def test_invalid_network_raises():
    with pytest.raises(IPFilterError, match="invalid network"):
        IPFilter("ip", ["not-an-ip"])


def test_field_property():
    f = IPFilter("client.ip", ["192.168.0.0/16"])
    assert f.field == "client.ip"


def test_invert_default_false():
    f = IPFilter("ip", ["10.0.0.1"])
    assert f.invert is False


def test_invert_stored():
    f = IPFilter("ip", ["10.0.0.1"], invert=True)
    assert f.invert is True


def test_networks_property_returns_copy():
    f = IPFilter("ip", ["10.0.0.0/8"])
    nets = f.networks
    assert len(nets) == 1
    nets.clear()
    assert len(f.networks) == 1  # original unaffected


def test_keep_matching_address():
    f = IPFilter("ip", ["192.168.1.0/24"])
    assert f.keep({"ip": "192.168.1.42"}) is True


def test_drop_non_matching_address():
    f = IPFilter("ip", ["192.168.1.0/24"])
    assert f.keep({"ip": "10.0.0.1"}) is False


def test_invert_drops_matching_address():
    f = IPFilter("ip", ["192.168.1.0/24"], invert=True)
    assert f.keep({"ip": "192.168.1.42"}) is False


def test_invert_keeps_non_matching_address():
    f = IPFilter("ip", ["192.168.1.0/24"], invert=True)
    assert f.keep({"ip": "10.0.0.1"}) is True


def test_missing_field_returns_false():
    f = IPFilter("ip", ["10.0.0.0/8"])
    assert f.keep({"host": "example.com"}) is False


def test_nested_field_resolved():
    f = IPFilter("meta.ip", ["172.16.0.0/12"])
    assert f.keep({"meta": {"ip": "172.16.5.10"}}) is True


def test_invalid_ip_value_returns_false():
    f = IPFilter("ip", ["10.0.0.0/8"])
    assert f.keep({"ip": "not-an-ip"}) is False


def test_non_dict_record_raises():
    f = IPFilter("ip", ["10.0.0.1"])
    with pytest.raises(IPFilterError):
        f.keep(["10.0.0.1"])  # type: ignore[arg-type]


def test_filter_many_yields_matching():
    f = IPFilter("ip", ["10.0.0.0/8"])
    records = [{"ip": "10.1.2.3"}, {"ip": "8.8.8.8"}, {"ip": "10.255.0.1"}]
    result = list(f.filter_many(records))
    assert result == [{"ip": "10.1.2.3"}, {"ip": "10.255.0.1"}]


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def _run(lines, extra_args=()):
    parser = build_ip_filter_parser()
    args = parser.parse_args(["--field", "ip", "--network", "10.0.0.0/8", *extra_args])
    stdin = io.StringIO("\n".join(lines) + "\n")
    stdout = io.StringIO()
    code = run_ip_filter_cli(args, stdin=stdin, stdout=stdout)
    return code, stdout.getvalue().splitlines()


def test_cli_keeps_matching_records():
    lines = [json.dumps({"ip": "10.1.2.3"}), json.dumps({"ip": "8.8.8.8"})]
    code, out = _run(lines)
    assert code == 0
    assert len(out) == 1
    assert json.loads(out[0])["ip"] == "10.1.2.3"


def test_cli_invert_drops_matching_records():
    lines = [json.dumps({"ip": "10.1.2.3"}), json.dumps({"ip": "8.8.8.8"})]
    code, out = _run(lines, extra_args=["--invert"])
    assert code == 0
    assert len(out) == 1
    assert json.loads(out[0])["ip"] == "8.8.8.8"


def test_cli_invalid_network_exits_2():
    parser = build_ip_filter_parser()
    args = parser.parse_args(["--field", "ip", "--network", "bad-cidr"])
    stdin = io.StringIO(json.dumps({"ip": "10.0.0.1"}) + "\n")
    stdout = io.StringIO()
    code = run_ip_filter_cli(args, stdin=stdin, stdout=stdout)
    assert code == 2


def test_cli_skips_invalid_json_lines():
    lines = ["not json", json.dumps({"ip": "10.0.0.1"})]
    code, out = _run(lines)
    assert code == 0
    assert len(out) == 1
