"""Regenerate docs/architecture.png. Run: python make_architecture_diagram.py"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrow

fig, ax = plt.subplots(figsize=(11, 6.5))
ax.set_xlim(0, 11)
ax.set_ylim(0, 6.5)
ax.axis("off")

boxes = [
    ("Sensing Layer\nRTL-SDR nodes\n(Raspberry Pi host)", 0.4, 4.6, "#2f6fed"),
    ("Data Layer\nMulti-node RSSI +\nconfidence readings", 2.9, 4.6, "#2f6fed"),
    ("AI Fusion Engine\n(RandomForest --\nfuses every node on\na channel)", 5.4, 4.6, "#0a1224"),
    ("Rules / Constraint\nLayer\n(ZNFAP as hard\nconstraints)", 7.9, 4.6, "#c0392b"),
    ("Flagging Layer\nVerified idle, or\nflagged for review\n(never autonomous)", 5.4, 1.8, "#2f6fed"),
    ("Dashboard / Audit\nLayer (POTRAZ\nvisibility + override)", 7.9, 1.8, "#2f6fed"),
]

for text, x, y, color in boxes:
    rect = mpatches.FancyBboxPatch((x, y), 2.1, 1.5, boxstyle="round,pad=0.08",
                                     linewidth=1.5, edgecolor=color, facecolor="white")
    ax.add_patch(rect)
    ax.text(x + 1.05, y + 0.75, text, ha="center", va="center", fontsize=9, color=color, weight="bold")

arrows = [
    (2.5, 5.35, 2.9, 5.35),
    (5.0, 5.35, 5.4, 5.35),
    (7.5, 5.35, 7.9, 5.35),
    (6.45, 4.6, 6.45, 3.3),
    (8.95, 4.6, 8.95, 3.3),
    (7.5, 2.55, 7.9, 2.55),
]
for x1, y1, x2, y2 in arrows:
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color="#555555", lw=1.6))

ax.text(0.4, 6.2, "MASAISAI System Architecture", fontsize=15, weight="bold", color="#0a1224")
ax.text(0.4, 0.5,
        "Rules layer always has final veto over the AI layer -- the AI predicts, it never\n"
        "decides. Fusion, not forecasting: combines every node reporting on a channel.",
        fontsize=8.5, color="#555555", style="italic")

plt.tight_layout()
plt.savefig("architecture.png", dpi=200, bbox_inches="tight")
print("Saved architecture.png")
