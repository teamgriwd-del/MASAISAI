"""Regenerate docs/ai_solution_diagram.png -- an unmistakable, literal picture of what the AI
is and what it does: real input features -> RandomForest -> a probability, benchmarked against
the naive-vote baseline it has to beat. Built after a POTRAZ technical-clinic engineer said
plainly: 'if we don't see the AI, you lose.'

Run: python make_ai_solution_diagram.py
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

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


def box(x, y, w, h, text, edge=NAVY, face="white", fontsize=9.5, weight="bold",
        text_color=None):
    rect = mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05,rounding_size=0.08",
                                     linewidth=1.8, edgecolor=edge, facecolor=face, zorder=3)
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize,
             color=text_color or edge, weight=weight, zorder=4, linespacing=1.3)


def arrow(x1, y1, x2, y2, color=MUTED, lw=2.2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), zorder=2,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw))


ax.text(0.2, 8.05, "THIS is the AI -- a RandomForestClassifier, trained and tested, not a label",
        fontsize=15.5, weight="bold", color=NAVY)

# ---- LEFT: real inputs ----
box(0.2, 4.5, 4.3, 3.1,
    "REAL INPUTS (12 features)\n\nmean / min / max / std RSSI\nmean / min / max confidence\nnaive vote fraction\nconfidence-weighted vote\nrolling occupancy history\nchannel identity, hour, day",
    face="white", edge=TEAL, fontsize=9.3, weight="normal")
ax.text(0.2, 4.15, "-- from every node currently reporting on one channel --",
        fontsize=8.5, color=MUTED, style="italic")

arrow(4.6, 6.05, 5.5, 6.05, color=TEAL)

# ---- MIDDLE: the model ----
box(5.6, 4.8, 3.5, 2.5, "RandomForestClassifier\n40 trees, depth 6\n\n<0.05 MB, <40ms/prediction\n(budget: 256MB, 100ms --\nverified by test, not claimed)",
    face=SURFACE, edge=SURFACE, text_color="white", fontsize=9)

arrow(9.2, 6.05, 10.1, 6.05, color=GREEN)

# ---- RIGHT: the output ----
box(10.2, 4.8, 4.3, 2.5,
    "OUTPUT: P(channel is occupied)\n\na single number, 0.00-1.00 --\nfed to the rules layer, which\ndecides VERIFIED IDLE or FLAGGED.\nThe AI never decides by itself.",
    face="white", edge=AMBER, fontsize=9.3, weight="normal")

# ---- BOTTOM: the benchmark, real numbers ----
ax.text(0.2, 3.55, "WHY THIS AI, NOT A SIMPLER RULE -- benchmarked, not asserted:",
        fontsize=12.5, weight="bold", color=NAVY)

bar_ax_left = 0.6
# Real numbers, computed fresh from one run of sensing_sim.generate_dataset() +
# occupancy_model (src/sensing_sim.py, src/occupancy_model.py) -- not asserted, reproducible
# via `python src/occupancy_model.py`. Single-sensor = one node's own RSSI threshold vs the
# true channel/hour ground truth; naive vote = unweighted majority of all nodes' threshold
# flags; fusion = the trained RandomForest.
bars = [
    ("Single sensor\nthreshold", 0.80, "#B8C2CE"),
    ("Unweighted vote\nacross sensors\n(the baseline)", 0.986, GOLD),
    ("This AI\n(fusion model)", 1.00, GREEN),
]
bw = 2.6
for i, (label, val, color) in enumerate(bars):
    x = bar_ax_left + i * 3.2
    h = val * 2.6
    rect = mpatches.FancyBboxPatch((x, 0.5), bw, h, boxstyle="round,pad=0.02,rounding_size=0.05",
                                     linewidth=1.5, edgecolor=color, facecolor=color, alpha=0.85, zorder=3)
    ax.add_patch(rect)
    num_str = f"{val*100:.1f}".rstrip("0").rstrip(".")
    ax.text(x + bw / 2, 0.5 + h + 0.18, f"{num_str}%", ha="center", fontsize=13, weight="bold", color=NAVY)
    ax.text(x + bw / 2, 0.32, label, ha="center", va="top", fontsize=9, color=MUTED, weight="bold")

ax.text(10.6, 2.9,
    "One sensor alone: 80%. A plain vote across\nsensors helps a lot (98.6%) but its errors\nare missed occupancy -- the dangerous\ndirection for incumbent protection.\nThis AI closes the rest of that gap.",
    fontsize=9.1, color=NAVY, style="italic", ha="left", va="top",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor=AMBER, linewidth=1.3))

plt.tight_layout()
plt.savefig("ai_solution_diagram.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
print("Saved ai_solution_diagram.png")
