import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from constraint_engine import decide_access  # noqa: E402

RULES = {
    "protected_channels": ["CH25", "CH26"],
    "excluded_nodes": ["NODE_EXCLUDED"],
}


def test_protected_channel_always_denied_even_with_confident_idle_prediction():
    """A protected channel must be denied no matter how confident the ML
    model is that it's idle -- rules layer has absolute veto over ML."""
    decision = decide_access("NODE1", "CH25", ml_probability=0.0, sensing_confidence=0.99, rules=RULES)
    assert decision.granted is False
    assert "protected" in decision.reason.lower()


def test_excluded_node_always_denied():
    decision = decide_access("NODE_EXCLUDED", "CH21", ml_probability=0.0, sensing_confidence=0.99, rules=RULES)
    assert decision.granted is False
    assert "exclusion" in decision.reason.lower()


def test_low_sensing_confidence_triggers_fail_safe_deny():
    """Even on an unprotected channel with a low occupancy prediction, low
    sensing confidence must default to deny (fail-safe-off)."""
    decision = decide_access("NODE1", "CH21", ml_probability=0.05, sensing_confidence=0.2, rules=RULES)
    assert decision.granted is False
    assert "confidence" in decision.reason.lower()


def test_high_predicted_occupancy_denied():
    decision = decide_access("NODE1", "CH21", ml_probability=0.9, sensing_confidence=0.95, rules=RULES)
    assert decision.granted is False
    assert "occupancy" in decision.reason.lower()


def test_grant_when_unprotected_confident_and_predicted_idle():
    decision = decide_access("NODE1", "CH21", ml_probability=0.05, sensing_confidence=0.95, rules=RULES)
    assert decision.granted is True
    assert decision.expires_at is not None


def test_decision_is_fully_auditable():
    decision = decide_access("NODE1", "CH21", ml_probability=0.05, sensing_confidence=0.95, rules=RULES)
    d = decision.to_dict()
    for key in ("timestamp", "node_id", "channel", "granted", "reason", "ml_probability", "sensing_confidence"):
        assert key in d
