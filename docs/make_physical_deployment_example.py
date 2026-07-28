"""Regenerate docs/physical_deployment_example.png -- a concrete, ground-level illustration
of what Phase-1 node placement would actually look like in one real rural community, using
real Zimbabwean place names for flavour. This is ILLUSTRATIVE -- no site survey or signed
agreement exists yet -- clearly labelled as such, not an overclaim.

Run: python make_physical_deployment_example.py
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

fig, ax = plt.subplots(figsize=(15, 9.2))
ax.set_xlim(0, 15)
ax.set_ylim(0, 9.2)
ax.axis("off")
fig.patch.set_facecolor(CREAM)
ax.set_facecolor(CREAM)

ax.text(0.2, 8.9, "What Phase-1 Deployment Looks Like On The Ground", fontsize=17, weight="bold", color=NAVY)
ax.text(0.2, 8.45,
        "ILLUSTRATIVE example, not a confirmed site -- no survey or agreement exists yet. Place names are real (Chivhu / Masvingo\n"
        "corridor, Mashonaland East - Masvingo Province) to make the placement LOGIC concrete, not to claim a signed deployment.",
        fontsize=9.3, color=MUTED, style="italic")

# Incumbent transmitter (top, fixed)
tx_x, tx_y = 7.4, 7.3
ax.scatter([tx_x], [tx_y], s=900, marker="^", color=NAVY, zorder=5)
ax.text(tx_x, tx_y + 0.42, "KNOWN INCUMBENT DTT TRANSMITTER\n(registered site, per ZNFAP)",
        ha="center", fontsize=9, weight="bold", color=NAVY)

nodes = [
    # label, x, y, attenuation-role, colour -- all y chosen so labels/notes stay clear
    # (>=1.9) of the two info boxes occupying y=[0.15, 1.70].
    ("Node A -- Chivhu Rural Hospital\n(anchor institution)", 3.3, 5.7, "Low attenuation --\nnear line of sight", GREEN),
    ("Node B -- Chivhu growth-point hub\n(connected backbone site)", 9.8, 6.0, "Low-medium attenuation", GREEN),
    ("Node C -- rural primary school,\nMasvingo road, ~9km out", 1.4, 3.35, "Medium attenuation --\npartial foliage/terrain", GOLD),
    ("Node D -- clinic outpost,\nfarming area, ~14km out", 12.7, 3.15, "Medium attenuation", GOLD),
    ("Node E -- borehole/relay point,\nfarthest community edge, ~19km out", 6.9, 2.75, "High attenuation --\nweakest, lowest confidence", AMBER),
]

for label, x, y, note, color in nodes:
    ax.scatter([x], [y], s=520, marker="o", color=color, edgecolor=NAVY, linewidth=1.3, zorder=5)
    # line back to transmitter, dashed, showing path-loss relationship
    ax.plot([tx_x, x], [tx_y, y], color=color, lw=1.1, linestyle=(0, (4, 3)), zorder=2, alpha=0.75)
    ax.text(x, y - 0.32, label, ha="center", va="top", fontsize=8.4, weight="bold", color=NAVY)
    ax.text(x, y - 0.78, note, ha="center", va="top", fontsize=7.6, color=MUTED, style="italic")

box_y = 0.15
rect = mpatches.FancyBboxPatch((0.2, box_y), 14.6, 0, boxstyle="round,pad=0.02", linewidth=0, facecolor="none")

ax.add_patch(mpatches.FancyBboxPatch((0.2, 0.15), 6.9, 1.55, boxstyle="round,pad=0.05,rounding_size=0.08",
                                       linewidth=1.6, edgecolor=TEAL, facecolor="white", zorder=3))
ax.text(0.55, 1.45, "WHY THIS SPREAD, NOT EVEN COVERAGE", fontsize=10, weight="bold", color=TEAL)
ax.text(0.55, 1.12,
        "Non-collinear (A-E don't sit on one line) so multi-node\ntriangulation can actually resolve a signal's source.\n"
        "Deliberately varied distance/attenuation (near to far)\nso the fusion model has real reliability diversity to learn from.",
        fontsize=8.6, color=NAVY, va="top")

ax.add_patch(mpatches.FancyBboxPatch((7.75, 0.15), 6.9, 1.55, boxstyle="round,pad=0.05,rounding_size=0.08",
                                       linewidth=1.6, edgecolor=SURFACE, facecolor=SURFACE, zorder=3))
ax.text(8.1, 1.45, "ALL FIVE FEED THE SAME PIPELINE", fontsize=10, weight="bold", color="white")
ax.text(8.1, 1.12,
        "Every node -> same MQTT broker -> same fusion model\n-> same rules engine -> same POTRAZ dashboard.\n"
        "No per-node special-casing -- this is exactly the\narchitecture already running in tonight's live demo.",
        fontsize=8.6, color="white", va="top")

plt.tight_layout()
plt.savefig("physical_deployment_example.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
print("Saved physical_deployment_example.png")
