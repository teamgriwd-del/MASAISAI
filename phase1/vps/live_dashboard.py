"""
MASAISAI Phase-1 LIVE dashboard -- reads real MQTT-ingested readings and
constraint-engine decisions from MySQL (fed by ingest_service.py), instead
of the synthetic in-process pipeline the prototype dashboard used.

Reworked 27 Jul 2026 (same night as ingest_service.py's forecasting->fusion pivot): access
decisions are now per-CHANNEL fused verdicts (ingest_service.py stores them with
node_id="FUSED"), not per (node, channel) anymore -- one node's own reading no longer gets
its own independent decision, since the whole point of fusion is combining every node
currently reporting on a channel into one verdict. Sensing readings are still logged per
real node (unchanged) for full dataset transparency; only decisions moved to channel
granularity.

Run under systemd (masaisai-dashboard.service) on port 8501.
"""

from __future__ import annotations

import os
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import pymysql
import streamlit as st
from streamlit_autorefresh import st_autorefresh

DB = dict(
    host=os.environ.get("DB_HOST", "127.0.0.1"),
    port=int(os.environ.get("DB_PORT", "3306")),
    user=os.environ.get("DB_USER", "masaisai_app"),
    password=os.environ.get("DB_PASS", ""),
    database=os.environ.get("DB_NAME", "masaisai"),
    charset="utf8mb4",
)

REFRESH_SECONDS = 5

# ---------- Palette (dark console theme; matches .streamlit/config.toml) ----------
SURFACE = "#1a1a19"
PAGE = "#0d0d0d"
INK_PRIMARY = "#ffffff"
INK_SECONDARY = "#c3c2b7"
INK_MUTED = "#898781"
GRID = "#2c2c2a"
BORDER = "rgba(255,255,255,0.10)"
GOOD = "#0ca30c"
CRITICAL = "#d03b3b"

# Fixed categorical order (never cycled) - one hue per channel slot, indexed by
# each channel's position in the firmware's scan list (see main.cpp CHANNELS[]).
CHANNEL_ORDER = [21, 23, 27, 31, 36, 40]
CATEGORICAL = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300"]


def channel_color(channel: str) -> str:
    try:
        n = int(str(channel).replace("CH", ""))
        idx = CHANNEL_ORDER.index(n)
    except ValueError:
        idx = 0
    return CATEGORICAL[idx % len(CATEGORICAL)]


# Standard 8 MHz-spaced UHF DTT channel plan, CH21 = 470 MHz (matches the
# CH21-CH40 range src/sensing_sim.py trains the occupancy model on).
def channel_to_freq_mhz(channel: str) -> float:
    try:
        n = int(str(channel).replace("CH", ""))
    except ValueError:
        return float("nan")
    return 470.0 + (n - 21) * 8.0


# Signal-strength tiers for display only (separate from the -75 dBm
# occupancy-decision threshold used by the constraint engine).
def rssi_quality(rssi: float) -> str:
    if rssi >= -50:
        return "Excellent"
    if rssi >= -65:
        return "Good"
    if rssi >= -75:
        return "Fair"
    if rssi >= -90:
        return "Poor"
    return "Very poor"


QUALITY_BARS = {
    "Excellent": "▰▰▰▰▰",
    "Good": "▰▰▰▰▱",
    "Fair": "▰▰▰▱▱",
    "Poor": "▰▰▱▱▱",
    "Very poor": "▰▱▱▱▱",
}


def q(sql: str, params=None) -> pd.DataFrame:
    conn = pymysql.connect(**DB)
    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()


st.set_page_config(
    page_title="MASAISAI -- Live Spectrum Idle-Verification Console",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    f"""
    <style>
    html, body, [class*="css"] {{
        font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    .block-container {{ padding-top: 1.6rem; max-width: 1280px; }}

    .masaisai-header {{
        display: flex; align-items: baseline; justify-content: space-between;
        gap: 1rem; flex-wrap: wrap; margin-bottom: 0.1rem;
    }}
    .masaisai-title {{ font-size: 1.6rem; font-weight: 700; color: {INK_PRIMARY}; }}
    .live-pill {{
        display: inline-flex; align-items: center; gap: 0.4rem;
        font-size: 0.78rem; font-weight: 600; color: {GOOD};
        background: rgba(12,163,12,0.12); border: 1px solid rgba(12,163,12,0.35);
        border-radius: 999px; padding: 0.22rem 0.7rem;
    }}
    .live-dot {{
        width: 7px; height: 7px; border-radius: 50%; background: {GOOD};
        box-shadow: 0 0 0 0 rgba(12,163,12,0.6);
        animation: pulse 2s infinite;
    }}
    @keyframes pulse {{
        0% {{ box-shadow: 0 0 0 0 rgba(12,163,12,0.55); }}
        70% {{ box-shadow: 0 0 0 6px rgba(12,163,12,0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(12,163,12,0); }}
    }}
    .masaisai-sub {{ color: {INK_SECONDARY}; font-size: 0.92rem; margin-bottom: 1.4rem; }}

    div[data-testid="stMetric"] {{
        background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px;
        padding: 0.85rem 1rem 0.7rem 1rem;
    }}
    div[data-testid="stMetricLabel"] {{ color: {INK_MUTED}; font-size: 0.78rem; }}
    div[data-testid="stMetricValue"] {{ color: {INK_PRIMARY}; }}

    .section-label {{
        color: {INK_MUTED}; font-size: 0.78rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.04em;
        margin: 1.6rem 0 0.5rem 0;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st_autorefresh(interval=REFRESH_SECONDS * 1000, key="datarefresh")

st.markdown(
    f"""
    <div class="masaisai-header">
      <div class="masaisai-title">MASAISAI &mdash; Live Spectrum Idle-Verification Console</div>
      <div class="live-pill"><span class="live-dot"></span>LIVE &middot; refreshing every {REFRESH_SECONDS}s</div>
    </div>
    <div class="masaisai-sub">
      Real readings arrive over MQTT from sensing nodes; every node currently reporting on a
      channel is fused into one verdict by the ML model, then passed through the
      POTRAZ-rules constraint engine &mdash; the rules layer always has final veto.
    </div>
    """,
    unsafe_allow_html=True,
)

readings = q("SELECT * FROM sensing_readings ORDER BY id DESC LIMIT 500")
decisions = q("SELECT * FROM access_decisions ORDER BY id DESC LIMIT 500")

if readings.empty:
    st.info("Waiting for the first sensing reading... start the Wokwi node simulation.")
    st.stop()

def channel_sort_key(ch):
    n = str(ch).replace("CH", "")
    return CHANNEL_ORDER.index(int(n)) if n.isdigit() and int(n) in CHANNEL_ORDER else 99


def latest_per(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    return df.sort_values("id").groupby(keys).tail(1)


def with_decision(df: pd.DataFrame, dec: pd.DataFrame) -> pd.DataFrame:
    """Merges in each row's CHANNEL's latest fused decision -- decisions are no longer
    per-node (ingest_service.py fuses every node currently reporting on a channel into one
    verdict, stored under node_id="FUSED"), so the join key is channel alone."""
    dec_latest = latest_per(dec, ["channel"])
    out = df.merge(
        dec_latest[["channel", "granted", "reason", "ml_probability"]], on="channel", how="left"
    )
    out["decision"] = out["granted"].map({1: "\U0001f7e2 VERIFIED IDLE", 0: "\U0001f534 FLAGGED"})
    out["freq_mhz"] = out["channel"].map(channel_to_freq_mhz)
    out["signal"] = out["rssi_dbm"].map(rssi_quality)
    out["signal_bar"] = out["signal"].map(QUALITY_BARS) + "  " + out["signal"]
    return out


last_ts = pd.to_datetime(readings["timestamp"].iloc[0])
age = (datetime.utcnow() - last_ts).total_seconds()
latest_decisions = latest_per(decisions, ["channel"])
verified = int((latest_decisions["granted"] == 1).sum())
flagged = int((latest_decisions["granted"] == 0).sum())

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Sensing nodes", readings["node_id"].nunique())
c2.metric("Channels scanned", readings["channel"].nunique())
c3.metric("Readings stored", len(readings))
c4.metric("Last reading", f"{age:.0f}s ago")
c5.metric("Verified idle", verified)
c6.metric("Flagged", flagged)


# ---------- Node focus selector ----------
st.markdown('<div class="section-label">Focus</div>', unsafe_allow_html=True)
node_list = sorted(readings["node_id"].unique())
sel_col, _ = st.columns([1, 3])
focus = sel_col.selectbox("Focus", ["All nodes"] + node_list, label_visibility="collapsed")

if focus == "All nodes":
    # ---------- Network overview: one row per node ----------
    st.markdown('<div class="section-label">All nodes &mdash; latest status</div>', unsafe_allow_html=True)
    st.caption("Pick a node above to drill into its own channel-by-channel view and RSSI history.")

    overview = with_decision(latest_per(readings, ["node_id"]), decisions)
    overview = overview.sort_values("node_id")

    st.dataframe(
        overview[["node_id", "channel", "freq_mhz", "rssi_dbm", "signal_bar",
                  "sensing_confidence", "decision", "timestamp"]],
        column_config={
            "node_id": "Node",
            "channel": "Active channel",
            "freq_mhz": st.column_config.NumberColumn("Frequency", format="%.0f MHz"),
            "rssi_dbm": st.column_config.NumberColumn("RSSI", format="%.1f dBm"),
            "signal_bar": "Signal",
            "sensing_confidence": st.column_config.ProgressColumn(
                "Sensing confidence", min_value=0.0, max_value=1.0, format="%.2f"
            ),
            "decision": "Decision",
            "timestamp": st.column_config.DatetimeColumn("Last seen", format="HH:mm:ss"),
        },
        hide_index=True,
        width="stretch",
    )

    st.markdown('<div class="section-label">RSSI by node, latest reading</div>', unsafe_allow_html=True)
    bar_colors = [GOOD if g == 1 else CRITICAL for g in overview["granted"].fillna(0)]
    bar_fig = go.Figure(go.Bar(
        x=overview["node_id"], y=overview["rssi_dbm"],
        marker_color=bar_colors,
        text=overview["decision"], textposition="outside",
        hovertemplate="%{x}<br>%{y:.1f} dBm<extra></extra>",
    ))
    bar_fig.add_hline(
        y=-75, line=dict(color=INK_MUTED, width=1, dash="dot"),
        annotation_text="occupancy threshold  -75 dBm",
        annotation_position="top left",
        annotation=dict(font=dict(color=INK_MUTED, size=11)),
    )
    bar_fig.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        font=dict(color=INK_SECONDARY, family="system-ui, -apple-system, Segoe UI, sans-serif"),
        showlegend=False,
        xaxis=dict(showgrid=False, color=INK_MUTED, linecolor=GRID),
        yaxis=dict(title="RSSI (dBm)", showgrid=True, gridcolor=GRID, gridwidth=1,
                   zeroline=False, color=INK_MUTED),
    )
    st.plotly_chart(bar_fig, width="stretch", config={"displayModeBar": False})
    st.caption(
        "Green = VERIFIED IDLE, red = FLAGGED (incumbent likely present, or sensing "
        "confidence too low to trust). Bar height is each node's most recent RSSI reading, "
        "on whichever channel it was scanning last -- the decision itself is the fused "
        "verdict for that whole channel, not this one node's reading alone."
    )

    audit_scope = decisions.copy()
else:
    # ---------- Single-node detail ----------
    node_readings = readings[readings["node_id"] == focus]
    # Decisions are fused per-channel now (node_id="FUSED"), not per real node -- scope the
    # audit/detail view to whichever channels this node happens to be reporting on.
    node_decisions = decisions[decisions["channel"].isin(node_readings["channel"].unique())]

    st.markdown(f'<div class="section-label">{focus} &mdash; latest reading per channel</div>', unsafe_allow_html=True)
    st.caption(
        "The decision column is each channel's fused verdict across every node currently "
        "reporting on it, not just this node's own reading -- see the 'All nodes' view for "
        "the full contributing picture."
    )
    merged = with_decision(latest_per(node_readings, ["node_id", "channel"]), node_decisions)
    merged = merged.sort_values("channel", key=lambda s: s.map(channel_sort_key))

    st.dataframe(
        merged[["channel", "freq_mhz", "rssi_dbm", "signal_bar",
                "sensing_confidence", "ml_probability", "decision", "timestamp"]],
        column_config={
            "channel": "Channel",
            "freq_mhz": st.column_config.NumberColumn("Frequency", format="%.0f MHz"),
            "rssi_dbm": st.column_config.NumberColumn("RSSI", format="%.1f dBm"),
            "signal_bar": "Signal",
            "sensing_confidence": st.column_config.ProgressColumn(
                "Sensing confidence", min_value=0.0, max_value=1.0, format="%.2f"
            ),
            "ml_probability": st.column_config.ProgressColumn(
                "P(occupied) -- fused", min_value=0.0, max_value=1.0, format="%.2f"
            ),
            "decision": "Decision",
            "timestamp": st.column_config.DatetimeColumn("Last seen", format="HH:mm:ss"),
        },
        hide_index=True,
        width="stretch",
    )

    st.markdown(f'<div class="section-label">{focus} &mdash; RSSI over time, all channels</div>', unsafe_allow_html=True)
    st.caption(
        "Watch a line cross the dotted **-75 dBm** threshold: crossing **up** on enough "
        "nodes flips that channel's fused verdict to **FLAGGED**; crossing **down** on "
        "enough nodes verifies the channel **IDLE**. The table above updates within a few "
        "seconds of each crossing."
    )
    chart_df = node_readings.sort_values("id").copy()
    chart_df["timestamp"] = pd.to_datetime(chart_df["timestamp"])

    fig = go.Figure()
    for ch in sorted(chart_df["channel"].unique(), key=channel_sort_key):
        g = chart_df[chart_df["channel"] == ch]
        freq = channel_to_freq_mhz(ch)
        fig.add_trace(go.Scatter(
            x=g["timestamp"], y=g["rssi_dbm"],
            mode="lines",
            name=f"{ch} ({freq:.0f} MHz)",
            line=dict(width=2, color=channel_color(ch), shape="linear"),
            hovertemplate="%{y:.1f} dBm<br>%{x|%H:%M:%S}<extra>" + str(ch) + "</extra>",
        ))

    fig.add_hline(
        y=-75, line=dict(color=INK_MUTED, width=1, dash="dot"),
        annotation_text="occupancy threshold  -75 dBm",
        annotation_position="top left",
        annotation=dict(font=dict(color=INK_MUTED, size=11)),
    )

    fig.update_layout(
        height=340,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(color=INK_SECONDARY, family="system-ui, -apple-system, Segoe UI, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(showgrid=False, color=INK_MUTED, linecolor=GRID),
        yaxis=dict(title="RSSI (dBm)", showgrid=True, gridcolor=GRID, gridwidth=1,
                   zeroline=False, color=INK_MUTED),
        hovermode="closest",
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.caption("Energy above -75 dBm indicates the incumbent broadcaster is active on that channel.")

    audit_scope = node_decisions

with st.expander("Full audit log (every decision, fully explained)"):
    audit = audit_scope.copy()
    audit["freq_mhz"] = audit["channel"].map(channel_to_freq_mhz)
    audit["decision"] = audit["granted"].map({1: "\U0001f7e2 VERIFIED IDLE", 0: "\U0001f534 FLAGGED"})
    st.dataframe(
        audit[["timestamp", "node_id", "channel", "freq_mhz", "decision", "reason",
               "ml_probability", "sensing_confidence", "expires_at"]],
        column_config={
            "freq_mhz": st.column_config.NumberColumn("Frequency", format="%.0f MHz"),
        },
        hide_index=True,
        width="stretch",
    )
