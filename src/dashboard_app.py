"""
MASAISAI operations console (Streamlit host).

Redesigned September 2026 as a full-viewport spectrum-management console. Streamlit remains
the server and the data layer; the interface itself is a self-contained HTML/CSS/JS
application in src/ui/, rendered in a single component so it has pixel-level control over
layout that Streamlit's native widgets can't give.

Nothing in the backend changed. dashboard_data.py calls sensing_sim, occupancy_model and
constraint_engine exactly as the previous dashboard did, and shapes the results into the
payload the UI renders. The previous dashboard's substance -- the fusion-vs-naive-vote
benchmark, per-node raw readings, rule-by-rule reasons and the audit trail -- all survives,
now spread across the console's views instead of one long page.

Charts and the map are drawn as inline SVG, so the console has no chart-library or map-tile
dependency and runs fully offline on the exhibition floor (fonts fall back to system faces).

Run: streamlit run src/dashboard_app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
import streamlit.components.v1 as components

from dashboard_data import build_payload, run_backend

UI_DIR = Path(__file__).resolve().parent / "ui"

st.set_page_config(page_title="MASAISAI -- Spectrum Intelligence", layout="wide",
                   initial_sidebar_state="collapsed")

# Strip Streamlit's own chrome so the console owns the whole viewport.
st.markdown(
    """
    <style>
    header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
    [data-testid="stStatusWidget"], #MainMenu, footer { display: none !important; }
    html, body, .stApp, [data-testid="stAppViewContainer"] { background: #07111f; overflow: hidden; }
    .block-container, [data-testid="stMainBlockContainer"] { padding: 0 !important; max-width: 100% !important; }
    [data-testid="stVerticalBlock"] { gap: 0 !important; }
    [data-testid="stElementContainer"] { margin: 0 !important; }
    iframe { display: block; width: 100% !important; height: 100vh !important; border: 0; }
    </style>
    """,
    unsafe_allow_html=True,
)


SKELETON = """
<div style="position:fixed;inset:0;background:#07111f;display:grid;place-items:center;
  font-family:'Inter','Segoe UI',system-ui,sans-serif;color:#b6c3d6;z-index:5">
  <div style="text-align:center">
    <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="#2dc6f0" stroke-width="1.7"
      stroke-linecap="round" style="margin-bottom:18px">
      <path d="M10.2 11a1.8 1.8 0 1 0 3.6 0a1.8 1.8 0 1 0 -3.6 0"/>
      <path d="M7.6 6.6a6.2 6.2 0 0 0 0 8.8M16.4 15.4a6.2 6.2 0 0 0 0-8.8" opacity=".75">
        <animate attributeName="opacity" values=".15;.8;.15" dur="1.8s" repeatCount="indefinite"/></path>
      <path d="M4.6 3.6a10.4 10.4 0 0 0 0 14.8M19.4 18.4a10.4 10.4 0 0 0 0-14.8" opacity=".4">
        <animate attributeName="opacity" values=".08;.5;.08" dur="1.8s" begin=".3s" repeatCount="indefinite"/></path>
      <path d="M12 13v8.5"/></svg>
    <div style="font-size:22px;font-weight:800;color:#eaf0f8;letter-spacing:.01em">MASAISAI</div>
    <div style="font-size:13px;margin-top:8px">Fetching sensing nodes and fusing this window&hellip;</div>
    <div style="width:220px;height:3px;border-radius:3px;background:#13243f;margin:20px auto 0;overflow:hidden">
      <div style="width:38%;height:100%;background:#2dc6f0;border-radius:3px;
        animation:sweep 1.25s ease-in-out infinite"></div></div>
  </div>
</div>
<style>@keyframes sweep{0%{transform:translateX(-100%)}100%{transform:translateX(360%)}}</style>
"""


@st.cache_resource(show_spinner=False)
def get_backend():
    return run_backend()


def render_console(payload: dict) -> str:
    html = (UI_DIR / "index.html").read_text(encoding="utf-8")
    data = json.dumps(payload).replace("</", "<\\/")   # never let data close a <script>
    return (html.replace("{{STYLES}}", (UI_DIR / "styles.css").read_text(encoding="utf-8"))
                .replace("{{DATA}}", data)
                .replace("{{SCRIPT}}", (UI_DIR / "app.js").read_text(encoding="utf-8")))


# The first run trains the fusion model, which takes a few seconds. Show the
# console's own loading state rather than Streamlit's spinner on a blank page.
_splash = st.empty()
_splash.markdown(SKELETON, unsafe_allow_html=True)
try:
    _payload = build_payload(get_backend())
except Exception as exc:                                   # noqa: BLE001
    _splash.empty()
    st.markdown(
        f"""<div style="position:fixed;inset:0;background:#07111f;display:grid;place-items:center;
          font-family:'Inter','Segoe UI',system-ui,sans-serif;color:#b6c3d6;padding:24px">
          <div style="max-width:520px;background:#0e1c32;border:1px solid #233a5e;border-radius:12px;padding:24px">
            <div style="font-size:19px;font-weight:700;color:#eaf0f8;margin-bottom:8px">Spectrum data unavailable</div>
            <p style="font-size:13.5px;margin:0 0 12px">The sensing backend could not build this window.</p>
            <pre style="background:#0a1628;border:1px solid #1b2d4a;border-radius:7px;padding:10px;
              font-size:11.5px;color:#ff9d9a;overflow:auto">{exc}</pre>
            <p style="font-size:12.5px;margin:0">Reload the page to retry.</p></div></div>""",
        unsafe_allow_html=True,
    )
    st.stop()
_splash.empty()

components.html(render_console(_payload), height=1080, scrolling=False)
