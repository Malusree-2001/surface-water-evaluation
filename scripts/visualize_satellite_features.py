from pathlib import Path

import numpy as np
import rasterio

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

# --------------------------------------------------
# FILES
# --------------------------------------------------
input_path = Path(
    "data/processed/monroe_lake_fused_features_july2017.tif"
)

output_dir = Path("results/visualizations")
output_dir.mkdir(parents=True, exist_ok=True)

output_path = output_dir / "07_satellite_feature_maps.png"

# --------------------------------------------------
# LOAD RASTER
# --------------------------------------------------
with rasterio.open(input_path) as src:
    data = src.read()
    names = list(src.descriptions)
    bounds = src.bounds
    crs = src.crs
    resolution = src.res

bands = {
    name: data[i].astype(float)
    for i, name in enumerate(names)
}

valid = np.all(np.isfinite(data[:10]), axis=0)

extent = [
    bounds.left,
    bounds.right,
    bounds.bottom,
    bounds.top,
]

# --------------------------------------------------
# RGB COMPOSITE
# --------------------------------------------------
rgb_bands = ["B4", "B3", "B2"]

rgb = np.zeros(
    (*valid.shape, 3),
    dtype=float
)

for channel, name in enumerate(rgb_bands):
    values = bands[name]

    low, high = np.percentile(
        values[valid],
        [2, 98]
    )

    rgb[:, :, channel] = np.clip(
        (values - low) / (high - low),
        0,
        1
    )

# Invalid pixels appear light gray.
rgb[~valid] = [0.92, 0.92, 0.92]

# --------------------------------------------------
# CREATE FIGURE
# --------------------------------------------------
fig, axes = plt.subplots(
    2,
    3,
    figsize=(17, 11),
    constrained_layout=True
)

fig.suptitle(
    "Monroe Lake, Indiana — Multisensor Satellite Features\n"
    "July 2017 | 20 m Aligned Raster Grid",
    fontsize=17,
    fontweight="bold"
)

# Panel 1: RGB
axes[0, 0].imshow(
    rgb,
    extent=extent,
    origin="upper"
)

axes[0, 0].set_title(
    "(a) Sentinel-2 RGB (B4/B3/B2)"
)

# Remaining panels
panels = [
    ("VV", "gray", "(b) Sentinel-1 VV"),
    ("VH", "gray", "(c) Sentinel-1 VH"),
    ("NDWI", "BrBG", "(d) NDWI"),
    ("MNDWI", "BrBG", "(e) MNDWI"),
    ("NDVI", "RdYlGn", "(f) NDVI"),
]

for ax, (name, cmap, title) in zip(
    [
        axes[0, 1],
        axes[0, 2],
        axes[1, 0],
        axes[1, 1],
        axes[1, 2],
    ],
    panels
):
    values = np.ma.masked_invalid(bands[name])

    low, high = np.percentile(
        bands[name][valid],
        [2, 98]
    )

    im = ax.imshow(
        values,
        cmap=cmap,
        vmin=low,
        vmax=high,
        extent=extent,
        origin="upper"
    )

    ax.set_title(title)

    cbar = fig.colorbar(
        im,
        ax=ax,
        shrink=0.78
    )

    if name in ("VV", "VH"):
        cbar.set_label("Backscatter (stored values)")
    else:
        cbar.set_label("Index value")

for ax in axes.flat:
    ax.set_xlabel("UTM Easting (m)")
    ax.set_ylabel("UTM Northing (m)")
    ax.ticklabel_format(
        style="plain",
        useOffset=False
    )

fig.text(
    0.5,
    0.005,
    f"CRS: {crs} | Pixel size: {resolution[0]:g} m | "
    "Display stretches: 2nd–98th percentile | "
    "Gray indicates missing data",
    ha="center",
    fontsize=10
)

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)

print("=== SATELLITE FEATURE VISUALIZATION ===")
print("Raster dimensions:", valid.shape)
print("Valid feature pixels:", int(valid.sum()))
print("Coordinate system:", crs)
print("Resolution:", resolution)
print("Output:", output_path)
print("Exists:", output_path.exists())
print("Size (MB):", round(output_path.stat().st_size / 1048576, 2))
