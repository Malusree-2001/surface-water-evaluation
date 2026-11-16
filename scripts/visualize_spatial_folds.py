from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch

# --------------------------------------------------
# INPUT FILES
# --------------------------------------------------
fold_csv = Path(
    "results/inventory/monroe_monthly_jrc_spatial_folds_5.csv"
)

reference_tif = Path(
    "data/reference/monroe_lake_jrc_monthly_july2017.tif"
)

output_dir = Path("results/visualizations")
output_dir.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# LOAD SPATIAL FOLD ASSIGNMENTS
# --------------------------------------------------
df = pd.read_csv(fold_csv)

assert len(df) == 99
assert df["fold"].between(0, 4).all()
assert not df.duplicated(["block_x", "block_y"]).any()

# --------------------------------------------------
# LOAD RASTER GRID
# --------------------------------------------------
with rasterio.open(reference_tif) as src:
    labels = src.read(1)
    transform = src.transform
    height = src.height
    width = src.width

# Each block is 2,000 meters.
block_size = 2000

# Coordinates of pixel centers.
rows, cols = np.indices((height, width))

xs, ys = rasterio.transform.xy(
    transform, rows, cols, offset="center"
)

xs = np.asarray(xs).reshape(height, width)
ys = np.asarray(ys).reshape(height, width)

# Convert geographic coordinates to block indices.
block_x = np.floor(xs / block_size).astype(int)
block_y = np.floor(ys / block_size).astype(int)

# --------------------------------------------------
# LOAD FEATURE VALIDITY MASK
# --------------------------------------------------
feature_path = (
    "data/processed/monroe_lake_fused_features_july2017.tif"
)

with rasterio.open(feature_path) as src:
    features = src.read()

    assert src.crs == rasterio.crs.CRS.from_epsg(32616)
    assert src.height == height
    assert src.width == width
    assert src.transform == transform

    # First 10 bands are predictors.
    # Band 11 is valid_obs.
    feature_valid = (
        np.all(np.isfinite(features[:10]), axis=0)
        & np.isfinite(features[10])
        & (features[10] > 0)
    )

# --------------------------------------------------
# RECONSTRUCT THE SPATIAL FOLD RASTER
# --------------------------------------------------
fold_map = np.full((height, width), np.nan)

for row in df.itertuples():
    mask = (
        (block_x == row.block_x) &
        (block_y == row.block_y) &
        np.isin(labels, [0, 1]) &
        feature_valid
    )

    fold_map[mask] = row.fold

# --------------------------------------------------
# VISUALIZATION
# --------------------------------------------------
colors = [
    "#4477AA",
    "#EE6677",
    "#228833",
    "#CCBB44",
    "#AA3377",
]

cmap = ListedColormap(colors)
cmap.set_bad("#eeeeee")

norm = BoundaryNorm(
    np.arange(-0.5, 5.5, 1),
    cmap.N
)

fig, ax = plt.subplots(figsize=(11, 8))

ax.imshow(
    fold_map,
    cmap=cmap,
    norm=norm,
    interpolation="nearest"
)

ax.set_title(
    "Monroe Lake — Five-Fold Spatial Cross-Validation\n"
    "2 km Blocks | July 2017",
    fontsize=15
)

ax.set_xlabel("Raster column")
ax.set_ylabel("Raster row")

legend = [
    Patch(facecolor=colors[i], label=f"Fold {i}")
    for i in range(5)
]

ax.legend(
    handles=legend,
    loc="upper right",
    framealpha=0.95
)

plt.tight_layout()

output = output_dir / "06_spatial_cross_validation_folds.png"

plt.savefig(
    output,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# --------------------------------------------------
# VERIFICATION
# --------------------------------------------------
print("\n=== SPATIAL FOLD MAP VERIFICATION ===")

print("Blocks:", len(df))

for fold in range(5):
    count = np.sum(fold_map == fold)
    print(f"Fold {fold}: {count:,} pixels")

print("Mapped pixels:", np.isfinite(fold_map).sum())
print("JRC labeled pixels:", np.isin(labels, [0, 1]).sum())

print("\nSaved:", output)
