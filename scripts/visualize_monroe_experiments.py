from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path("results")
OUT = ROOT / "visualizations"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.labelsize": 11,
    "figure.dpi": 120,
    "savefig.dpi": 300,
})

def load(folder):
    return pd.read_csv(ROOT / folder / "fold_metrics.csv")

def save(name):
    plt.savefig(OUT / name, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {OUT / name}")

baseline = load("monthly_jrc_rf_cv")
groups = load("monthly_jrc_rf_ablation")
individual = load("monthly_jrc_rf_individual_ablation")
sizes = load("monthly_jrc_rf_sample_sizes")

assert len(baseline) == 5
assert len(groups) == 25
assert len(individual) == 40
assert len(sizes) == 25

# ---------------------------------------------------------
# FIGURE 1: POOLED CONFUSION MATRIX
# ---------------------------------------------------------
tn = int(baseline["tn"].sum())
fp = int(baseline["fp"].sum())
fn = int(baseline["fn"].sum())
tp = int(baseline["tp"].sum())

cm = np.array([[tn, fp], [fn, tp]])

fig, ax = plt.subplots(figsize=(7, 6))
im = ax.imshow(cm, cmap="Blues")

ax.set_xticks([0, 1], ["Predicted Land", "Predicted Water"])
ax.set_yticks([0, 1], ["JRC Land", "JRC Water"])

for i in range(2):
    for j in range(2):
        value = cm[i, j]
        ax.text(
            j, i, f"{value:,}",
            ha="center", va="center",
            fontsize=15,
            color="white" if value > cm.max() / 2 else "black"
        )

ax.set_title("Random Forest: Pooled Confusion Matrix\n"
             "Monroe Lake, July 2017")
fig.colorbar(im, ax=ax, label="Pixel count")
save("01_confusion_matrix.png")

# ---------------------------------------------------------
# FIGURE 2: BASELINE PERFORMANCE ACROSS SPATIAL FOLDS
# ---------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 5))

for metric, label in [
    ("precision", "Precision"),
    ("recall", "Recall"),
    ("f1", "F1-score"),
    ("iou", "IoU"),
]:
    ax.plot(
        baseline["fold"],
        baseline[metric] * 100,
        marker="o",
        linewidth=2,
        label=label
    )

ax.set_xticks(sorted(baseline["fold"].unique()))
ax.set_xlabel("Spatial validation fold")
ax.set_ylabel("Agreement with JRC labels (%)")
ax.set_title("Baseline Random Forest Performance Across Spatial Folds")
ax.legend()
ax.grid(alpha=0.3)
save("02_baseline_fold_performance.png")

# ---------------------------------------------------------
# FIGURE 3: FEATURE-GROUP ABLATION
# ---------------------------------------------------------
group_summary = (
    groups.groupby("experiment")["f1"]
    .agg(["mean", "std"])
    .sort_index()
)

group_labels = {
    "A1_S1_only": "Sentinel-1 only",
    "A2_S2_only": "Sentinel-2 bands",
    "A3_S2_indices": "Sentinel-2 + indices",
    "A4_S1_S2_bands": "S1 + S2 bands",
    "A5_all_features": "All 10 features",
}

labels = [
    group_labels.get(x, x)
    for x in group_summary.index
]

fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(labels))

ax.bar(
    x,
    group_summary["mean"] * 100,
    yerr=group_summary["std"] * 100,
    capsize=5,
    alpha=0.85
)

ax.set_xticks(x, labels, rotation=15, ha="right")
ax.set_ylabel("Mean F1-score (%)")
ax.set_title("Feature-Group Ablation: Five Spatial Folds")
ax.set_ylim(90, 98)
ax.grid(axis="y", alpha=0.25)

for i, value in enumerate(group_summary["mean"] * 100):
    ax.text(i, value + 0.25, f"{value:.2f}%",
            ha="center", fontsize=10)

save("03_feature_group_ablation.png")

# ---------------------------------------------------------
# FIGURE 4: INDIVIDUAL-FEATURE REMOVAL EFFECT
# ---------------------------------------------------------
feature_summary = (
    individual.groupby("experiment")["f1"]
    .mean()
)

base_f1 = feature_summary["B0_all_7_features"]

removals = feature_summary.drop(
    "B0_all_7_features"
)

# Positive means removing the feature reduced F1.
impact = (base_f1 - removals) * 100

impact.index = [
    name.replace("B_remove_", "")
    for name in impact.index
]

impact = impact.sort_values()

fig, ax = plt.subplots(figsize=(9, 5))

ax.barh(impact.index, impact.values)
ax.axvline(0, color="black", linewidth=1)

ax.set_xlabel("F1 decrease after feature removal (percentage points)")
ax.set_ylabel("Removed feature")
ax.set_title("Leave-One-Feature-Out Ablation\n"
             "Seven-Feature Multisensor Baseline")
ax.grid(axis="x", alpha=0.25)

for i, value in enumerate(impact.values):
    ax.annotate(
        f"{value:+.3f}",
        (value, i),
        xytext=(5 if value >= 0 else -5, 0),
        textcoords="offset points",
        ha="left" if value >= 0 else "right",
        va="center"
    )

save("04_individual_feature_ablation.png")

# ---------------------------------------------------------
# FIGURE 5: TRAINING-DATA SENSITIVITY
# ---------------------------------------------------------
size_summary = (
    sizes.groupby("train_samples")["f1"]
    .agg(["mean", "std"])
    .sort_index()
)

fig, ax = plt.subplots(figsize=(9, 5))

ax.errorbar(
    size_summary.index,
    size_summary["mean"] * 100,
    yerr=size_summary["std"] * 100,
    fmt="o-",
    capsize=5,
    linewidth=2
)

ax.set_xticks(size_summary.index)
ax.set_xlabel("Total balanced training samples")
ax.set_ylabel("Mean F1-score (%)")
ax.set_title("Random Forest Training-Data Sensitivity\n"
             "Five Spatial Folds")
ax.grid(alpha=0.3)

for x, row in size_summary.iterrows():
    ax.annotate(
        f"{row['mean'] * 100:.2f}%",
        (x, row["mean"] * 100),
        xytext=(0, 12),
        textcoords="offset points",
        ha="center"
    )

save("05_training_size_sensitivity.png")

print("\nAll five visualizations generated successfully.")
print("Note: Metrics represent agreement with JRC monthly labels.")
