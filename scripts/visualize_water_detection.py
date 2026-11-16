from pathlib import Path

import numpy as np
import rasterio

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

# --------------------------------------------------
# INPUTS
# --------------------------------------------------
reference_path = (
    "data/reference/monroe_lake_jrc_monthly_july2017.tif"
)

prediction_path = (
    "results/maps/monroe_rf_water_july2017.tif"
)

probability_path = (
    "results/maps/monroe_rf_water_probability_july2017.tif"
)

output_dir = Path("results/visualizations")
output_dir.mkdir(parents=True, exist_ok=True)

output_path = output_dir / "08_water_detection_comparison.png"

# --------------------------------------------------
# LOAD AND VERIFY RASTERS
# --------------------------------------------------
with rasterio.open(reference_path) as src:
    reference = src.read(1)
    transform = src.transform
    crs = src.crs
    bounds = src.bounds
    shape = reference.shape

with rasterio.open(prediction_path) as src:
    assert src.crs == crs
    assert src.transform == transform
    assert src.read(1).shape == shape

    prediction = src.read(1)

with rasterio.open(probability_path) as src:
    assert src.crs == crs
    assert src.transform == transform
    assert src.read(1).shape == shape

    probability = src.read(1)

extent = [
    bounds.left,
    bounds.right,
    bounds.bottom,
    bounds.top
]

# --------------------------------------------------
# VALIDITY MASKS
# --------------------------------------------------
reference_valid = np.isin(reference, [0, 1])
prediction_valid = np.isin(prediction, [0, 1])
probability_valid = np.isfinite(probability)

common_valid = (
    reference_valid &
    prediction_valid &
    probability_valid
)

# --------------------------------------------------
# PREPARE REFERENCE AND PREDICTION MAPS
# --------------------------------------------------
reference_map = np.ma.masked_where(
    ~reference_valid,
    reference.astype(float)
)

prediction_map = np.ma.masked_where(
    ~prediction_valid,
    prediction.astype(float)
)

probability_map = np.ma.masked_where(
    ~probability_valid,
    probability.astype(float)
)

binary_cmap = ListedColormap([
    "#eeeeee",
    "#1764ab"
])
binary_cmap.set_bad("#ffffff")

# --------------------------------------------------
# AGREEMENT CATEGORIES
# --------------------------------------------------
# 0 = TN
# 1 = TP
# 2 = FP
# 3 = FN

agreement = np.full(
    shape,
    np.nan,
    dtype=float
)

tn = common_valid & (reference == 0) & (prediction == 0)
tp = common_valid & (reference == 1) & (prediction == 1)
fp = common_valid & (reference == 0) & (prediction == 1)
fn = common_valid & (reference == 1) & (prediction == 0)

agreement[tn] = 0
agreement[tp] = 1
agreement[fp] = 2
agreement[fn] = 3

agreement_cmap = ListedColormap([
    "#eeeeee",
    "#1764ab",
    "#e66101",
    "#d01c8b"
])
agreement_cmap.set_bad("#ffffff")

# --------------------------------------------------
# CREATE FIGURE
# --------------------------------------------------
fig, axes = plt.subplots(
    2, 2,
    figsize=(15, 12),
    constrained_layout=True
)

fig.suptitle(
    "Monroe Lake — Surface Water Detection Comparison\n"
    "July 2017 | JRC Reference and Saved Random Forest Predictions",
    fontsize=16,
    fontweight="bold"
)

# JRC
axes[0, 0].imshow(
    reference_map,
    cmap=binary_cmap,
    vmin=-0.5,
    vmax=1.5,
    extent=extent,
    origin="upper",
    interpolation="nearest"
)
axes[0, 0].set_title("(a) JRC Monthly Reference")

# Probability
im = axes[0, 1].imshow(
    probability_map,
    cmap="Blues",
    vmin=0,
    vmax=1,
    extent=extent,
    origin="upper",
    interpolation="nearest"
)
axes[0, 1].set_title("(b) RF Water Probability")

cbar = fig.colorbar(
    im,
    ax=axes[0, 1],
    shrink=0.8
)
cbar.set_label("Predicted water probability")

# Classification
axes[1, 0].imshow(
    prediction_map,
    cmap=binary_cmap,
    vmin=-0.5,
    vmax=1.5,
    extent=extent,
    origin="upper",
    interpolation="nearest"
)
axes[1, 0].set_title("(c) RF Binary Classification")

# Agreement
axes[1, 1].imshow(
    np.ma.masked_invalid(agreement),
    cmap=agreement_cmap,
    vmin=-0.5,
    vmax=3.5,
    extent=extent,
    origin="upper",
    interpolation="nearest"
)
axes[1, 1].set_title("(d) RF–JRC Agreement and Disagreement")

legend = [
    Patch(facecolor="#eeeeee", label="TN: land agreement"),
    Patch(facecolor="#1764ab", label="TP: water agreement"),
    Patch(facecolor="#e66101", label="FP: RF water / JRC land"),
    Patch(facecolor="#d01c8b", label="FN: RF land / JRC water")
]

axes[1, 1].legend(
    handles=legend,
    loc="upper right",
    fontsize=8,
    framealpha=0.95
)

for ax in axes.flat:
    ax.set_xlabel("UTM Easting (m)")
    ax.set_ylabel("UTM Northing (m)")
    ax.ticklabel_format(style="plain", useOffset=False)

fig.text(
    0.5,
    0.005,
    "Descriptive comparison of saved prediction rasters against "
    "JRC reference labels. Out-of-fold status of saved maps is "
    "not established. This is not independent accuracy validation.",
    ha="center",
    fontsize=10
)

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)

# --------------------------------------------------
# VERIFICATION
# --------------------------------------------------
print("\n=== WATER DETECTION MAP VERIFICATION ===")

print("Reference valid pixels:", int(reference_valid.sum()))
print("Prediction valid pixels:", int(prediction_valid.sum()))
print("Common valid pixels:", int(common_valid.sum()))

print("\nAgreement counts:")
print("TN:", int(tn.sum()))
print("FP:", int(fp.sum()))
print("FN:", int(fn.sum()))
print("TP:", int(tp.sum()))

print("\nOutput:", output_path)
print("Exists:", output_path.exists())
print(
    "Size (MB):",
    round(output_path.stat().st_size / 1048576, 2)
)
