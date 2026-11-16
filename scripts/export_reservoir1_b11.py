import ee

# Initialize Google Earth Engine
ee.Initialize(project='class-project-487115')

# Same reservoir center used in the earlier export
point = ee.Geometry.Point([-86.12402, 38.00545])

# Same approximate 1 km x 1 km inspection area
region = point.buffer(500).bounds()

# Retrieve the same historical Sentinel-2 scene
image = ee.Image(
    'COPERNICUS/S2_HARMONIZED/'
    '20170702T163319_20170702T163720_T16SEH'
)

# Select only B11 (shortwave infrared)
b11 = image.select('B11')

# Export B11 at its native 20 m resolution
task = ee.batch.Export.image.toDrive(
    image=b11,
    description='reservoir1_B11_20170702',
    folder='Indiana_Surface_Water',
    fileNamePrefix='reservoir1_B11_20170702',
    region=region,
    scale=20,
    crs='EPSG:32616',
    fileFormat='GeoTIFF',
    maxPixels=1000000
)

task.start()

print("B11 export submitted.")
print("Task ID:", task.id)
print("Initial status:", task.status()['state'])
