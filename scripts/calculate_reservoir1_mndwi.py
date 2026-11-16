import numpy as np
from osgeo import gdal

# Input satellite rasters
rgb_path = "data/raw/sentinel2/reservoir1_sentinel2_20170702.tif"
swir_path = "data/processed/reservoir1_B11_aligned_10m.tif"

# Output MNDWI raster
output_path = "data/processed/reservoir1_MNDWI_20170702.tif"

# Open both GeoTIFF files
rgb = gdal.Open(rgb_path)
swir = gdal.Open(swir_path)

if rgb is None or swir is None:
    raise RuntimeError("Could not open one or both input rasters.")

# Confirm the pixel grids match
assert rgb.RasterXSize == swir.RasterXSize
assert rgb.RasterYSize == swir.RasterYSize
assert rgb.GetGeoTransform() == swir.GetGeoTransform()
assert rgb.GetProjection() == swir.GetProjection()

# Original GeoTIFF Band 2 = Sentinel-2 B3 (Green)
green = rgb.GetRasterBand(2).ReadAsArray().astype(np.float32)

# Aligned GeoTIFF Band 1 = Sentinel-2 B11 (SWIR)
swir_values = swir.GetRasterBand(1).ReadAsArray().astype(np.float32)

# Identify invalid or missing observations
# Sentinel-2 values of zero are treated as invalid here.
valid = (
    np.isfinite(green)
    & np.isfinite(swir_values)
    & (green > 0)
    & (swir_values > 0)
)

# Initialize the output with NoData
mndwi = np.full(green.shape, -9999.0, dtype=np.float32)

# Calculate MNDWI only for valid pixels
mndwi[valid] = (
    (green[valid] - swir_values[valid])
    / (green[valid] + swir_values[valid])
)

# Create a new Float32 GeoTIFF
driver = gdal.GetDriverByName("GTiff")
output = driver.Create(
    output_path,
    rgb.RasterXSize,
    rgb.RasterYSize,
    1,
    gdal.GDT_Float32,
    options=["COMPRESS=LZW"]
)

# Preserve spatial referencing
output.SetGeoTransform(rgb.GetGeoTransform())
output.SetProjection(rgb.GetProjection())

band = output.GetRasterBand(1)
band.WriteArray(mndwi)
band.SetNoDataValue(-9999)
band.SetDescription("MNDWI")
band.FlushCache()

output = None

# Print results for verification
print("MNDWI raster created:", output_path)
print("Raster dimensions:", mndwi.shape)
print("Valid pixels:", np.count_nonzero(valid))
print("Invalid pixels:", np.count_nonzero(~valid))

if np.any(valid):
    print("Minimum MNDWI:", float(np.min(mndwi[valid])))
    print("Maximum MNDWI:", float(np.max(mndwi[valid])))
    print("Mean MNDWI:", float(np.mean(mndwi[valid])))
