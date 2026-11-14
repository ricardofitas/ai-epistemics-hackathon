"""Render verified fixed-panel RULE acceptance and missing-output bounds."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
report = json.loads((ROOT / "RANKING_SENSITIVITY.json").read_text())
assert report["status"] == "PASS"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
figure, axes = plt.subplots(1, 2, figsize=(9, 4.3), sharey=True)
models = (("gemma-4-31b-it", "Gemma"), ("qwen3.8-27b", "Qwen"))
styles = (("free_form", "Free-form instruction", "#2166AC", "o"),
          ("choice", "Choice instruction", "#B35806", "s"))

for axis, (model, title) in zip(axes, models):
    for instruction, label, color, marker in styles:
        bounds = [report["conditions"][instruction + "__" + carrier]
                  ["models"][model]["correct_count_bounds"]
                  for carrier in ("absent", "A.None")]
        lower = [value[0] * 5 for value in bounds]
        upper = [value[1] * 5 for value in bounds]
        midpoint = [(left + right) / 2 for left, right in zip(lower, upper)]
        errors = [[center - left for center, left in zip(midpoint, lower)],
                  [right - center for right, center in zip(upper, midpoint)]]
        axis.errorbar([0, 1], midpoint, yerr=errors, color=color,
                      marker=marker, linewidth=2, capsize=5, label=label)
    axis.set_title(title)
    axis.set_xticks([0, 1], ["Absent", "Present"])
    axis.set_xlabel("Appended A. None")
    axis.set_xlim(-0.15, 1.15)
    axis.set_ylim(-3, 103)
    axis.set_yticks([0, 20, 40, 60, 80, 100])
    axis.grid(axis="y", color="#DDDDDD", linewidth=0.7)
    axis.spines[["top", "right"]].set_visible(False)

axes[0].set_ylabel("Official RULE acceptance (%)")
handles, labels = axes[0].get_legend_handles_labels()
figure.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.105),
              ncol=2, frameon=False)
figure.text(0.5, 0.035,
            "Same 20 source questions per model. Whiskers cover every binary assignment to incomplete outputs.\n"
            "Markers show interval midpoints. Bounds describe missing-output sensitivity on this fixed panel.",
            ha="center", fontsize=9)
figure.tight_layout(rect=(0.015, 0.20, 1, 1))
figure.savefig(ROOT / "instruction_carrier_interaction.png", dpi=220)
plt.close(figure)
