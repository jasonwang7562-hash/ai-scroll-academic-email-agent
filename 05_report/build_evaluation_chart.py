from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
output = ROOT / "05_report" / "assets" / "evaluation_comparison.png"
output.parent.mkdir(parents=True, exist_ok=True)

labels = ["Task type", "Deadline", "Urgency", "Calendar", "Cross-email"]
baseline = np.array([56.0, 74.4, 82.0, 56.0, 0.0])
current = np.array([86.0, 93.0, 96.0, 90.0, 100.0])
y = np.arange(len(labels))
fig, ax = plt.subplots(figsize=(8.4, 3.5), dpi=180)
ax.barh(y + 0.18, baseline, 0.32, label="Keyword/date baseline", color="#B8C8D6")
ax.barh(y - 0.18, current, 0.32, label="AI Scroll pipeline", color="#119E96")
for idx, value in enumerate(baseline):
    ax.text(value + 1.2, idx + 0.18, f"{value:g}%", va="center", fontsize=8, color="#52677A")
for idx, value in enumerate(current):
    ax.text(min(value + 1.2, 101.5), idx - 0.18, f"{value:g}%", va="center", fontsize=8, color="#0B2D49", fontweight="bold")
ax.set_yticks(y, labels, fontsize=9, color="#0B2D49")
ax.set_xlim(0, 106)
ax.invert_yaxis()
ax.set_xlabel("Correct cases (%)", fontsize=8, color="#60748A")
ax.grid(axis="x", color="#E5EDF2", linewidth=0.8)
ax.set_axisbelow(True)
for spine in ax.spines.values():
    spine.set_visible(False)
ax.tick_params(axis="x", labelsize=8, colors="#60748A")
ax.legend(frameon=False, loc="lower right", fontsize=8)
plt.tight_layout()
fig.savefig(output, bbox_inches="tight", facecolor="white")
plt.close(fig)
