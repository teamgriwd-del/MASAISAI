"""
MASAISAI Phase-1 ingestion service.

Subscribes to masaisai/sensing/# on the local Mosquitto broker, stores every
raw reading in MySQL, fuses each channel's currently-known per-node readings
through the trained occupancy model + POTRAZ-rules constraint engine, and
stores the resulting per-channel verdict (full audit trail).

Reworked 27 Jul 2026 (same night as occupancy_model.py's forecasting->fusion
pivot -- see src/occupancy_model.py's module docstring and
Pitching and Presenting/04_ANTICIPATED_QUESTIONS.md section 1) to match: this
service no longer scores one node's reading in isolation against a next-window
forecast. It keeps a last-known-reading cache per (channel, node) -- a
standard asynchronous multi-sensor fusion pattern -- and on every incoming
reading recomputes that channel's fused verdict from every node currently
reporting on it, exactly mirroring src/occupancy_model.build_fusion_frame's
feature set. Same model class, same rules engine (constraint_engine.
decide_access), same "AI predicts, rules decide" architecture as the
simulated prototype -- only the data source changed from sensing_sim.py to
real MQTT readings, exactly as promised in the proposal (Section 2.2 /
DATASET_STATEMENT "What changes for the real pilot").

Runs under systemd (masaisai-ingest.service), restarts on failure/reboot.
"""

from __future__ import annotations

import json
import logging
import os
import statistics
import sys
from collections import defaultdict, deque
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import paho.mqtt.client as mqtt
import pymysql

# src/ modules from the MASAISAI repo (deployed to /opt/masaisai/src)
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from constraint_engine import decide_access, load_rules  # noqa: E402
from occupancy_model import (  # noqa: E402
    ENERGY_DETECTION_THRESHOLD_DBM,
    FEATURE_COLUMNS,
    build_fusion_frame,
    train_model,
)
from sensing_sim import generate_dataset  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("masaisai-ingest")

# ---------- Config from environment (/opt/masaisai/.env via systemd) ----------
MQTT_HOST = os.environ.get("MQTT_BROKER_HOST", "127.0.0.1")
MQTT_PORT = int(os.environ.get("MQTT_BROKER_PORT", "1883"))
MQTT_USER = os.environ.get("MQTT_USER", "masaisai_node")
MQTT_PASS = os.environ.get("MQTT_PASS", "")
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "masaisai_app")
DB_PASS = os.environ.get("DB_PASS", "")
DB_NAME = os.environ.get("DB_NAME", "masaisai")

# ---------- Train the model once at startup (seconds, per proposal 3.2) ----------
log.info("Training occupancy model on synthetic bootstrap data...")
_raw = generate_dataset()
_fused = build_fusion_frame(_raw)
_train_df = _fused[_fused["split"] == "train"]
MODEL = train_model(_train_df)
_CHANNELS = sorted(_raw["channel"].unique().tolist())
_CHANNEL_CODE = {ch: i for i, ch in enumerate(_CHANNELS)}
RULES = load_rules()
log.info("Model trained. %d channels in code map.", len(_CHANNELS))

# Last-known reading per (channel -> {node_id: {rssi, confidence}}) -- readings
# arrive asynchronously over MQTT, so fusion here means "every node's most
# recently reported value for this channel," not a synchronized time window.
_latest_readings: dict[str, dict[str, dict]] = defaultdict(dict)
# Per-channel history of the fused verdict (for rolling_occupancy_rate) -- the
# live substitute for build_fusion_frame's ground-truth history, since a real
# deployment has no ground truth, only its own past verdicts.
_channel_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=3))


def _db():
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS,
        database=DB_NAME, autocommit=True, charset="utf8mb4",
    )


def fuse_channel(channel: str) -> tuple[float, float]:
    """Recomputes this channel's fused verdict from every node's latest known
    reading, using the exact feature set build_fusion_frame trains on.
    Returns (ml_probability, max_confidence) -- max, not mean, because one
    reliable node should be enough to trust a reading even if others
    currently reporting on this channel are degraded."""
    readings = list(_latest_readings[channel].values())
    rssi_vals = [r["rssi"] for r in readings]
    conf_vals = [r["confidence"] for r in readings]
    naive_flags = [1 if r["rssi"] > ENERGY_DETECTION_THRESHOLD_DBM else 0 for r in readings]
    conf_sum = sum(conf_vals)
    weighted_vote = (
        sum(f * c for f, c in zip(naive_flags, conf_vals)) / conf_sum if conf_sum else 0.5
    )
    hist = _channel_history[channel]
    now = datetime.now(UTC)
    row = pd.DataFrame([{
        "hour": now.hour,
        "dow": now.weekday(),
        "channel_code": _CHANNEL_CODE.get(channel, 0),
        "mean_rssi_dbm": statistics.fmean(rssi_vals),
        "min_rssi_dbm": min(rssi_vals),
        "max_rssi_dbm": max(rssi_vals),
        "std_rssi_dbm": statistics.pstdev(rssi_vals) if len(rssi_vals) > 1 else 0.0,
        "mean_confidence": statistics.fmean(conf_vals),
        "min_confidence": min(conf_vals),
        "max_confidence": max(conf_vals),
        "naive_vote_frac": statistics.fmean(naive_flags),
        "confidence_weighted_vote": weighted_vote,
        "rolling_occupancy_rate": (sum(hist) / len(hist)) if hist else 0.5,
    }])
    prob = float(MODEL.predict_proba(row[FEATURE_COLUMNS])[:, 1][0])
    return prob, max(conf_vals)


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        node_id = str(data["node_id"])
        channel = f"CH{int(data['channel'])}" if not str(data["channel"]).startswith("CH") else str(data["channel"])
        rssi = float(data["rssi_dbm"])
        occupied = int(data["occupied"])
        conf = float(data["sensing_confidence"])
        now = datetime.now(UTC).replace(tzinfo=None)

        _latest_readings[channel][node_id] = {"rssi": rssi, "confidence": conf}
        prob, fused_confidence = fuse_channel(channel)
        decision = decide_access("FUSED", channel, prob, fused_confidence, RULES)
        _channel_history[channel].append(int(decision.granted))

        with _db() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO sensing_readings (node_id, channel, timestamp, rssi_dbm, occupied, sensing_confidence)"
                " VALUES (%s,%s,%s,%s,%s,%s)",
                (node_id, channel, now, rssi, occupied, conf),
            )
            expires = decision.expires_at
            if expires:
                expires = datetime.fromisoformat(expires).replace(tzinfo=None)
            cur.execute(
                "INSERT INTO access_decisions (node_id, channel, timestamp, granted, reason,"
                " ml_probability, sensing_confidence, expires_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (decision.node_id, channel, now, int(decision.granted), decision.reason,
                 decision.ml_probability, decision.sensing_confidence, expires),
            )
        log.info("%s %s rssi=%.1f conf=%.2f -> fused p=%.2f (n=%d nodes) -> %s",
                 node_id, channel, rssi, conf, prob, len(_latest_readings[channel]),
                 "VERIFIED IDLE" if decision.granted else "FLAGGED")
    except Exception:
        log.exception("Failed to process message on %s", msg.topic)


def on_connect(client, userdata, flags, reason_code, properties=None):
    log.info("Connected to broker (rc=%s); subscribing masaisai/sensing/#", reason_code)
    client.subscribe("masaisai/sensing/#", qos=0)


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
    client.loop_forever(retry_first_connection=True)


if __name__ == "__main__":
    main()
