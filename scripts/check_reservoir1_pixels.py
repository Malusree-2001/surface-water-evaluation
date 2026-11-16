from osgeo import ogr, osr

# Official NHD polygon dataset
path = "data/reference/hydrography/waterbody_sample_5.geojson"

# Open the GeoJSON
dataset = ogr.Open(path)

if dataset is None:
    raise RuntimeError("Could not open the NHD GeoJSON.")

layer = dataset.GetLayer()

# Find Reservoir 1 using its official objectid
reservoir = None

for feature in layer:
    if int(feature.GetField("objectid")) == 1:
        reservoir = feature.GetGeometryRef().Clone()
        break

if reservoir is None:
    raise RuntimeError("Reservoir 1 was not found.")

# Coordinates reported by QGIS Identify Features
# Format: (longitude, latitude)
points = {
    "Pixel 1": (-86.1239986, 38.0055548),
    "Pixel 2": (-86.1240245, 38.0054698),
}

print("Reservoir objectid: 1")

for name, (lon, lat) in points.items():
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint_2D(lon, lat)

    inside = bool(reservoir.Contains(point))
    touching = bool(reservoir.Touches(point))

    if inside:
        status = "INSIDE"
    elif touching:
        status = "ON BOUNDARY"
    else:
        status = "OUTSIDE"

    print(f"{name}: {status}")
    print(f"  Longitude: {lon}")
    print(f"  Latitude: {lat}")

dataset = None
