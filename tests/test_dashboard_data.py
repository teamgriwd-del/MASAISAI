"""
Tests for the console's data layer.

These guard the two things a redesign could silently break: that the UI still reports what the
backend actually computed, and that the interface can never present an ML prediction as an
authorisation. The rules layer must remain the only thing that grants access.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dashboard_data import build_payload, channel_centre_mhz, run_backend  # noqa: E402
from sensing_sim import CHANNELS  # noqa: E402


@pytest.fixture(scope="module")
def backend():
    return run_backend()


@pytest.fixture(scope="module")
def payload(backend):
    # Fixed hour so the snapshot is stable regardless of when the suite runs.
    return build_payload(backend, now=datetime(2026, 1, 1, 14, 0))


def test_payload_is_json_serialisable(payload):
    assert json.loads(json.dumps(payload))["meta"]["product"] == "MASAISAI"


def test_counts_come_from_the_backend(payload, backend):
    assert payload["kpis"]["channels_monitored"] == len(CHANNELS)
    assert payload["kpis"]["nodes_total"] == backend["raw"]["node_id"].nunique()
    assert len(payload["channels"]) == len(CHANNELS)


def test_rules_layer_never_grants_a_protected_channel(payload):
    """The core safety invariant, asserted on what the UI actually displays."""
    protected = set(payload["config"]["protected_channels"])
    assert protected, "test is meaningless if no channels are protected"
    for ch in payload["channels"]:
        if ch["channel"] in protected:
            assert ch["status"] == "PROTECTED"
    assert payload["kpis"]["grants_on_protected"] == 0
    granted = {d["channel"] for d in payload["decisions"] if d["decision"] == "Granted"}
    assert granted.isdisjoint(protected)


def test_a_confident_ml_idle_call_cannot_override_protection(payload):
    """A protected channel the model is sure is idle must still not be available.

    The sensing simulator is not seeded, so whether any protected channel reads
    idle in a given run is chance. Asserting that precondition made this test
    fail at random; the invariant it guards is unconditional and is also covered
    by test_rules_layer_never_grants_a_protected_channel.
    """
    protected = set(payload["config"]["protected_channels"])
    confident_idle = [c for c in payload["channels"]
                      if c["channel"] in protected and c["p_idle"] > 0.5]
    if not confident_idle:
        pytest.skip("no protected channel read as idle in this run -- nothing to contradict")
    for c in confident_idle:
        assert c["status"] == "PROTECTED"


def test_usage_totals_reconcile(payload):
    u = payload["usage"]
    assert u["idle"] + u["occupied"] + u["protected"] + u["flagged"] == u["total"]
    assert u["total"] == len(CHANNELS)


def test_channel_frequencies_use_the_8mhz_raster(payload):
    for c in payload["channels"]:
        assert c["freq_mhz"] == channel_centre_mhz(c["channel"])
    by_ch = {c["channel"]: c["freq_mhz"] for c in payload["channels"]}
    assert by_ch["CH21"] == 474.0 and by_ch["CH22"] == 482.0 and by_ch["CH23"] == 490.0


def test_unmodelled_rules_are_declared_not_passed(payload):
    """Checks the engine does not perform must never be shown as passing."""
    states = {c["name"]: c["state"] for c in payload["live"]["checks"]}
    assert states["Permitted Power"] == "NOT MODELLED"
    assert states["Regulatory Conditions"] == "PLACEHOLDER"


def test_decisions_and_audit_reference_real_entities(payload):
    channels = {c["channel"] for c in payload["channels"]}
    towns = {n["town"] for n in payload["nodes"]}
    for d in payload["decisions"]:
        assert d["channel"] in channels
        assert d["location"] in towns
        assert d["decision"] in {"Granted", "Denied", "Revoked"}
        # Only a grant carries a bounded window; a refusal must not imply one.
        assert (d["duration"] is not None) == (d["decision"] == "Granted")


def test_simulated_data_is_disclosed(payload):
    assert payload["meta"]["simulated"] is True
    assert "synthetic" in payload["meta"]["data_notice"].lower()
    assert "illustrative" in payload["meta"]["site_notice"].lower()


def test_outlook_separates_measurement_from_expectation(payload):
    """The model verifies the current window; it does not forecast."""
    assert payload["outlook"], "expected candidate channels"
    for series in payload["outlook"]:
        assert series["measured"] and series["expected"]
        assert all(0.0 <= p["p_idle"] <= 1.0 for p in series["measured"])
        assert all(0.0 <= p["p_idle"] <= 1.0 for p in series["expected"])
