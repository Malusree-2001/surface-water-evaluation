import numpy as np
import rasterio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

jrc_path = "data/reference/monroe_lake_jrc_weak_labels.tif"
rf_path = "results/maps/monroe_rf_water_july2017.tif"
prob_path = "results/maps/monroe_rf_water_probability_july2017.tif"

output = "results/figures/monroe_rf_jrc_disagreement_july2017.png"

with rasterio.open(jrc_path) as jrc_src, \
     rasterio.open(rf_path) as rf_src, \
     rasterio.open(prob_path) as prob_src:

    assert jrc_src.shape == rf_src.shape == prob_src.shape
    assert jrc_src.crs == rf_src.crs == prob_src.crs
    assert jrc_src.transform == rf_src.transform == prob_src.transform

    jrc = jrc_src.read(1)
    rf = rf_src.read(1)
    prob = prob_src.read(1)

valid = np.isfinite(prob) & np.isin(rf, [0, 1])

# Classification categories
# 0 = RF land and JRC land
# 1 = RF water and JRC water
# 2 = RF water and JRC land
# 3 = RF land and JRC water
# 4 = RF water and JRC unclassified
# 5 = RF land and JRC unclassified
# 6 = Missing RF data

comparison = np.full(jrc.shape, 6, dtype=np.uint8)

comparison[valid & (rf == 0) & (jrc == 0)] = 0
comparison[valid & (rf == 1) & (jrc == 1)] = 1
comparison[valid & (rf == 1) & (jrc == 0)] = 2
comparison[valid & (rf == 0) & (jrc == 1)] = 3
comparison[valid & (rf == 1) & (jrc == 255)] = 4
comparison[valid & (rf == 0) & (jrc == 255)] = 5

colors = [
    "#E6D8B8",  # Land agreement
    "#2166AC",  # Water agreement
    "#D73027",  # RF water / JRC land
    "#FDAE61",  # RF land / JRC water
    "#762A83",  # RF water / JRC unknown
    "#AAAAAA",  # RF land / JRC unknown
    "#FFFFFF",  # Missing
]

labels = [
    "Both land",
    "Both water",
    "RF water / JRC land",
    "RF land / JRC water",
    "RF water / JRC unclassified",
    "RF land / JRC unclassified",
    "Missing RF data",
]

cmap = ListedColormap(colors)
norm = BoundaryNorm(np.arange(-0.5, 7.5, 1), cmap.N)

fig, ax = plt.subplots(figsize=(12, 9))

ax.imshow(comparison, cmap=cmap, norm=norm)

ax.set_title(
    "Monroe Lake — Random Forest vs JRC\n"
    "Spatial Disagreement Analysis | July 2017 | 20 m",
    fontsize=15
)

ax.set_xticks([])
ax.set_yticks([])

legend = [
    Patch(facecolor=color, label=label)
    for color, label in zip(colors, labels)
]

ax.legend(
    handles=legend,
    loc="upper left",
    bbox_to_anchor=(1.02, 1),
    frameon=True
)

plt.tight_layout()
plt.savefig(output, dpi=250, bbox_inches="tight")
plt.close()

print("Saved:", output)

print("\n=== PIXEL COUNTS ===")
for code, label in enumerate(labels):
    count = np.count_nonzero(comparison == code)
    print(f"{label}: {count:,}")
