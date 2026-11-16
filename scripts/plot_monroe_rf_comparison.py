import numpy as np
import rasterio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from pathlib import Path

BASE = Path(".")

JRC_PATH = BASE / "data/reference/monroe_lake_jrc_weak_labels.tif"
MNDWI_PATH = BASE / "data/processed/monroe_lake_MNDWI_20170702.tif"
RF_PATH = BASE / "results/maps/monroe_rf_water_july2017.tif"
PROB_PATH = BASE / "results/maps/monroe_rf_water_probability_july2017.tif"

OUTPUT = BASE / "results/figures/monroe_rf_comparison_july2017.png"

def read_raster(path):
    with rasterio.open(path) as src:
        return src.read(1), src.transform, src.crs

jrc, jrc_transform, jrc_crs = read_raster(JRC_PATH)
mndwi, mndwi_transform, mndwi_crs = read_raster(MNDWI_PATH)
rf, rf_transform, rf_crs = read_raster(RF_PATH)
prob, prob_transform, prob_crs = read_raster(PROB_PATH)

# Verify geographic alignment before comparing pixel values.
assert jrc.shape == mndwi.shape == rf.shape == prob.shape
assert jrc_transform == mndwi_transform == rf_transform == prob_transform
assert jrc_crs == mndwi_crs == rf_crs == prob_crs

# JRC: 0=land, 1=water, 255=unclassified.
# Display unclassified pixels in gray.
jrc_display = np.where(jrc == 255, 2, jrc)

# MNDWI threshold baseline.
mndwi_display = np.where(np.isfinite(mndwi), (mndwi > 0).astype(float), np.nan)

# RF binary output. Restrict display to pixels with valid probabilities.
rf_display = np.where(np.isfinite(prob), rf, np.nan)

# Plotting colors: land, water, unclassified.
class_cmap = ListedColormap(["#E6D8B8", "#2166AC", "#AAAAAA"])
class_norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5], class_cmap.N)

binary_cmap = ListedColormap(["#E6D8B8", "#2166AC"])
binary_cmap.set_bad("#AAAAAA")
binary_norm = BoundaryNorm([-0.5, 0.5, 1.5], binary_cmap.N)

fig, axes = plt.subplots(2, 2, figsize=(13, 10))

axes[0, 0].imshow(jrc_display, cmap=class_cmap, norm=class_norm)
axes[0, 0].set_title("A. JRC Provisional Reference Labels")

axes[0, 1].imshow(mndwi_display, cmap=binary_cmap, norm=binary_norm)
axes[0, 1].set_title("B. MNDWI > 0")

axes[1, 0].imshow(rf_display, cmap=binary_cmap, norm=binary_norm)
axes[1, 0].set_title("C. Random Forest Classification")

im = axes[1, 1].imshow(
    np.ma.masked_invalid(prob),
    cmap="Blues",
    vmin=0,
    vmax=1
)
axes[1, 1].set_title("D. Random Forest Water Probability")

fig.colorbar(
    im,
    ax=axes[1, 1],
    fraction=0.046,
    pad=0.04,
    label="Model water-class probability"
)

for ax in axes.flat:
    ax.set_xticks([])
    ax.set_yticks([])

fig.suptitle(
    "Monroe Lake Surface Water Detection — July 2017\n"
    "Sentinel-1 + Sentinel-2 | 20 m Resolution",
    fontsize=15
)

plt.tight_layout()
plt.savefig(OUTPUT, dpi=250, bbox_inches="tight")
plt.close()

print("Figure saved:", OUTPUT)
