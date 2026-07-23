"""
MASAISAI Phase-1 ingestion service.

Subscribes to masaisai/sensing/# on the local Mosquitto broker, stores every
reading in MySQL, runs the trained occupancy model + POTRAZ-rules constraint
engine on it, and stores the resulting access decision (full audit trail).

This is the live version of the pipeline the simulated prototype proved:
same model (occupancy_model.train_model), same rules engine
(constraint_engine.decide_access) -- only the data source changed from
sensing_sim.py to real MQTT readings, exactly as promised in the proposal
(Section 2.2 / DATASET_STATEMENT "What changes for the real pilot").

Runs under systemd (masaisai-ingest.service), restarts on failure/reboot.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import paho.mqtt.client as mqtt
import pymysql

# src/ modules from the MASAISAI repo (deployed to /opt/masaisai/src)
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from constraint_engine import decide_access, load_rules  # noqa: E402
from occupancy_model import FEATURE_COLUMNS, add_features, train_model  # noqa: E402
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
_featured = add_features(_raw)
_train_df = _featured[_featured["split"] == "train"]
MODEL = train_model(_train_df)
_CHANNELS = sorted(_raw["channel"].unique().tolist())
_CHANNEL_CODE = {ch: i for i, ch in enumerate(_CHANNELS)}
_NODES = sorted(_raw["node_id"].unique().tolist())
_NODE_CODE = {n: i for i, n in enumerate(_NODES)}
RULES = load_rules()
log.info("Model trained. %d channels, %d nodes in code maps.", len(_CHANNELS), len(_NODES))

# Per (node, channel) history of previous occupied flags (for rolling rate)
_history: dict[tuple, deque] = defaultdict(lambda: deque(maxlen=3))


def _db():
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS,
        database=DB_NAME, autocommit=True, charset="utf8mb4",
    )


def ml_probability(node_id: str, channel: str, rssi: float, occupied: int) -> float:
    """Score next-window occupancy with the same features used in training."""
    hist = _history[(node_id, channel)]
    rolling = (sum(hist) / len(hist)) if hist else 0.5
    nxt = datetime.now(UTC) + timedelta(minutes=15)
    row = pd.DataFrame([{
        "next_hour": nxt.hour,
        "next_dow": nxt.weekday(),
        "rssi_dbm": rssi,
        "occupied": occupied,
        "rolling_occupancy_rate": rolling,
        "channel_code": _CHANNEL_CODE.get(channel, 0),
        "node_code": _NODE_CODE.get(node_id, 0),
    }])
    return float(MODEL.predict_proba(row[FEATURE_COLUMNS])[:, 1][0])


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        node_id = str(data["node_id"])
        channel = f"CH{int(data['channel'])}" if not str(data["channel"]).startswith("CH") else str(data["channel"])
        rssi = float(data["rssi_dbm"])
        occupied = int(data["occupied"])
        conf = float(data["sensing_confidence"])
        now = datetime.now(UTC).replace(tzinfo=None)

        prob = ml_probability(node_id, channel, rssi, occupied)
        decision = decide_access(node_id, channel, prob, conf, RULES)
        _history[(node_id, channel)].append(occupied)

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
                (node_id, channel, now, int(decision.granted), decision.reason,
                 decision.ml_probability, decision.sensing_confidence, expires),
            )
        log.info("%s %s rssi=%.1f occ=%d conf=%.2f p=%.2f -> %s",
                 node_id, channel, rssi, occupied, conf, prob,
                 "GRANT" if decision.granted else "DENY")
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
