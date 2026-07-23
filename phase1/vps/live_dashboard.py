"""
MASAISAI Phase-1 LIVE dashboard -- reads real MQTT-ingested readings and
constraint-engine decisions from MySQL (fed by ingest_service.py), instead
of the synthetic in-process pipeline the prototype dashboard used.

Run under systemd (masaisai-dashboard.service) on port 8501.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

import pandas as pd
import pymysql
import streamlit as st

DB = dict(
    host=os.environ.get("DB_HOST", "127.0.0.1"),
    port=int(os.environ.get("DB_PORT", "3306")),
    user=os.environ.get("DB_USER", "masaisai_app"),
    password=os.environ.get("DB_PASS", ""),
    database=os.environ.get("DB_NAME", "masaisai"),
    charset="utf8mb4",
)

st.set_page_config(page_title="MASAISAI -- Live Spectrum Access Console", layout="wide")
st.title("MASAISAI -- Live Spectrum Access Console (Phase 1)")
st.caption(
    "LIVE data: readings arrive over MQTT from sensing nodes (Wokwi-simulated "
    "ESP32 hardware), are scored by the ML occupancy model, and pass through the "
    "POTRAZ-rules constraint engine. The rules layer always has final veto."
)

REFRESH_SECONDS = 5
st.markdown(
    f"<meta http-equiv='refresh' content='{REFRESH_SECONDS}'>",
    unsafe_allow_html=True,
)


def q(sql: str, params=None) -> pd.DataFrame:
    conn = pymysql.connect(**DB)
    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()


readings = q(
    "SELECT * FROM sensing_readings ORDER BY id DESC LIMIT 500"
)
decisions = q(
    "SELECT * FROM access_decisions ORDER BY id DESC LIMIT 500"
)

if readings.empty:
    st.info("Waiting for the first sensing reading... start the Wokwi node simulation.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Sensing nodes (live)", readings["node_id"].nunique())
col2.metric("Channels monitored", readings["channel"].nunique())
col3.metric("Readings stored", len(readings))
last_ts = pd.to_datetime(readings["timestamp"].iloc[0])
age = (datetime.utcnow() - last_ts).total_seconds()
col4.metric("Last reading", f"{age:.0f}s ago")

st.subheader("Latest reading per node/channel")
latest = readings.sort_values("id").groupby(["node_id", "channel"]).tail(1)
latest_dec = decisions.sort_values("id").groupby(["node_id", "channel"]).tail(1)
merged = latest.merge(
    latest_dec[["node_id", "channel", "granted", "reason", "ml_probability"]],
    on=["node_id", "channel"], how="left",
)
merged["decision"] = merged["granted"].map({1: "GRANT", 0: "DENY"})
st.dataframe(
    merged[["node_id", "channel", "timestamp", "rssi_dbm", "occupied",
            "sensing_confidence", "ml_probability", "decision", "reason"]],
    width="stretch",
)

grants = int((decisions["granted"] == 1).sum())
denies = int((decisions["granted"] == 0).sum())
st.subheader(f"Decisions (last 500): {grants} granted / {denies} denied")

st.subheader("RSSI over time (live incumbent detection)")
chart_df = readings.sort_values("id").copy()
chart_df["timestamp"] = pd.to_datetime(chart_df["timestamp"])
for (node, ch), g in chart_df.groupby(["node_id", "channel"]):
    st.line_chart(g.set_index("timestamp")["rssi_dbm"], height=200)
    st.caption(f"{node} / {ch} -- energy above -75 dBm = incumbent broadcaster active")

with st.expander("Full audit log (every decision, fully explained)"):
    st.dataframe(
        decisions[["timestamp", "node_id", "channel", "granted", "reason",
                   "ml_probability", "sensing_confidence", "expires_at"]],
        width="stretch",
    )
