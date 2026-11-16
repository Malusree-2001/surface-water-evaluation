import ee

# Connect to Earth Engine
ee.Initialize(project='class-project-487115')

# Reservoir 1 location
point = ee.Geometry.Point([-86.12402, 38.00545])

# Small test area around the reservoir
region = point.buffer(500).bounds()

# Select the July 2, 2017 Sentinel-2 image
image = ee.Image(
    'COPERNICUS/S2_HARMONIZED/'
    '20170702T163319_20170702T163720_T16SEH'
)

# Select four 10-meter spectral bands
image = image.select(['B2', 'B3', 'B4', 'B8'])

# Export as a GeoTIFF to Google Drive
task = ee.batch.Export.image.toDrive(
    image=image,
    description='reservoir1_sentinel2_20170702',
    folder='Indiana_Surface_Water',
    fileNamePrefix='reservoir1_sentinel2_20170702',
    region=region,
    scale=10,
    crs='EPSG:32616',
    fileFormat='GeoTIFF',
    maxPixels=10000000
)

task.start()

print("Export submitted successfully.")
print("Task ID:", task.id)
print("Initial task status:", task.status()['state'])
