import ee
import numpy as np
import rasterio
import requests
from rasterio.io import MemoryFile
from rasterio.enums import Resampling
from rasterio.warp import reproject

ee.Initialize()

feature_path = "data/processed/monroe_lake_fused_features_july2017.tif"
output_path = "data/reference/monroe_lake_jrc_monthly_july2017.tif"

# Read the target grid from our existing Sentinel feature raster.
with rasterio.open(feature_path) as src:
    target_crs = src.crs
    target_transform = src.transform
    target_width = src.width
    target_height = src.height
    bounds = src.bounds
    profile = src.profile.copy()

# Select the exact July 2017 monthly JRC image.
monthly = (
    ee.ImageCollection("JRC/GSW1_4/MonthlyHistory")
    .filterDate("2017-07-01", "2017-08-01")
    .first()
)

monthly = ee.Image(monthly).select("water").unmask(0).toUint8()

# Define the study-area bounding rectangle in the target CRS.
region = ee.Geometry.Rectangle(
    [bounds.left, bounds.bottom, bounds.right, bounds.top],
    proj=target_crs.to_string(),
    geodesic=False,
)

# Download the categorical raster at its native approximate resolution.
url = monthly.getDownloadURL({
    "region": region,
    "scale": 30,
    "format": "GEO_TIFF",
})

response = requests.get(url, timeout=180)
response.raise_for_status()

# Read the downloaded raster in memory.
with MemoryFile(response.content) as memfile:
    with memfile.open() as source:
        source_data = source.read(1)
        source_crs = source.crs
        source_transform = source.transform

# Align JRC classes to the existing 20 m Sentinel grid.
aligned = np.zeros(
    (target_height, target_width),
    dtype=np.uint8,
)

reproject(
    source=source_data,
    destination=aligned,
    src_transform=source_transform,
    src_crs=source_crs,
    dst_transform=target_transform,
    dst_crs=target_crs,
    src_nodata=None,
    dst_nodata=None,
    resampling=Resampling.nearest,
)

# JRC Monthly History:
# 0 = no data, 1 = land, 2 = water
#
# Random Forest labels:
# 255 = uncertain/no data, 0 = land, 1 = water
labels = np.full(aligned.shape, 255, dtype=np.uint8)
labels[aligned == 1] = 0
labels[aligned == 2] = 1

# Save the label raster.
profile.update(
    driver="GTiff",
    count=1,
    dtype="uint8",
    nodata=255,
    compress="lzw",
)

with rasterio.open(output_path, "w", **profile) as dst:
    dst.write(labels, 1)
    dst.set_band_description(1, "jrc_monthly_july2017_label")
    dst.update_tags(
        source="JRC/GSW1_4/MonthlyHistory",
        source_image="2017_07",
        label_0="land",
        label_1="water",
        label_255="no_data",
        resampling="nearest",
    )

unique, counts = np.unique(labels, return_counts=True)

print("=== JRC MONTHLY EXPORT COMPLETE ===")
print("Output:", output_path)
print("CRS:", target_crs)
print("Dimensions:", target_width, "x", target_height)
print("Class counts:", dict(zip(unique.tolist(), counts.tolist())))
print("Total pixels:", int(counts.sum()))
