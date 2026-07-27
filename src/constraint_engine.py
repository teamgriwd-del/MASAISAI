"""
POTRAZ-rules constraint engine for MASAISAI.

Core safety architecture: rules always override the ML model. The ML
occupancy predictor (occupancy_model.py) never gets the final word on
whether a channel is opened -- it only ever supplies one input to a
decision that a hard-coded, auditable rules layer can veto. This mirrors
the incumbent-protection guarantee the FCC/Ofcom TV white space database
model already relies on (see proposal Section 5), implemented so it holds
regardless of what the ML layer predicts.

Decision order (see decide_access):
  1. Rules layer: is this channel in the protected/incumbent list, or is
     this node inside an exclusion zone? -> deny, unconditionally.
  2. Fail-safe: is sensing confidence for this reading below threshold
     (node degraded/offline)? -> deny, regardless of ML prediction.
  3. ML layer: is predicted occupancy probability for the next window
     above the grant threshold? -> deny.
  4. Otherwise -> grant, for a bounded time window, fully logged.

`rules` are loaded from data/znfap_rules_PLACEHOLDER.json -- explicitly
named and documented as an illustrative structure, NOT POTRAZ's real
channel-by-channel ZNFAP assignment table, which has not been published
to us in machine-readable form. See data/DATASET_STATEMENT.md.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

RULES_PATH = Path(__file__).resolve().parent.parent / "data" / "znfap_rules_PLACEHOLDER.json"

DEFAULT_CONFIDENCE_THRESHOLD = 0.6
# Deny (flag for review) if predicted occupancy prob exceeds this. Recalibrated 2026-07-27
# after occupancy_model.py moved from next-window forecasting to multi-node sensor fusion:
# re-probed the new model's own output distribution -- genuinely-idle windows score up to
# ~0.23, genuinely-occupied windows score down to ~0.85, a wide, clean gap with no overlap in
# this benchmark. 0.5 sits comfortably in that gap ("verify idle only if more likely idle than
# occupied") and needs no further tuning unless the underlying fusion model changes again.
DEFAULT_OCCUPANCY_GRANT_THRESHOLD = 0.5
DEFAULT_GRANT_WINDOW_MINUTES = 15


@dataclass
class Decision:
    node_id: str
    channel: str
    granted: bool
    reason: str
    ml_probability: float | None = None
    sensing_confidence: float | None = None
    expires_at: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "node_id": self.node_id,
            "channel": self.channel,
            "granted": self.granted,
            "reason": self.reason,
            "ml_probability": self.ml_probability,
            "sensing_confidence": self.sensing_confidence,
            "expires_at": self.expires_at,
        }


def load_rules(path: Path = RULES_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def decide_access(
    node_id: str,
    channel: str,
    ml_probability: float,
    sensing_confidence: float,
    rules: dict,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    occupancy_grant_threshold: float = DEFAULT_OCCUPANCY_GRANT_THRESHOLD,
    grant_window_minutes: int = DEFAULT_GRANT_WINDOW_MINUTES,
) -> Decision:
    # 1. Rules layer -- absolute veto, checked first, ML is never consulted
    # for a protected channel.
    if channel in rules.get("protected_channels", []):
        return Decision(node_id, channel, False, "DENIED: channel is on the protected/incumbent list",
                         sensing_confidence=sensing_confidence)

    if node_id in rules.get("excluded_nodes", []):
        return Decision(node_id, channel, False, "DENIED: node is within a hard exclusion zone",
                         sensing_confidence=sensing_confidence)

    # 2. Fail-safe -- default to deny if we can't trust the sensing data.
    if sensing_confidence < confidence_threshold:
        return Decision(node_id, channel, False,
                         f"DENIED: sensing confidence {sensing_confidence:.2f} below "
                         f"fail-safe threshold {confidence_threshold:.2f}",
                         ml_probability=ml_probability, sensing_confidence=sensing_confidence)

    # 3. ML layer -- only consulted once the channel has cleared the hard
    # rules and sensing is trustworthy.
    if ml_probability > occupancy_grant_threshold:
        return Decision(node_id, channel, False,
                         f"DENIED: predicted occupancy probability {ml_probability:.2f} exceeds "
                         f"grant threshold {occupancy_grant_threshold:.2f}",
                         ml_probability=ml_probability, sensing_confidence=sensing_confidence)

    # 4. Grant, bounded and logged.
    expires_at = (datetime.now(UTC) + timedelta(minutes=grant_window_minutes)).isoformat()
    return Decision(node_id, channel, True,
                     f"GRANTED: verified idle (p_occupied={ml_probability:.2f}), "
                     f"confidence {sensing_confidence:.2f}, window {grant_window_minutes} min",
                     ml_probability=ml_probability, sensing_confidence=sensing_confidence,
                     expires_at=expires_at)


if __name__ == "__main__":
    rules = load_rules()
    examples = [
        ("NODE1", "CH21", 0.10, 0.92),  # expect grant
        ("NODE1", "CH25", 0.05, 0.92),  # protected channel -> deny regardless
        ("NODE3", "CH30", 0.05, 0.40),  # low confidence -> fail-safe deny
        ("NODE2", "CH33", 0.80, 0.92),  # predicted occupied -> deny
    ]
    for node_id, channel, p, conf in examples:
        d = decide_access(node_id, channel, p, conf, rules)
        print(d.to_dict())
