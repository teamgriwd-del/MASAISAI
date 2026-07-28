"""Regenerate docs/business_model_diagram.png -- a one-page visual matching business_model.md,
same visual family as the architecture/AI/constraints diagrams built tonight.

Run: python make_business_model_diagram.py
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

fig, ax = plt.subplots(figsize=(15, 9.4))
ax.set_xlim(0, 15)
ax.set_ylim(0, 9.4)
ax.axis("off")
fig.patch.set_facecolor(CREAM)
ax.set_facecolor(CREAM)


def box(x, y, w, h, text, edge=NAVY, face="white", fontsize=9.2, weight="normal",
        text_color=None):
    rect = mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05,rounding_size=0.08",
                                     linewidth=1.7, edgecolor=edge, facecolor=face, zorder=3)
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize,
             color=text_color or edge, weight=weight, zorder=4, linespacing=1.3)


ax.text(0.2, 9.05, "Business Model -- Who Pays, Who Benefits, Why", fontsize=17, weight="bold", color=NAVY)
ax.text(0.2, 8.65,
        "MASAISAI verifies band idle-status and flags anomalies -- it does not itself grant access. One buyer, three revenue lines.",
        fontsize=9.5, color=MUTED, style="italic")

# Buyer / problem / value prop row
box(0.2, 6.5, 4.6, 1.75,
    "BUYER: POTRAZ (sole buyer)\n\nLegal mandate over the spectrum +\nthe AI4I budget line this comes\nfrom. Not rural ISPs or\ncommunities directly.",
    face=SURFACE, edge=SURFACE, text_color="white", fontsize=9.3)

box(5.1, 6.5, 4.6, 1.75,
    "THEIR PROBLEM\n\nAn idle national asset, no\nverifiable way to prove how idle\nit is, real pressure from their\nown National AI Strategy\ncommitments.",
    face="white", edge=AMBER, fontsize=9.3)

box(10.0, 6.5, 4.8, 1.75,
    "VALUE DELIVERED\n\nContinuous, verifiable\nutilization intelligence a static\nZNFAP table can't provide --\nno allocation-law change\nrequired.",
    face="white", edge=TEAL, fontsize=9.3)

# Revenue lines row
ax.text(0.2, 6.05, "THREE REVENUE LINES, NOT ONE NUMBER", fontsize=12.5, weight="bold", color=NAVY)

box(0.2, 4.1, 4.85, 1.7,
    "1. PILOT COST-RECOVERY\n(one-time)\n\n~$80,000 -- itemised in the\nproposal, AI4I milestone-funded.\nNot a margin play.",
    face="white", edge=GOLD, fontsize=9.2)
box(5.25, 4.1, 4.85, 1.7,
    "2. HARDWARE, COST-PLUS\n\n~$190-230/site delivered vs.\n~$100-150 bare BOM -- covers\ncalibration, warranty, field\nsupport.",
    face="white", edge=GOLD, fontsize=9.2)
box(10.3, 4.1, 4.5, 1.7,
    "3. MANAGED SERVICE\n(recurring)\n\n~$50-80/site/year -- less than\none month of the VSAT/Starlink\nbill it replaces.",
    face="white", edge=GOLD, fontsize=9.2)

# Long-term revenue, both sides
box(0.2, 2.15, 7.15, 1.75,
    "LONG-TERM: THE TEAM EARNS\n\nHardware/integration markup + the\nrecurring contract + (if this pilot\nsucceeds) the same package resold to\na second African regulator at lower\nmarginal cost.",
    face=SURFACE, edge=SURFACE, text_color="white", fontsize=9)
box(7.6, 2.15, 7.2, 1.75,
    "LONG-TERM: POTRAZ EARNS\n\nA previously-idle asset gains a real\ncoordination/visibility capability, plus\nfirst-mover standing as (to our\nknowledge) Africa's first AI-governed\nspectrum-utilization authority.",
    face=SURFACE, edge=SURFACE, text_color="white", fontsize=9)

# Honest risks strip
ax.text(0.2, 1.75,
    "NAMED RISKS, NOT HIDDEN: POTRAZ's own decision timeline · hardware sourcing lead times · the disclosed RF-differentiation gap · ZCHPC relationship not yet confirmed",
    fontsize=8.8, color=AMBER, weight="bold", style="italic")
ax.text(0.2, 1.3,
    "IP: codebase stays MIT -- a trust requirement for a regulator auditing an AI spectrum-safety system, not a giveaway. What's owned: tuned models, deployment know-how, brand, real pilot dataset.",
    fontsize=8.6, color=MUTED, style="italic")

plt.tight_layout()
plt.savefig("business_model_diagram.png", dpi=200, bbox_inches="tight", facecolor=CREAM)
print("Saved business_model_diagram.png")
