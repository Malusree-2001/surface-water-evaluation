from osgeo import gdal
import numpy as np
from pathlib import Path

gdal.UseExceptions()

# Input: five-band Sentinel-2 GeoTIFF
input_path = Path(
    "data/raw/sentinel2/monroe_lake_s2_20170702.tif"
)

# Output: calculated MNDWI raster
output_path = Path(
    "data/processed/monroe_lake_MNDWI_20170702.tif"
)

if not input_path.exists():
    raise FileNotFoundError(
        f"Sentinel-2 export not found: {input_path}"
    )

ds = gdal.Open(str(input_path))

# Export band order:
# 1=B2, 2=B3, 3=B4, 4=B8, 5=B11
green_band = ds.GetRasterBand(2)
swir_band = ds.GetRasterBand(5)

green = green_band.ReadAsArray().astype(np.float32)
swir = swir_band.ReadAsArray().astype(np.float32)

# Preserve source validity masks.
valid = (
    (green_band.GetMaskBand().ReadAsArray() != 0)
    & (swir_band.GetMaskBand().ReadAsArray() != 0)
    & np.isfinite(green)
    & np.isfinite(swir)
    & ((green + swir) != 0)
)

mndwi = np.full(green.shape, -9999, dtype=np.float32)

mndwi[valid] = (
    (green[valid] - swir[valid])
    / (green[valid] + swir[valid])
)

output_path.parent.mkdir(parents=True, exist_ok=True)

driver = gdal.GetDriverByName("GTiff")
out = driver.Create(
    str(output_path),
    ds.RasterXSize,
    ds.RasterYSize,
    1,
    gdal.GDT_Float32,
    options=["COMPRESS=LZW"]
)

out.SetGeoTransform(ds.GetGeoTransform())
out.SetProjection(ds.GetProjection())

band = out.GetRasterBand(1)
band.WriteArray(mndwi)
band.SetNoDataValue(-9999)
band.FlushCache()

out = None
ds = None

print("MNDWI raster:", output_path)
print("Valid pixels:", int(valid.sum()))
print("Invalid pixels:", int((~valid).sum()))

if valid.any():
    print("Minimum:", float(mndwi[valid].min()))
    print("Maximum:", float(mndwi[valid].max()))
    print("Mean:", float(mndwi[valid].mean()))
