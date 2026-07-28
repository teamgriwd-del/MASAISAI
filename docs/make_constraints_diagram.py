"""Regenerate docs/constraints_diagram.png -- hardware constraints (left) and data
constraints (right), side by side, in one slide-ready image. Built after the technical-clinic
engineer asked to see both explicitly.

Run: python make_constraints_diagram.py
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

NAVY = "#0B1C33"
SURFACE = "#0F2340"
TEAL = "#2EC4B6"
GOLD = "#F5A623"
GREEN = "#22C55E"
AMBER = "#F59E0B"
MUTED = "#5A6578"
CREAM = "#FAF7F0"

fig, ax = plt.subplots(figsize=(15, 8.4))
ax.set_xlim(0, 15)
ax.set_ylim(0, 8.4)
ax.axis("off")
fig.patch.set_facecolor(CREAM)
ax.set_facecolor(CREAM)


def box(x, y, w, h, text, edge=NAVY, face="white", fontsize=9.3, weight="normal",
        text_color=None, ha="center"):
    rect = mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05,rounding_size=0.08",
                                     linewidth=1.8, edgecolor=edge, facecolor=face, zorder=3)
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h / 2, text, ha=ha, va="center", fontsize=fontsize,
             color=text_color or edge, weight=weight, zorder=4, linespacing=1.35)


# Column dividers
ax.plot([7.45, 7.45], [0.3, 7.9], color=MUTED, lw=1, linestyle=(0, (3, 3)))

# ============ LEFT: HARDWARE CONSTRAINTS ============
ax.text(0.2, 7.85, "HARDWARE CONSTRAINTS", fontsize=15, weight="bold", color=TEAL)

box(0.2, 5.7, 6.9, 1.7,
    "TODAY'S DEMO: ESP32 (Wokwi-simulated)\n\nMeasures RSSI (signal strength) only.\n"
    "Simulates 10 nodes off one board.\nCannot classify signal type -- energy only.",
    face="white", edge=GOLD, fontsize=9.5)

box(0.2, 3.6, 6.9, 1.7,
    "PRODUCTION TARGET: RTL-SDR +\nRaspberry-Pi-class host (unchanged\nfrom the original proposal)\n\n"
    "Wideband SDR front-end -- captures\nreal I/Q samples, needed for actual\nsignal classification.",
    face="white", edge=TEAL, fontsize=9.5)

box(0.2, 1.5, 6.9, 1.7,
    "EDGE BUDGET -- verified by test,\nnot claimed\n\n"
    "Model size: <0.05 MB (budget 256 MB)\nLatency: <40 ms/prediction (budget 100 ms)\n"
    "Runs comfortably on Raspberry-Pi-class hardware.",
    face=SURFACE, edge=SURFACE, text_color="white", fontsize=9.5)

ax.text(0.2, 1.15,
    "Honest gap: RSSI alone can't yet tell a specific broadcaster from another\n"
    "transmitter on the same frequency -- that needs real I/Q + cyclostationary detection.",
    fontsize=8.6, color=AMBER, weight="bold", style="italic")

# ============ RIGHT: DATA CONSTRAINTS ============
ax.text(7.75, 7.85, "DATA CONSTRAINTS", fontsize=15, weight="bold", color=GOLD)

box(7.75, 5.7, 6.9, 1.7,
    "TODAY: 100% synthetic\n\nDisclosed throughout the repo, not\nhidden. No live POTRAZ feed or real\nsensing data existed to train on yet.",
    face="white", edge=GOLD, fontsize=9.5)

box(7.75, 3.6, 6.9, 1.7,
    "BUILT TO BE REALISTIC, NOT EASY\n\nIndependent per-node fade noise,\nwide attenuation range (0-60 dB),\n"
    "confidence degradation -- deliberately\nharder than a clean toy dataset.",
    face="white", edge=TEAL, fontsize=9.5)

box(7.75, 1.5, 6.9, 1.7,
    "WHAT CHANGES WITH REAL DATA\n\nsensing_sim.py -> live RTL-SDR readings.\n"
    "znfap_rules_PLACEHOLDER.json -> POTRAZ's\nreal rules extract. Nothing else in the\npipeline needs to change.",
    face=SURFACE, edge=SURFACE, text_color="white", fontsize=9.5)

ax.text(7.75, 1.15,
    "Honest gap: no real POTRAZ occupancy data exists yet to statistically validate\n"
    "against -- exactly what a monitoring pilot partnership would produce.",
    fontsize=8.6, color=AMBER, weight="bold", style="italic")

plt.tight_layout()
plt.savefig("constraints_diagram.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
print("Saved constraints_diagram.png")
