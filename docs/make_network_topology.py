"""Regenerate docs/network_topology.png -- logical (data/protocol flow) and physical
(where things actually run, today vs. the target Phase-1 deployment) topology of the
MASAISAI sensing network, fusion AI, rules engine, and dashboard.

Run: python make_network_topology.py
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ---- Brand palette, matching the pitch deck / dashboard redesign ----
NAVY = "#0B1C33"
SURFACE = "#0F2340"
TEAL = "#2EC4B6"
GOLD = "#F5A623"
GREEN = "#22C55E"
AMBER = "#F59E0B"
MUTED = "#5A6578"
CREAM = "#FAF7F0"

fig, ax = plt.subplots(figsize=(15, 13))
ax.set_xlim(0, 15)
ax.set_ylim(0, 13)
ax.axis("off")
fig.patch.set_facecolor(CREAM)
ax.set_facecolor(CREAM)


def box(x, y, w, h, text, edge=NAVY, face="white", fontsize=9.2, weight="bold",
        text_color=None, fontstyle="normal"):
    rect = mpatches.FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.05,rounding_size=0.07",
        linewidth=1.8, edgecolor=edge, facecolor=face, zorder=3,
    )
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
             fontsize=fontsize, color=text_color or edge, weight=weight,
             fontstyle=fontstyle, zorder=4, linespacing=1.3)


def arrow(x1, y1, x2, y2, color=MUTED, style="-", lw=1.6, label=None, label_dx=0.0, label_dy=0.0):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), zorder=2,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                linestyle=style, shrinkA=1, shrinkB=1))
    if label:
        mx, my = (x1 + x2) / 2 + label_dx, (y1 + y2) / 2 + label_dy
        ax.text(mx, my, label, ha="center", va="center", fontsize=7.3,
                 color=color, style="italic", zorder=5,
                 bbox=dict(boxstyle="round,pad=0.12", facecolor=CREAM, edgecolor="none"))


# =====================================================================
# TITLE
# =====================================================================
ax.text(0.2, 12.72, "MASAISAI -- Network Topology", fontsize=19, weight="bold", color=NAVY)
ax.text(0.2, 12.36,
        "One band, UHF TV white space. Sensing -> fusion AI -> rules engine -> dashboard.",
        fontsize=10.5, color=MUTED, style="italic")

# =====================================================================
# BAND BACKGROUNDS -- logical on top, physical below, no vertical overlap
# =====================================================================
LOGICAL_BOTTOM, LOGICAL_TOP = 6.35, 12.05
PHYSICAL_BOTTOM, PHYSICAL_TOP = 0.15, 6.15

ax.add_patch(mpatches.FancyBboxPatch((0.15, LOGICAL_BOTTOM), 14.7, LOGICAL_TOP - LOGICAL_BOTTOM,
                                       boxstyle="round,pad=0.05", linewidth=0,
                                       facecolor="#EEF3F8", zorder=1))
ax.text(0.4, LOGICAL_TOP - 0.28, "LOGICAL TOPOLOGY -- data & protocol flow",
        fontsize=12.5, weight="bold", color=TEAL, zorder=2)

ax.add_patch(mpatches.FancyBboxPatch((0.15, PHYSICAL_BOTTOM), 14.7, PHYSICAL_TOP - PHYSICAL_BOTTOM,
                                       boxstyle="round,pad=0.05", linewidth=0,
                                       facecolor="#F7EFE3", zorder=1))
ax.text(0.4, PHYSICAL_TOP - 0.4, "PHYSICAL TOPOLOGY -- where things actually run",
        fontsize=12.5, weight="bold", color=GOLD, zorder=2)

# =====================================================================
# LOGICAL TOPOLOGY content, all within [LOGICAL_BOTTOM, LOGICAL_TOP]
# =====================================================================
# Row 1: 10 sensing nodes
node_y, node_h = 10.72, 0.55
node_w, gap = 1.31, 0.15
start_x = 0.35
ax.text(start_x, node_y + node_h + 0.14,
        "10x simulated sensing nodes -- one channel scan per node per tick",
        fontsize=8.3, color=MUTED, style="italic")
node_centers = []
for i in range(10):
    x = start_x + i * (node_w + gap)
    box(x, node_y, node_w, node_h, f"N{i+1:02d}", face="white", edge=TEAL, fontsize=8)
    node_centers.append(x + node_w / 2)
for xc in node_centers[::3]:
    arrow(xc, node_y, xc, node_y - 0.35, color=TEAL, lw=1.1)

# Row 2: MQTT broker
broker_y, broker_h = 9.75, 0.6
box(start_x, broker_y, 14.15, broker_h,
    "MQTT BROKER -- Mosquitto, :1883, authenticated  |  topic masaisai/sensing/<node_id>",
    face="white", edge=NAVY, fontsize=9.8)
arrow((start_x + 14.15 / 2), broker_y, (start_x + 14.15 / 2), broker_y - 0.35,
      color=NAVY, label="subscribe masaisai/sensing/#", label_dy=0.02)

# Row 3: Ingest service (left) -> AI fusion model -> Rules engine
row3_y, row3_h = 8.05, 1.15
ingest_w = 6.7
box(start_x, row3_y, ingest_w, row3_h,
    "INGEST SERVICE (ingest_service.py)\nfuses every node currently reporting on a channel:\n"
    "mean/min/max/spread RSSI, confidence-weighted\nvote, rolling history",
    face=SURFACE, edge=SURFACE, text_color="white", fontsize=8.4)

ai_x, ai_w = start_x + ingest_w + 0.35, 3.4
box(ai_x, row3_y, ai_w, row3_h, "AI FUSION MODEL\nRandomForest\n(PREDICTS only)",
    face="white", edge=GREEN, fontsize=9)

rules_x, rules_w = ai_x + ai_w + 0.35, 3.35
box(rules_x, row3_y, rules_w, row3_h, "RULES ENGINE\nabsolute veto\n(DECIDES)",
    face="white", edge=AMBER, fontsize=9)

arrow(start_x + ingest_w, row3_y + row3_h / 2, ai_x, row3_y + row3_h / 2, color=GREEN, lw=1.5)
arrow(ai_x + ai_w, row3_y + row3_h / 2, rules_x, row3_y + row3_h / 2, color=AMBER, lw=1.5,
      label="P(occupied)\n+ confidence", label_dy=0.32)

# Golden-rule callout -- placed in the clear horizontal gap between the broker row and row 3,
# to the right of the subscribe-arrow so it never overlaps either box.
ax.text(8.4, (broker_y + (row3_y + row3_h)) / 2,
        "The rules layer always overrides the AI layer --\nthe AI predicts, it never decides.",
        fontsize=8.8, color=AMBER, weight="bold", style="italic", ha="left", va="center")

arrow(start_x + ingest_w / 2, row3_y, start_x + ingest_w / 2, row3_y - 0.35, color=NAVY,
      label="INSERT", label_dy=0.02)

# Row 4: MySQL -> Dashboard
row4_y, row4_h = 6.55, 0.95
mysql_w = 6.9
box(start_x, row4_y, mysql_w, row4_h,
    "MySQL\nsensing_readings (raw, per node) +\naccess_decisions (fused, per channel:\nVERIFIED IDLE / FLAGGED)",
    face="white", edge=NAVY, fontsize=8.3)

dash_x, dash_w = start_x + mysql_w + 0.35, 7.1
box(dash_x, row4_y, dash_w, row4_h,
    "DASHBOARD (live_dashboard.py, Streamlit :8501)\npolls every 5s -- shows fused verdict\n+ full audit trail",
    face="white", edge=TEAL, fontsize=8.6)
arrow(start_x + mysql_w, row4_y + row4_h / 2, dash_x, row4_y + row4_h / 2, color=NAVY,
      lw=1.4, style=":", label="SELECT")

# =====================================================================
# PHYSICAL TOPOLOGY content, all within [PHYSICAL_BOTTOM, PHYSICAL_TOP]
# =====================================================================
prow_y, prow_h = 4.35, 1.35
box(0.4, prow_y, 4.05, prow_h,
    "PRESENTER'S LAPTOP\nWokwi simulator (VS Code)\nsimulates 10 nodes off 1 ESP32 board",
    face="white", edge=TEAL, fontsize=8.8)
arrow(4.45, prow_y + prow_h / 2, 5.75, prow_y + prow_h / 2, color=TEAL,
      label="MQTT over\nWi-Fi/Internet", label_dy=0.35)

box(5.75, prow_y - 0.3, 4.7, prow_h + 0.6,
    "VPS -- WINDOWS SERVER\n38.247.146.172 (cloud-hosted)\n\nMosquitto + ingest_service.py\n"
    "+ MySQL + live_dashboard.py\nall co-located, one box",
    face=SURFACE, edge=SURFACE, text_color="white", fontsize=8.8)

arrow(10.45, prow_y + prow_h / 2, 11.75, prow_y + prow_h / 2, color=NAVY,
      label="HTTPS :8501", label_dy=0.35)
box(11.75, prow_y, 2.9, prow_h,
    "JUDGES / POTRAZ\nany browser,\nanywhere with internet",
    face="white", edge=NAVY, fontsize=8.8)

divider_y = 3.55
ax.plot([0.4, 14.6], [divider_y, divider_y], linestyle=(0, (4, 3)), color=MUTED, lw=1.2)
ax.text(0.4, divider_y - 0.3, "TODAY (verified live, 27-28 Jul)", fontsize=8.6, color=MUTED,
        weight="bold", style="italic")
ax.text(9.0, divider_y - 0.3, "TARGET PHASE-1 DEPLOYMENT (not yet built)", fontsize=8.6,
        color=GOLD, weight="bold", style="italic")

brow_y, brow_h = 0.4, 2.35
box(0.4, brow_y, 6.55, brow_h,
    "6-10 real RTL-SDR + Raspberry-Pi-class nodes\ndistributed across ONE rural community:\n"
    "non-collinear placement (triangulation geometry)\n+ deliberate distance/attenuation diversity\n"
    "from the known incumbent transmitter site --\nnot even coverage.",
    face="white", edge=GOLD, fontsize=8.5, weight="normal", fontstyle="italic")
arrow(6.95, brow_y + brow_h / 2, 7.85, brow_y + brow_h / 2, color=GOLD, style="--",
      label="same MQTT/\nfusion pipeline")

box(7.85, brow_y, 6.35, brow_h,
    "Same VPS backend (or ZCHPC Cloud Compute\nEnvironment, per proposal) -- no pipeline change,\n"
    "only the sensing hardware and its physical\nplacement change, from simulated to real.",
    face="white", edge=GOLD, fontsize=8.5, fontstyle="italic")

plt.tight_layout()
plt.savefig("network_topology.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
print("Saved network_topology.png")
