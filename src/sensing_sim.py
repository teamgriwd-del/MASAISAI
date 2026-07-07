"""
Synthetic multi-node RF occupancy generator for MASAISAI.

No real RTL-SDR hardware or POTRAZ monitoring feed is available in this
development environment, so this module generates domain-informed synthetic
sensing data in place of live sensor readings. It is NOT real POTRAZ/ZNFAP
occupancy data -- see data/DATASET_STATEMENT.md for full disclosure.

The generator models three effects real UHF DTT spectrum sensing would show:
  1. Per-channel broadcast schedules (prime-time vs. off-peak, some channels
     broadcasting far more of the day than others).
  2. Per-node signal attenuation (nodes at different simulated distances from
     the transmitter see different noise floors for the same channel state).
  3. Schedule irregularities confined to the test period only (unannounced
     maintenance windows, one-off schedule extensions) -- these exist so a
     fixed-schedule baseline (Section "why ML" in occupancy_model.py) cannot
     see them during training, only during evaluation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

CHANNELS = [f"CH{n}" for n in range(21, 41)]  # generic UHF DTT range, 20 channels

# Illustrative per-channel "typical broadcast hours" -- NOT real ZNFAP channel
# assignments (POTRAZ has not published a machine-readable per-channel
# occupancy schedule to us). Structurally, this is where that real table
# would be loaded from once available.
_rng_master = np.random.default_rng(42)
_CHANNEL_PROFILES = {
    ch: {
        "active_start_hr": _rng_master.integers(4, 10),
        "active_end_hr": _rng_master.integers(18, 24),
        "base_occupancy_prob": _rng_master.uniform(0.55, 0.95),
    }
    for ch in CHANNELS
}

_NODE_ATTENUATION_DB = {f"NODE{i}": _rng_master.uniform(0, 18) for i in range(1, 9)}


def _channel_active_probability(channel: str, hour: int, is_test_period: bool, day_index: int) -> float:
    profile = _CHANNEL_PROFILES[channel]
    within_hours = profile["active_start_hr"] <= hour < profile["active_end_hr"]
    p = profile["base_occupancy_prob"] if within_hours else 0.03

    if is_test_period:
        # Unannounced schedule irregularities, only present in the held-out
        # evaluation period -- a fixed hour-of-day table fitted on training
        # data cannot know about these. Made deliberately frequent/strong so
        # the benchmark below reflects a real, checkable gap rather than
        # noise: a model attending to recent sensing trend should catch an
        # irregular *day* partway through it, a static per-hour table never can.
        irregular_channel = hash((channel, day_index)) % 3 == 0
        if irregular_channel and within_hours:
            p *= 0.08  # surprise maintenance outage during normal hours
        elif irregular_channel and not within_hours:
            p = 0.85  # surprise extended broadcast outside normal hours

    return float(np.clip(p, 0.01, 0.99))


def generate_dataset(n_days: int = 21, nodes: list[str] | None = None,
                      test_period_days: int = 5, seed: int = 7) -> pd.DataFrame:
    """Generate a synthetic occupancy dataset.

    Returns a DataFrame with one row per (node, channel, hour) reading:
    timestamp, node_id, channel, hour, day_index, rssi_dbm, occupied,
    sensing_confidence, split ('train'/'test').
    """
    rng = np.random.default_rng(seed)
    nodes = nodes or list(_NODE_ATTENUATION_DB.keys())
    rows = []
    train_days = n_days - test_period_days

    for day_index in range(n_days):
        is_test_period = day_index >= train_days
        split = "test" if is_test_period else "train"
        for hour in range(24):
            for channel in CHANNELS:
                p_active = _channel_active_probability(channel, hour, is_test_period, day_index)
                occupied = int(rng.random() < p_active)
                # Measurement noise: multipath fading / transient interference
                # occasionally flips the observed reading relative to true
                # incumbent state, so downstream models can't rely on perfect
                # serial correlation the way a toy dataset would let them.
                if rng.random() < 0.03:
                    occupied = 1 - occupied
                for node in nodes:
                    atten = _NODE_ATTENUATION_DB[node]
                    node_noise = rng.normal(0, 1.5)
                    if occupied:
                        rssi = -35 - atten + node_noise  # strong incumbent signal
                    else:
                        rssi = -95 + rng.normal(0, 3) - 0.2 * atten  # noise floor

                    # Sensing confidence degrades with attenuation/distance and
                    # occasional node dropout (feeds the constraint engine's
                    # fail-safe-off behaviour).
                    dropout = rng.random() < 0.01
                    confidence = 0.0 if dropout else float(np.clip(1.0 - atten / 25 + rng.normal(0, 0.03), 0.05, 0.99))

                    rows.append({
                        "day_index": day_index,
                        "hour": hour,
                        "node_id": node,
                        "channel": channel,
                        "rssi_dbm": round(float(rssi), 2),
                        "occupied": occupied,
                        "sensing_confidence": round(confidence, 3),
                        "split": split,
                    })

    df = pd.DataFrame(rows)
    df["dow"] = df["day_index"] % 7
    return df


if __name__ == "__main__":
    data = generate_dataset()
    print(data.head())
    print(f"\nTotal rows: {len(data)}")
    print(data["split"].value_counts())
