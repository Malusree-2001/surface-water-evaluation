
## 2026-10-21 — Indiana Hydrography Inventory

### Objective
Identify the number and types of officially mapped
waterbody polygons in Indiana before selecting
training and validation samples.

### Data source
Indiana Local-Resolution NHD Waterbody Layer
https://gisdata.in.gov/server/rest/services/Hosted/NHD_Local_Resolution_RO/FeatureServer/1

### Method
1. Queried the ArcGIS FeatureServer for total records.
2. Queried grouped feature counts using ftype.
3. Saved the JSON responses on Big Red 200.

### Results
Total polygons: 186,689
Lake/Pond (390): 163,489
Reservoir (436): 3,662
Swamp/Marsh (466): 19,538

### Evidence
results/inventory/waterbody_count.json
results/inventory/waterbody_types.json

### Interpretation
These are mapped polygon records, not confirmed
2017 water pixels or independent waterbodies.
Wetlands require separate evaluation.
River geometries still need to be inventoried.

### Errors
None reported for these two queries.

### Next step
Inspect the dataset schema and geometry metadata
before downloading polygon records.


## Step 5 — Download Five Waterbody Polygons

### Objective
Test downloading real polygon geometries and
attributes from the official Indiana NHD service.

### Exact download command
curl -L --fail --silent --show-error --get \
  "https://gisdata.in.gov/server/rest/services/Hosted/NHD_Local_Resolution_RO/FeatureServer/1/query" \
  --data-urlencode "where=1=1" \
  --data-urlencode "outFields=*" \
  --data-urlencode "returnGeometry=true" \
  --data-urlencode "orderByFields=objectid ASC" \
  --data-urlencode "resultRecordCount=5" \
  --data-urlencode "f=geojson" \
  -o data/reference/hydrography/waterbody_sample_5.geojson

### Verification command
python - <<'PYTHON'
import json

path = "data/reference/hydrography/waterbody_sample_5.geojson"

with open(path) as f:
    data = json.load(f)

if "error" in data:
    print("SERVER ERROR:", data["error"])
else:
    print("Format:", data.get("type"))
    features = data.get("features", [])
    print("Number of polygons:", len(features))

    for feature in features:
        p = feature.get("properties", {})
        g = feature.get("geometry") or {}
        print(
            "ID:", p.get("objectid"),
            "| Name:", p.get("gnis_name"),
            "| Area (km²):", p.get("areasqkm"),
            "| Geometry:", g.get("type")
        )
PYTHON

### Actual output
Format: FeatureCollection
Number of polygons: 5
ID 1: unnamed, 0.002 km2, Polygon
ID 2: unnamed, 0.00078175 km2, Polygon
ID 3: unnamed, 0.00063827 km2, Polygon
ID 4: unnamed, 0.001 km2, Polygon
ID 5: unnamed, 0 km2, Polygon

### Interpretation
The download and JSON parsing succeeded.
Small polygons may contain few or no pure 10 m
Sentinel pixels.
The zero-area attribute requires further checking.
These records are not yet verified 2017 water labels.

### Errors
None reported.

### Evidence
data/reference/hydrography/waterbody_sample_5.geojson

### Next step
Inspect polygon coordinates and bounding boxes,
then visualize the locations in QGIS.


## Step 6 — Geographic Coordinate Inspection

### Objective
Identify the geographic locations of five downloaded
waterbody polygons and check their plausibility.

### Command executed
python - <<'PYTHON'
import json

path = "data/reference/hydrography/waterbody_sample_5.geojson"

with open(path) as f:
    data = json.load(f)

for feature in data["features"]:
    props = feature["properties"]
    geom = feature["geometry"]

    def collect_coordinates(obj):
        if isinstance(obj, list):
            if len(obj) >= 2 and all(
                isinstance(v, (int, float)) for v in obj[:2]
            ):
                yield obj[:2]
            else:
                for part in obj:
                    yield from collect_coordinates(part)

    points = list(collect_coordinates(geom["coordinates"]))
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    print(
        f"ID {props['objectid']}: "
        f"Longitude {min(xs):.5f} to {max(xs):.5f}, "
        f"Latitude {min(ys):.5f} to {max(ys):.5f}"
    )
PYTHON

### Actual results
ID 1: -86.12420 to -86.12384; 38.00520 to 38.00570
ID 2: -86.22612 to -86.22575; 39.66555 to 39.66584
ID 3: -86.89541 to -86.89512; 38.89451 to 38.89475
ID 4: -87.85307 to -87.85275; 42.15874 to 42.15898
ID 5: -87.71793 to -87.71769; 42.02235 to 42.02253

### Interpretation
The GeoJSON coordinates are consistent with
longitude/latitude degrees.
Records 4 and 5 appear outside Indiana, in Illinois.
The statewide inventory count may therefore include
features outside the intended study boundary.

### Errors
No command errors.

### Research issue discovered
Need to verify the official layer's geographic coverage
and clip or spatially filter to Indiana before using it.

### Evidence
data/reference/hydrography/waterbody_sample_5.geojson

### Next step
Visualize the polygons in QGIS and confirm their locations.


## Step 7 — QGIS Visual Inspection

### Objective
Load official hydrography polygons and inspect
the geographic location of reservoir Object ID 1.

### QGIS actions
1. Opened Layer > Add Layer > Add Vector Layer.
2. Loaded waterbody_sample_5.geojson.
3. Opened the attribute table.
4. Selected Object ID 1.
5. Zoomed to the selected polygon.
6. Added OpenStreetMap through XYZ Tiles.
7. Changed polygon styling to a transparent fill.
8. Saved the QGIS project.

### Results
Five polygon features loaded successfully.
Object ID 1 was located in an industrial area.
The polygon is classified as a reservoir (ftype 436).
The water status during 2017 remains unverified.

### Troubleshooting
The polygon was initially difficult to see because
of the map scale and yellow selection highlight.
Resolved by zooming to the selected feature,
deselecting it, zooming out, and changing symbology.

### Evidence
data/reference/hydrography/waterbody_sample_5.geojson
data/validation/waterbody_inspection.csv
QGIS project: indiana_waterbody_inspection.qgz

### Next step
Inspect historical Sentinel-2 imagery from
June 1 to September 30, 2017.


## Step 9 — Google Earth Engine Environment Setup

### Objective
Prepare Python to access historical Sentinel-2 imagery
for waterbody verification.

### Initial diagnostic command
python - <<'PYTHON'
try:
    import ee
    print("Earth Engine Python API: INSTALLED")
    print("Version:", ee.__version__)
except ImportError as error:
    print("Earth Engine Python API: NOT INSTALLED")
    print("Error:", error)
PYTHON

### Actual error
Earth Engine Python API: NOT INSTALLED
Error: No module named 'ee'

### Interpretation
The active Python environment did not contain the
Google Earth Engine Python package.

### Proposed resolution
Create a project-specific Python virtual environment
and install earthengine-api.

### Setup commands
module load python/3.12.11
python -m venv .venv
source .venv/bin/activate
python -m pip install earthengine-api
python -c "import ee; print('Earth Engine version:', ee.__version__)"

### Verification status
Pending confirmation of installation output.

### Next step
Authenticate Earth Engine, inspect 2017 Sentinel-2
availability, and prepare imagery for QGIS.


## Step 9B — Earth Engine Installation Completed

### Objective
Install the Earth Engine Python API in an isolated
Python environment on Big Red 200.

### Commands
module load python/3.12.11
python -m venv .venv
source .venv/bin/activate
python -m pip install earthengine-api
python -c "import ee; print('Earth Engine version:', ee.__version__)"

### Verified output
Earth Engine version: 1.7.49

### Result
Earth Engine Python API successfully installed.
The project virtual environment is active.

### Previous error
No module named 'ee'

### Resolution
Installed earthengine-api in the project virtual environment.

### Next step
Check Earth Engine initialization and authentication
before requesting 2017 Sentinel-2 imagery.


## Step 10 — Earth Engine Authentication

### Objective
Initialize Earth Engine on Big Red 200.

### Diagnostic command
python - <<'PYTHON'
import ee

try:
    ee.Initialize()
    print("SUCCESS: Earth Engine initialized")
except Exception as error:
    print("INITIALIZATION FAILED")
    print("Error type:", type(error).__name__)
    print("Message:", str(error))
PYTHON

### Actual result
INITIALIZATION FAILED

Error type:
EEException

Error message:
Please authorize access to your Earth Engine account
by running earthengine authenticate or ee.Authenticate().

### Cause
Earth Engine credentials were not available to the
current Big Red 200 user environment.

### Proposed resolution
earthengine authenticate --auth_mode=notebook

### Resolution status
Pending authentication.

### Next step
Verify Earth Engine initialization with a registered
Google Cloud project, then inspect 2017 Sentinel-2 scenes.


---

# Step 10: Google Earth Engine Installation and Authentication

## 1. Objective

Configure Google Earth Engine (GEE) on Indiana University's
Big Red 200 HPC environment to access historical Sentinel-1
and Sentinel-2 satellite imagery for the Indiana surface-water
detection and temporal dynamics research project.

## 2. Computing Environment

HPC system: IU Big Red 200
Login host: login1
Project directory:
/N/project/persl/indiana_surface_water/anaprad

Python module: python/3.12.11
Virtual environment: .venv
Earth Engine Python API version: 1.7.49
Google Cloud project: class-project-487115

## 3. Initial Package Availability Test

Command:
python -c "import ee; print('Earth Engine version:', ee.__version__)"

Initial result:
ModuleNotFoundError: No module named 'ee'

Interpretation:
The Earth Engine Python API was unavailable in the
initial Python environment.

## 4. Python Environment Setup

Commands:
module load python/3.12.11
python -m venv .venv
source .venv/bin/activate
python -m pip install earthengine-api

Verification command:
python -c "import ee; print('Earth Engine version:', ee.__version__)"

Verified output:
Earth Engine version: 1.7.49

Result:
Earth Engine API installed successfully in the
project-specific Python virtual environment.

## 5. Initial Earth Engine Initialization

Python operation:
import ee
ee.Initialize()

Actual result:
INITIALIZATION FAILED

Error type:
EEException

Error:
Please authorize access to your Earth Engine account
by running earthengine authenticate or ee.Authenticate().

Interpretation:
Earth Engine was installed, but the HPC environment
did not yet have saved Google authorization credentials.

## 6. Authentication Method

Command:
earthengine authenticate --auth_mode=notebook

The command generated an Earth Engine authorization URL.

The URL was opened manually in a browser on the
local Windows computer.

The Google Earth Engine Notebook Authenticator displayed
the selected Google account and Cloud project:

class-project-487115

The user selected GENERATE TOKEN and completed the
Google authorization workflow.

The resulting verification code was entered directly
into the Big Red 200 terminal.

Security:
The verification code, authorization URL, and tokens
were not saved in the research log.

## 7. Authentication Errors and Troubleshooting

Observed error:
Cannot authenticate: Invalid request

Additional terminal errors:
xdg-open: no method available
firefox: command not found
google-chrome: command not found

Cause:
The HPC login environment could not automatically
launch a supported web browser.

Troubleshooting:
1. Initiated a fresh notebook authentication request.
2. Copied the generated authorization URL.
3. Opened it manually in a Windows web browser.
4. Completed Google's authorization workflow.
5. Entered the verification code into the HPC terminal.

## 8. Final Authentication Result

Actual terminal output:
Successfully saved authorization token.

Status:
Authentication token successfully saved.

Important limitation:
Earth Engine API initialization with the selected
Google Cloud project has not yet been verified.

## 9. Next Verification

Initialize Earth Engine using:
ee.Initialize(project='class-project-487115')

Then test access to the historical Sentinel-2 catalog:
COPERNICUS/S2_HARMONIZED

Target imagery period:
2017-06-01 to 2017-09-30

No satellite imagery has been downloaded at this stage.

## 10. Research Relevance

This configuration enables future access to Earth Engine
satellite collections for historical waterbody inspection,
feature extraction, and surface-water classification.

The immediate research objective is to examine 2017
Sentinel-2 imagery for selected official hydrography
features and determine their suitability as training
or validation sites.


---

# Step 11: Earth Engine Connection and Sentinel-2 Availability

## Objective
Verify Earth Engine access from Big Red 200 and determine
whether historical Sentinel-2 imagery is available for
the first candidate waterbody.

## Environment
HPC: Big Red 200
Earth Engine Python API: 1.7.49
Cloud project: class-project-487115

## Test Command

python - <<'PYTHON'
import ee

ee.Initialize(project='class-project-487115')

print("SUCCESS: Earth Engine initialized")

point = ee.Geometry.Point([-86.12402, 38.00545])

images = (
    ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
    .filterBounds(point)
    .filterDate('2017-06-01', '2017-10-01')
)

print("2017 Sentinel-2 images:", images.size().getInfo())
PYTHON

## Actual Output

SUCCESS: Earth Engine initialized
2017 Sentinel-2 images: 11

## Interpretation

1. Google Earth Engine authentication succeeded.
2. Cloud project access was verified.
3. The Sentinel-2 Harmonized collection is accessible.
4. Eleven scenes intersect the selected waterbody location
   during June-September 2017.
5. Cloud coverage and image quality remain unverified.

## Research Implications

Historical Sentinel-2 imagery is available for initial
inspection of the first hydrography candidate.

The official waterbody polygon remains an unverified
reference feature, not confirmed 2017 water ground truth.

## Next Step

Inspect scene acquisition dates, cloud coverage, and
available spectral bands before selecting an image
for GeoTIFF export.

## Download Status

No satellite imagery downloaded yet.


---

# Step 12 — Historical Sentinel-2 Scene Inventory

## Objective
Identify Sentinel-2 scenes covering Reservoir 1 during
June-September 2017 and compare scene-level cloud coverage.

## Source
Google Earth Engine: COPERNICUS/S2_HARMONIZED

## Location
Longitude: -86.12402
Latitude: 38.00545

## Date filter
2017-06-01 to 2017-10-01 (exclusive end)

## Verified results
Total scenes: 11

Lowest reported cloud coverage:
2017-07-02: 1.20%
2017-09-20: 3.82%
2017-07-07: 15.07%

Full scene inventory:
results/inventory/reservoir1_sentinel2_2017.csv

## Initial selection
2017-07-02
Image ID:
20170702T163319_20170702T163720_T16SEH

## Selection rationale
This image has the lowest scene-level cloud coverage
among the 11 scenes returned for the study period.

## Limitations
Cloud percentages describe the satellite scene,
not cloud coverage directly over Reservoir 1.

Local cloud and shadow conditions have not been verified.

The candidate waterbody has not been confirmed as
surface water in 2017.

## Next action
Export a small image surrounding Reservoir 1,
inspect it in QGIS, and assess water visibility.

## Download status
No satellite imagery downloaded yet.


---

# Step 13 — First Sentinel-2 GeoTIFF Export

## Objective
Export historical satellite imagery surrounding Reservoir 1
for visual verification against the official hydrography polygon.

## Script
scripts/export_reservoir1_s2.py

## Source collection
COPERNICUS/S2_HARMONIZED

## Acquisition date
2017-07-02

## Image ID
20170702T163319_20170702T163720_T16SEH

## Export configuration
Center longitude: -86.12402
Center latitude: 38.00545
Buffer radius: 500 meters
Bands: B2, B3, B4, B8
Resolution: 10 meters
CRS: EPSG:32616
Format: GeoTIFF
Destination: Google Drive / Indiana_Surface_Water
Filename prefix: reservoir1_sentinel2_20170702

## Command
python scripts/export_reservoir1_s2.py

## Actual output
Export submitted successfully.
Task ID: OBI3VYJTTZHTLAENUH4JVRAB
Initial task status: READY

## Interpretation
The Earth Engine export task was submitted successfully.
The task was queued at the time of submission.

## Verification status
Export completion and output file not yet verified.

## Next action
Check task status, locate completed GeoTIFF in Google Drive,
and open it in QGIS for historical waterbody inspection.


## Step 13 — Export Completion Verification

### Verification method
Google Earth Engine Python API:
ee.data.getTaskStatus(task_id)

### Task ID
OBI3VYJTTZHTLAENUH4JVRAB

### Actual terminal output
State: COMPLETED
Error: None

### Interpretation
Google Earth Engine successfully completed the
Sentinel-2 GeoTIFF export task.

### Output destination
Google Drive / Indiana_Surface_Water

### Remaining verification
- Confirm the exported GeoTIFF exists in Google Drive.
- Transfer it to Big Red 200.
- Inspect its CRS, dimensions, bands, and pixel values.
- Open it in QGIS and inspect the 2017 waterbody.


---

# Step 15 — GeoTIFF Metadata Inspection

## Objective
Inspect the coordinate reference system, dimensions,
pixel resolution, spectral bands, and data type of the
exported Sentinel-2 GeoTIFF.

## Input file
data/raw/sentinel2/reservoir1_sentinel2_20170702.tif

## File existence verification
Command:
ls -lh data/raw/sentinel2/reservoir1_sentinel2_20170702.tif

Observed result:
File exists.
File size: 90K
Owner: anaprad

## Initial metadata inspection
Command:
gdalinfo data/raw/sentinel2/reservoir1_sentinel2_20170702.tif

Actual error:
-bash: gdalinfo: command not found

## Interpretation
The GDAL command-line utility is unavailable in the
current terminal environment.

This does not establish any problem with the GeoTIFF.

## Troubleshooting
Check whether a GDAL environment module is available:
module avail gdal

## Status
Raster metadata verification pending.


---

# Step 15 — GeoTIFF Metadata Inspection

## Objective
Inspect the coordinate reference system, dimensions,
pixel resolution, spectral bands, and data type of the
exported Sentinel-2 GeoTIFF.

## Input file
data/raw/sentinel2/reservoir1_sentinel2_20170702.tif

## File existence verification
Command:
ls -lh data/raw/sentinel2/reservoir1_sentinel2_20170702.tif

Observed result:
File exists.
File size: 90K
Owner: anaprad

## Initial metadata inspection
Command:
gdalinfo data/raw/sentinel2/reservoir1_sentinel2_20170702.tif

Actual error:
-bash: gdalinfo: command not found

## Interpretation
The GDAL command-line utility is unavailable in the
current terminal environment.

This does not establish any problem with the GeoTIFF.

## Troubleshooting
Check whether a GDAL environment module is available:
module avail gdal

## Status
Raster metadata verification pending.


---

# Step 15 — GDAL Troubleshooting and Raster Verification

## Initial problem
Command:
gdalinfo data/raw/sentinel2/reservoir1_sentinel2_20170702.tif

Error:
-bash: gdalinfo: command not found

## Investigation
Command:
module avail gdal

Result:
gdal/3.10.3 available on Big Red 200.

## Resolution
Command:
module load gdal/3.10.3

Verification:
gdalinfo --version

Actual output:
GDAL 3.10.3, released 2025/04/01

## Raster inspection command
gdalinfo data/raw/sentinel2/reservoir1_sentinel2_20170702.tif

## Verified raster properties
Format: GeoTIFF
Width: 101 pixels
Height: 102 pixels
Total cells per band: 10302
CRS: EPSG:32616
Pixel size: 10 x 10 meters
Origin: (576400, 4207290)
Raster footprint: approximately 1.0404 km2
Data type: UInt16
Compression: LZW

Band 1: B2 (Blue)
Band 2: B3 (Green)
Band 3: B4 (Red)
Band 4: B8 (Near-infrared)

## Interpretation
The raster metadata matches the requested export
projection, resolution, and spectral band selection.

The raster contains 10302 spatial cells per band.
This does not establish how many cells contain water.

## Remaining verification
Inspect pixel values and spatial alignment in QGIS.
Check cloud/shadow contamination at Reservoir 1.
Compare the 2017 imagery with the hydrography polygon.

## Research status
First historical Sentinel-2 GeoTIFF exported,
transferred to Big Red 200, and metadata verified.


---

# QGIS Workflow — Historical Waterbody Inspection

## Objective

Visually inspect an official NHD waterbody polygon
against historical Sentinel-2 imagery from July 2, 2017.

Determine whether the candidate is suitable for use
as a water-training or validation feature.

## Step 1 — Open QGIS

Opened QGIS through the IU Research Desktop
using ThinLinc.

Opened the existing Indiana waterbody inspection project.

## Step 2 — Load Historical Sentinel-2 Raster

Menu:
Layer > Add Layer > Add Raster Layer

Input file:
data/raw/sentinel2/reservoir1_sentinel2_20170702.tif

Clicked Add.

Result:
The Sentinel-2 raster appeared over OpenStreetMap.

## Step 3 — Configure True-Color Visualization

Right-clicked the Sentinel-2 layer.
Selected Properties > Symbology.

Selected Multiband color.

Configured:
Red channel = Band 3 (B4)
Green channel = Band 2 (B3)
Blue channel = Band 1 (B2)

Clicked Apply and OK.

Result:
A true-color visualization of the industrial
facility and surrounding landscape was displayed.

## Step 4 — Locate Reservoir 1

Opened the attribute table of waterbody_sample_5.

Selected the record:
objectid = 1

Used Zoom to Selected Features.

Observation:
The initial zoom level was approximately 1:161.
Individual 10-meter raster pixels appeared as
large colored squares.

## Step 5 — Adjust Map Scale

Changed the QGIS map scale to approximately 1:2000.

Result:
The industrial facility and surrounding satellite
pixels became easier to inspect.

## Step 6 — Display Waterbody Boundary

Opened:
waterbody_sample_5 > Properties > Symbology

Used a transparent polygon fill with a red outline.

Changed the outline stroke width from:
0.26 mm to 0.80 mm

Kept the waterbody layer above the satellite raster.

Result:
The selected Reservoir 1 polygon became visible
as a yellow selection outline over the image.

## Step 7 — Initial RGB Inspection

Observed that the selected polygon overlapped
a dark area within an industrial facility.

Interpretation:
The dark area could represent water, shadow,
or another surface.

No confirmed water label was assigned.

## Step 8 — Near-Infrared Inspection

Opened:
Sentinel-2 layer > Properties > Symbology

Changed render type:
Multiband color > Singleband gray

Selected:
Band 4 (B8, near-infrared)

Clicked Apply and OK.

Result:
The selected polygon overlapped dark NIR pixels.

Interpretation:
Low NIR brightness is consistent with possible
water but is not sufficient to confirm water.

## Step 9 — Inspect Numerical Pixel Values

Selected the Sentinel-2 raster layer.

Used the QGIS Identify Features tool.

Clicked a pixel near the selected reservoir polygon.

Observed values:
B2 = 1508
B3 = 1139
B4 = 1090
B8 = 1118

Note:
The exact clicked pixel coordinate and whether
its center lies inside the polygon remain unverified.

## Step 10 — Calculate NDWI

Formula:
NDWI = (B3 - B8) / (B3 + B8)

Calculation:
NDWI = (1139 - 1118) / (1139 + 1118)
NDWI = 21 / 2257
NDWI = 0.0093

Interpretation:
NDWI is close to zero and does not provide
strong evidence of open water by itself.

## Step 11 — Preliminary Validation Decision

Waterbody identifier:
objectid = 1

Official feature type:
436 (Reservoir)

Source-reported area:
0.002 km2

Inspection imagery:
Sentinel-2, July 2, 2017

Current status:
UNVERIFIED

Training eligibility:
NOT APPROVED

Reasons:
- Small feature relative to 10 m pixel size
- Industrial surroundings
- Potential shadows or mixed pixels
- Ambiguous NDWI
- No independent historical confirmation yet

## Step 12 — Remaining Work

1. Inspect B11 and calculate MNDWI.
2. Verify the clicked pixel lies inside the polygon.
3. Inspect additional pixels and nearby land surfaces.
4. Compare with other historical imagery where available.
5. Record a final evidence-based validation decision.


---

# Step 21 — Sentinel-2 B11 Availability Verification

## Objective
Verify the availability and native spatial resolution
of the SWIR band required for MNDWI.

## Source
COPERNICUS/S2_HARMONIZED

## Image
20170702T163319_20170702T163720_T16SEH

## Method
Queried image.bandNames() and the nominal scale
of the B11 band using the Earth Engine Python API.

## Verified output
B11 is present in the image.
B11 native resolution: 20 meters.

## Research interpretation
B3 is a 10 m band, whereas B11 is a 20 m band.
Any later comparison requires explicit grid alignment.

Resampling B11 to 10 m does not increase its
native spatial information.

## Next action
Export B11 at 20 m resolution and inspect the
resulting GeoTIFF before calculating MNDWI.


---

# Step 22 — Sentinel-2 B11 Export Submission

## Objective
Export the SWIR band B11 from the July 2, 2017
Sentinel-2 scene for subsequent MNDWI analysis.

## Actions performed
1. Created scripts/export_reservoir1_b11.py.
2. Initialized Earth Engine using class-project-487115.
3. Selected the same Sentinel-2 image used for RGB
   and NDWI inspection.
4. Defined a 500 m buffer around Reservoir 1.
5. Selected the B11 band.
6. Configured a 20 m GeoTIFF export in EPSG:32616.
7. Submitted the export task using Python.

## Terminal command
python scripts/export_reservoir1_b11.py

## Actual output
B11 export submitted.
Task ID: MOWBI5M3DU7DSWC4G6UYEKNM
Initial status: READY

## Export settings
Source: COPERNICUS/S2_HARMONIZED
Acquisition date: 2017-07-02
Band: B11
Resolution: 20 meters
CRS: EPSG:32616
Format: GeoTIFF
Destination: Google Drive / Indiana_Surface_Water
Filename prefix: reservoir1_B11_20170702

## Current status
Submitted successfully.
Completion not yet verified.

## Next step
Check task status, verify the Google Drive output,
transfer the GeoTIFF to Big Red 200, and inspect
its raster metadata before MNDWI calculation.


---

# Step 22 — B11 Export Completion Verification

## Objective
Verify that the Sentinel-2 B11 export finished successfully.

## Verification method
Google Earth Engine Python API:
ee.data.getTaskStatus(task_id)

## Task ID
MOWBI5M3DU7DSWC4G6UYEKNM

## Actual terminal output
State: COMPLETED
Error: None

## Interpretation
Google Earth Engine completed the B11 export task
without reporting an error.

## Output destination
Google Drive / Indiana_Surface_Water

## Remaining work
1. Verify the B11 GeoTIFF exists in Google Drive.
2. Transfer the file to Big Red 200.
3. Inspect raster CRS, dimensions, and resolution.
4. Align B3 and B11 grids before calculating MNDWI.
5. Inspect Reservoir 1 and document the findings.

## Status
Earth Engine export completed.
HPC transfer and raster verification pending.


---

# Step 24 — B11 GeoTIFF Metadata Verification

## Objective
Verify the spatial and technical properties of
the exported Sentinel-2 B11 raster.

## Commands executed
module load gdal/3.10.3

gdalinfo data/raw/sentinel2/reservoir1_B11_20170702.tif

## Verified output
Driver: GTiff/GeoTIFF
Size: 51 columns x 52 rows
Total cells: 2652
CRS: EPSG:32616
Origin: (576400, 4207300)
Pixel size: (20, -20) meters
Band count: 1
Band description: B11
Data type: UInt16
Compression: LZW

## Comparison with original Sentinel-2 raster
Original raster:
101 columns x 102 rows
10 m resolution
Origin: (576400, 4207290)

B11 raster:
51 columns x 52 rows
20 m resolution
Origin: (576400, 4207300)

## Finding
Both rasters use EPSG:32616, but have different
pixel resolutions, dimensions, and grid origins.

## Research decision
Do not calculate pixelwise MNDWI until B11
has been aligned with the B3 raster.

## Next action
Inspect the original raster grid and prepare
a reproducible alignment procedure.


---

# Step 25 — Original Sentinel-2 Grid Verification

## Command executed
gdalinfo data/raw/sentinel2/reservoir1_sentinel2_20170702.tif | grep -E "Size is|Origin =|Pixel Size =|Description ="

## Actual output
Size is 101, 102
Origin = (576400, 4207290)
Pixel Size = (10, -10)
Description = B2
Description = B3
Description = B4
Description = B8

## Findings
Original raster dimensions: 101 x 102
Original resolution: 10 m
Original CRS: EPSG:32616
B3 is raster band 2.

## Derived original raster bounds
xmin = 576400
ymin = 4206270
xmax = 577410
ymax = 4207290

## Research decision
Use the original raster as the reference grid.
Resample B11 using bilinear interpolation.
Preserve the original 20 m B11 file unchanged.


---

# Step 26 — B11 Spatial Grid Alignment

## Objective
Align Sentinel-2 B11 with the original 10 m
Sentinel-2 raster for pixelwise MNDWI calculation.

## Command executed
gdalwarp \
  -overwrite \
  -of GTiff \
  -t_srs EPSG:32616 \
  -te 576400 4206270 577410 4207290 \
  -ts 101 102 \
  -r bilinear \
  -co COMPRESS=LZW \
  data/raw/sentinel2/reservoir1_B11_20170702.tif \
  data/processed/reservoir1_B11_aligned_10m.tif

## Actual terminal output
Creating output file that is 101P x 102L.

## Input
data/raw/sentinel2/reservoir1_B11_20170702.tif

Native B11 resolution: 20 m
Original dimensions: 51 x 52

## Output
data/processed/reservoir1_B11_aligned_10m.tif

Requested dimensions: 101 x 102
Requested CRS: EPSG:32616
Resampling method: Bilinear
Compression: LZW

## Scientific interpretation
The B11 raster was resampled onto the original
10 m Sentinel-2 grid.

The aligned B11 values are interpolated.
The original B11 information remains 20 m resolution.

## Verification status
GDAL reported output creation.
Exact output grid metadata verification pending.


---

# Step 26A — Verification of Aligned B11 Raster

## Command executed
gdalinfo data/processed/reservoir1_B11_aligned_10m.tif | grep -E "Size is|Origin =|Pixel Size =|Band 1|Description ="

## Actual output
Size is 101, 102
Origin = (576400, 4207290)
Pixel Size = (10, -10)
Band 1 Block=101x40 Type=UInt16, ColorInterp=Gray
Description = B11

## Findings
Aligned B11 raster dimensions match the original raster.
Aligned B11 origin matches the original raster.
Aligned B11 pixel size matches the original raster.

## Research decision
Proceed to calculate MNDWI using original B3
and the aligned B11 raster.

## Limitation
B11 was resampled from native 20 m resolution.
Resampling does not add new spatial information.


---

# Step 27A — MNDWI Script Execution Error

## Objective
Calculate MNDWI using Sentinel-2 B3 and aligned B11.

## Command executed
python scripts/calculate_reservoir1_mndwi.py

## Actual error
Traceback (most recent call last):
  File "/N/project/persl/indiana_surface_water/anaprad/scripts/calculate_reservoir1_mndwi.py", line 1, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'

## Diagnosis
The active project Python virtual environment
does not contain the NumPy package.

The MNDWI calculation did not execute.
No successful output has been verified.

## Proposed correction
Install NumPy into the active virtual environment.

Command:
python -m pip install numpy

## Verification command
python -c "import numpy; print('NumPy version:', numpy.__version__)"

## Status
Installation and verification pending.


---

# Step 27A — NumPy Installation Verification

## Previous error
ModuleNotFoundError: No module named 'numpy'

## Corrective action
Installed NumPy in the active project virtual environment.

## Installation command
python -m pip install numpy

## Verification command
python -c "import numpy; print('NumPy version:', numpy.__version__)"

## Actual verification output
NumPy version: 2.5.4

## Result
NumPy import succeeded.
The missing NumPy dependency is resolved.

## Next action
Verify that the GDAL Python bindings are available
before rerunning the MNDWI calculation.


---

# Step 27B — GDAL Python Import Attempt

## Action performed
Entered a Python import statement directly
into the Bash terminal.

## Command entered
from osgeo import gdal

## Actual terminal output
-bash: from: command not found

## Diagnosis
The command was Python syntax, not a Bash command.
Bash attempted to execute "from" as a shell program.

## Correction
Execute the Python statement through the
Python interpreter using python -c.

## Correct verification command
python -c "from osgeo import gdal; print('GDAL Python version:', gdal.VersionInfo('--version'))"

## Status
GDAL Python import verification pending.


---

# Step 27B — GDAL Python Binding Verification Failed

## Command executed
python -c "from osgeo import gdal; print('GDAL Python version:', gdal.VersionInfo('--version'))"

## Actual output
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'osgeo'

## Diagnosis
The active Python environment cannot import osgeo.
GDAL command-line utilities worked previously,
but Python GDAL bindings are not currently available.

## Impact
MNDWI calculation remains blocked by a Python
dependency issue, not by raster alignment.

## Next action
Check the active Python executable, installed
GDAL version, and GDAL Python package availability.

## Status
Unresolved. No installation attempted yet.


---

# Step 27C — GDAL Python Package Check

## Command executed
python -m pip show GDAL

## Actual output
WARNING: Package(s) not found: GDAL

## Confirmed environment
Python: Project virtual environment (.venv)
GDAL command-line version: 3.10.3
NumPy version: 2.5.4

## Diagnosis
The GDAL Python package is not installed in
the active virtual environment.

## Proposed correction
Attempt installation of Python GDAL bindings
matching the available GDAL 3.10.3 library.

## Installation command
python -m pip install "GDAL==3.10.3"

## Status
Installation pending.
MNDWI calculation has not yet succeeded.


---

# Step 27D — GDAL Python Bindings Installation

## Previous problem
ModuleNotFoundError: No module named 'osgeo'

## Command executed
python -m pip install "GDAL==3.10.3"

## Actual installation output
Successfully built GDAL
Installing collected packages: GDAL
Successfully installed GDAL-3.10.3

## Result
GDAL Python bindings installed successfully
in the active project virtual environment.

## Next action
Verify that Python can import osgeo.gdal.

## Status
Installation successful.
Import verification pending.


---

# Step 27E — GDAL Python Import Verification

## Objective
Verify that GDAL Python bindings work inside
the project's virtual environment.

## Command executed
python -c "from osgeo import gdal; print('GDAL Python version:', gdal.VersionInfo('--version'))"

## Actual terminal output
GDAL Python version: GDAL 3.10.3, released 2025/04/01

## Result
GDAL Python import succeeded.

## Verified dependencies
NumPy: 2.5.4
GDAL Python: 3.10.3

## Issues resolved
1. Missing NumPy package.
2. Missing GDAL Python bindings.
3. Confusion between Bash commands and Python statements.

## Current research status
Sentinel-2 B3 raster: Available
Sentinel-2 B11 raster: Available
B11 grid alignment: Verified
Python dependencies: Verified
MNDWI calculation: Pending
Reservoir 1 water classification: Unverified

## Next command
python scripts/calculate_reservoir1_mndwi.py


---

# Step 28 — First Successful MNDWI Calculation

## Objective
Calculate the Modified Normalized Difference Water Index
using Sentinel-2 B3 and aligned B11 from July 2, 2017.

## Environment setup
module load python/3.12.11
module load gdal/3.10.3
source .venv/bin/activate

## First execution attempt
^Mpython scripts/calculate_reservoir1_mndwi.py

## Actual error
-bash: $'\rpython': command not found

## Diagnosis
An unintended carriage-return character preceded
the Python command.

## Correction
Retyped the command without the extra character.

## Successful command
python scripts/calculate_reservoir1_mndwi.py

## Warning observed
FutureWarning: Neither gdal.UseExceptions() nor
gdal.DontUseExceptions() has been explicitly called.
GDAL 4.0 will enable exceptions by default.

## Actual calculation output
MNDWI raster created:
data/processed/reservoir1_MNDWI_20170702.tif

Raster dimensions: (102, 101)
Valid pixels: 10302
Invalid pixels: 0
Minimum MNDWI: -0.5897336006164551
Maximum MNDWI: 0.2078431397676468
Mean MNDWI: -0.31966644525527954

## Method
MNDWI = (B3 - B11) / (B3 + B11)

B3 source: Original Sentinel-2 GeoTIFF, band 2
B11 source: Bilinearly aligned SWIR GeoTIFF, band 1

Output data type: Float32
Output NoData value: -9999

## Result
MNDWI computation completed successfully.
The script reported 10,302 valid pixels.

## Scientific limitations
1. No cloud or shadow mask has been applied.
2. B11 was resampled from native 20 m resolution.
3. The statistics describe the entire inspection raster,
   not only Reservoir 1.
4. No independent historical water verification has occurred.
5. Reservoir 1 remains UNVERIFIED.

## Next action
Load the MNDWI GeoTIFF in QGIS and inspect its
spatial relationship with the NHD reservoir polygon.


---

# Step 29 — MNDWI Raster Opening Attempt

## Action performed
Entered the MNDWI GeoTIFF path directly in Bash.

## Actual error
-bash: /N/project/persl/indiana_surface_water/anaprad/data/processed/reservoir1_MNDWI_20170702.tif: Permission denied

## Diagnosis
Bash attempted to execute a GeoTIFF file as a command.
The raster was not intended to be executable.

## Correction
Open the GeoTIFF through QGIS:
Layer > Add Layer > Add Raster Layer

## File
data/processed/reservoir1_MNDWI_20170702.tif

## Status
QGIS visualization pending.


---

# Step 31 — First MNDWI Pixel Inspection in QGIS

## Objective
Inspect a numerical MNDWI value near the
candidate Reservoir 1 polygon.

## Actions performed
1. Opened the MNDWI raster in QGIS.
2. Selected the reservoir polygon for visual reference.
3. Activated the Identify Features tool.
4. Clicked a raster pixel near the reservoir center.
5. Recorded the reported value and location.

## Data source
reservoir1_MNDWI_20170702.tif

## Actual QGIS observation
Band 1 MNDWI: -0.349515
Longitude: -86.1239986
Latitude: 38.0055548
Column: 50
Row: 49

## Interpretation
The selected pixel has a negative MNDWI value.
This does not provide strong evidence of open water.

## Limitations
- Pixel containment within the NHD polygon is not verified.
- One pixel cannot characterize the whole reservoir.
- B11 was resampled from 20 m.
- Cloud and shadow masking has not been performed.
- The NHD polygon is not independently verified 2017 ground truth.

## Research status
Reservoir 1 remains UNVERIFIED.

## Next action
Inspect a nearby pixel outside the polygon and
compare its MNDWI value.


---

# Step 32 — MNDWI Pixel Comparison

## Objective
Compare the MNDWI of a candidate reservoir pixel
with a nearby comparison pixel.

## Pixel 1
MNDWI: -0.349515
Longitude: -86.1239986
Latitude: 38.0055548
Column: 50
Row: 49

## Pixel 2
MNDWI: -0.225697
Longitude: -86.1240245
Latitude: 38.0054698
Column: 50
Row: 50

## Calculation
Pixel 1 minus Pixel 2:
-0.349515 - (-0.225697) = -0.123818

## Observation
Both sampled pixels have negative MNDWI.
Pixel 1 has a lower MNDWI than Pixel 2.

## Interpretation
The observed values do not clearly distinguish
the candidate reservoir from its nearby surroundings.

## Limitations
1. Pixel 2 has not been confirmed as non-water.
2. Pixel containment relative to the polygon
   has not been independently checked.
3. Both pixels may contain mixed surfaces.
4. B11 has native 20 m resolution.
5. Cloud and shadow masking remains incomplete.

## Decision
Do not assign a water or land training label
to either pixel yet.

Reservoir 1 status: UNVERIFIED.


---

# Step 34 — OGR Geometry Library Verification

## Objective
Verify that the GDAL OGR Python library is available
for spatial geometry operations.

## Command executed
python -c "import osgeo.ogr; print('OGR geometry library available')"

## Actual output
OGR geometry library available

## Result
OGR Python import succeeded.

## Research purpose
Use official NHD polygon geometry to determine
whether sampled locations fall inside or outside
Reservoir 1.

## Next step
Execute scripts/check_reservoir1_pixels.py.

## Limitations
Point-in-polygon testing does not establish
historical water presence or full pixel containment.


---

# Step 35 — Reservoir 1 Point-in-Polygon Verification

## Objective
Determine whether two QGIS-inspected locations
fall inside the official NHD reservoir polygon.

## Command executed
python scripts/check_reservoir1_pixels.py

## Warning observed
OGR FutureWarning:
Neither ogr.UseExceptions() nor
ogr.DontUseExceptions() has been explicitly called.
GDAL 4.0 will enable exceptions by default.

## Actual terminal output
Reservoir objectid: 1

Pixel 1: INSIDE
Longitude: -86.1239986
Latitude: 38.0055548

Pixel 2: INSIDE
Longitude: -86.1240245
Latitude: 38.0054698

## Corresponding MNDWI values
Pixel 1: -0.349515
Pixel 2: -0.225697

## Important correction
Pixel 2 was previously treated as a possible
nearby land comparison.

The geometry test shows that its clicked
location is also inside the reservoir polygon.

Therefore, this is NOT a verified water-versus-land
comparison.

## Interpretation
Both sampled locations have negative MNDWI.
Neither observation independently confirms
open water or dry land in 2017.

## Limitations
1. The test uses QGIS clicked coordinates.
2. Raster-cell center containment is not yet verified.
3. Full pixel containment is not yet verified.
4. NHD geometry does not establish 2017 water presence.
5. B11 has native 20 m resolution.
6. Cloud and shadow masking is incomplete.

## Research decision
Do not use either pixel as a confirmed training label.

Reservoir 1 status: UNVERIFIED.

## Next action
Select and verify a comparison pixel outside
the NHD reservoir polygon.


---

# Step 36 — Additional MNDWI Pixel Inspection

## Objective
Inspect MNDWI values near and outside the
upper boundary of Reservoir 1.

## QGIS actions
1. Kept the MNDWI raster visible.
2. Kept the selected NHD reservoir polygon visible.
3. Used Identify Features on additional pixels.
4. Recorded the displayed MNDWI values.

## Pixel 3
MNDWI: -0.203025
Longitude: -86.123998
Latitude: 38.005755
Column: 50
Row: 47

Visual observation:
Clicked location appears above the reservoir boundary.

## Pixel 4
MNDWI: -0.336924

Visual observation:
Clicked location appears near the upper boundary.
Coordinates not recorded in the screenshot.

## Interpretation
Both observed values are negative.
Polygon containment and surface type remain unverified.

## Next action
Perform a geometry containment check for Pixel 3.


---

# Step 37 — Outside-Polygon Verification

## Objective
Verify whether Pixel 3 lies outside the
official NHD Reservoir 1 polygon.

## Method
Used GDAL/OGR point-in-polygon testing
against objectid = 1 in waterbody_sample_5.geojson.

## Tested point
Longitude: -86.123998
Latitude: 38.005755

## Associated MNDWI
-0.203025

## Actual terminal output
Pixel 3 MNDWI: -0.203025
Inside reservoir: False
Touches boundary: False
Result: OUTSIDE

## Verified finding
The tested coordinate is outside the NHD polygon
and does not touch its boundary.

## Three-point comparison
Pixel 1: -0.349515, INSIDE
Pixel 2: -0.225697, INSIDE
Pixel 3: -0.203025, OUTSIDE

## Interpretation
Both inside observations have lower MNDWI
than the outside observation.

This is an exploratory comparison only.

## Limitations
1. Outside the polygon does not prove dry land.
2. Point containment does not verify full raster-cell containment.
3. NHD geometry is not verified 2017 ground truth.
4. B11 was resampled from 20 m resolution.
5. Cloud and shadow masking is incomplete.

## Research decision
No training labels assigned.
Reservoir 1 remains UNVERIFIED.


---

# Step 39 — Actual Raster Pixel-Center Calculation

## Objective
Calculate the exact centers of three inspected
MNDWI raster cells using the GeoTIFF geotransform.

## Method
Read the raster geotransform using GDAL.

For each raster cell:
X = originX + (column + 0.5) * pixelWidth
Y = originY + (row + 0.5) * pixelHeight

## Actual terminal output
Pixel 1: center X=576905.0, Y=4206795.0
Pixel 2: center X=576905.0, Y=4206785.0
Pixel 3: center X=576905.0, Y=4206815.0

## Coordinate system
EPSG:32616 — WGS 84 / UTM zone 16N
Coordinates are expressed in meters.

## Findings
All three pixels occupy column 50.
Their centers differ in northing according
to their respective raster rows.

## Limitation
These are raster-cell centers, not full
10 m pixel footprints.

## Next action
Transform pixel centers to EPSG:4326 and
test their containment within the NHD polygon.


---

# Step 40 — Raster Pixel-Center Polygon Verification

## Objective
Determine whether the actual centers of three
MNDWI raster cells fall inside or outside
the official NHD Reservoir 1 polygon.

## Method
1. Used EPSG:32616 raster-cell center coordinates.
2. Transformed coordinates to EPSG:4326.
3. Loaded the official NHD waterbody GeoJSON.
4. Selected the polygon with objectid = 1.
5. Used OGR spatial containment testing.

## Actual terminal output

Pixel 1
Longitude: -86.12400426
Latitude: 38.00556971
Status: INSIDE

Pixel 2
Longitude: -86.12400533
Latitude: 38.00547959
Status: INSIDE

Pixel 3
Longitude: -86.12400212
Latitude: 38.00574995
Status: OUTSIDE

## Corresponding MNDWI observations
Pixel 1: -0.349515
Pixel 2: -0.225697
Pixel 3: -0.203025

## Verified finding
Two raster-cell centers are inside the mapped
reservoir polygon.

One raster-cell center is outside the polygon.

## Interpretation
The two inside pixels have negative MNDWI.
The outside pixel also has negative MNDWI.

The index has not clearly distinguished
the candidate reservoir from its surroundings
in this three-pixel comparison.

## Limitations
1. Pixel-center containment is not full-pixel containment.
2. NHD polygons are not verified 2017 water labels.
3. Native B11 resolution is 20 m.
4. Cloud and shadow masking is incomplete.
5. The outside pixel is not independently verified land.

## Research decision
Do not assign training labels yet.
Reservoir 1 remains UNVERIFIED.

## Next action
Check whether the complete 10 m raster-cell
footprints lie inside or outside the NHD polygon.


---

# Step 42 — Full Raster Pixel-Footprint Verification

## Objective
Measure the percentage of each 10 m raster-cell
footprint overlapping the official NHD Reservoir 1 polygon.

## Method
1. Loaded the official NHD GeoJSON using OGR.
2. Selected objectid = 1.
3. Transformed the polygon from EPSG:4326 to EPSG:32616.
4. Constructed 10 m x 10 m raster-cell polygons.
5. Calculated their intersections with the NHD polygon.
6. Divided intersection area by raster-cell area.

## Actual terminal output
Pixel 1: 100.00% inside NHD polygon
Pixel 2: 100.00% inside NHD polygon
Pixel 3: 0.00% inside NHD polygon

## Corresponding MNDWI
Pixel 1: -0.349515
Pixel 2: -0.225697
Pixel 3: -0.203025

## Findings
Pixel 1: Entire 10 m footprint inside NHD polygon.
Pixel 2: Entire 10 m footprint inside NHD polygon.
Pixel 3: No 10 m footprint overlap with NHD polygon.

## Interpretation
The full-footprint geometry test confirms
two polygon-interior cells and one exterior cell.

All three MNDWI values are negative.
The exterior pixel has a higher MNDWI than
the two interior pixels.

This is not sufficient to determine historical
water presence or model classification accuracy.

## Scientific limitations
- NHD polygon is not verified 2017 ground truth.
- Native Sentinel-2 B11 resolution is 20 m.
- Cloud and shadow masking is incomplete.
- No independent water or land labels are available.
- Only three pixels were examined.

## Research decision
Reservoir 1 remains UNVERIFIED.
Do not assign water or land training labels.

## Next research priority
Identify larger representative Indiana waterbodies,
inspect historical satellite imagery, and establish
reliable water and non-water reference samples.


---

# Step 45 — Discovery of Larger Waterbody Candidates

## Objective
Identify larger NHD lake/pond and reservoir records
for historical surface-water inspection.

## Source
Indiana NHD Local Resolution Waterbody FeatureServer
Layer 1

## Query criteria
ftype IN (390,436)
areasqkm >= 1

## Ordering
areasqkm DESC

## Maximum returned records
20

## Fields requested
objectid, gnis_name, ftype, areasqkm

## Output
results/inventory/large_waterbody_candidates.json

## Method
Used the ArcGIS REST query endpoint with curl.
Used Python json to inspect returned attributes.

## Limitations
- Reported area is a source attribute.
- Records have not yet been clipped to Indiana.
- Large polygons are not automatically suitable
  training or validation sites.
- Historical 2017 water presence is unverified.

## Next action
Inspect the returned candidate records, check
their geographic locations, and select suitable
waterbodies for historical imagery verification.


---

# Step 46 — Monroe Lake NHD Polygon Retrieval

## Objective
Retrieve the official NHD polygon for Monroe Lake.

## Source
Indiana NHD Local Resolution Waterbody FeatureServer
Layer 1

## Query
objectid = 80983
returnGeometry = true
outSR = 4326
f = geojson

## Saved file
data/reference/hydrography/monroe_lake_nhd.geojson

## Actual terminal output
Features returned: 1
Name: Monroe Lake
Object ID: 80983
Geometry: Polygon

## Verified findings
One Monroe Lake polygon was successfully retrieved.

## Limitations
The polygon is a hydrographic reference boundary.
Its agreement with 2017 satellite observations
has not yet been established.

## Next action
Load the polygon into QGIS and inspect its
shape, location, and surrounding landscape.


---

# Step 47 — Monroe Lake QGIS Inspection

## Objective
Inspect the downloaded Monroe Lake NHD polygon
in QGIS against an OpenStreetMap basemap.

## Layer
monroe_lake_nhd

## Reference file
data/reference/hydrography/monroe_lake_nhd.geojson

## Observations
- Polygon successfully loaded into QGIS.
- Polygon appears as a large branching waterbody.
- General location and shape visually align
  with Monroe Lake on OpenStreetMap.
- Polygon currently has a solid grey fill.

## Interpretation
The geometry appears geographically plausible.

## Limitations
- OpenStreetMap is not historical 2017 ground truth.
- Sentinel-2 imagery has not been inspected.
- Water and non-water training labels remain unassigned.

## Next action
Change polygon symbology to a transparent fill
with a visible boundary.


---

# Step 50 — Sentinel-2 Scene Discovery: CRS Error

## Objective
Identify Sentinel-2 scenes intersecting Monroe Lake
between June 1 and September 30, 2017.

## Initial error
ee.ee_exception.EEException:
Invalid CRS declaration in GeoJSON: null

## Cause
The GeoJSON geometry passed to Earth Engine
contained an invalid null CRS declaration.

## Correction
Extracted only the geometry type and coordinates
and explicitly set the CRS to EPSG:4326.

## Data source
COPERNICUS/S2_HARMONIZED

## Study period
2017-06-01 to 2017-09-30 inclusive.

## Status
Corrected code provided; execution results pending.


## Step 50 — Second CRS Error and Correction

### Second error
EEException: Invalid CRS declaration in GeoJSON:
"EPSG:4326"

### Cause
The Earth Engine geometry constructor rejected the
string CRS declaration in the GeoJSON object.

### Correction
Removed the CRS property entirely.
Passed only geometry type and coordinates.

### Coordinate assumption
The NHD GeoJSON was requested with outSR=4326,
so its coordinates are WGS84 longitude/latitude.

### Status
Third execution attempt pending.


---

# Step 50 — Successful Sentinel-2 Scene Discovery

## Study area
Monroe Lake, Indiana
NHD objectid: 80983

## Satellite dataset
COPERNICUS/S2_HARMONIZED

## Period
2017-06-01 to 2017-09-30 inclusive

## Actual result
12 Sentinel-2 scenes intersect Monroe Lake.
All returned scene IDs belong to tile T16SEJ.

## Scenes with less than 5% reported cloud cover
2017-07-02: 3.87575024634955%
2017-09-05: 2.58992505001642%
2017-09-20: 3.98632386753859%
2017-09-25: 2.29131953775867%

## Interpretation
Four scenes have low scene-level cloud percentages.

These are preliminary candidates, not yet
confirmed cloud-free observations over Monroe Lake.

## Research decision
Prioritize July 2, 2017 for the initial
Monroe Lake experiment.

Retain September observations as candidates
for temporal comparison.

## Next action
Evaluate cloud contamination over the lake
before exporting satellite bands.


---

# Step 51 — Monroe Lake QA60 Cloud Inspection

## Objective
Estimate cloud-flagged pixel fractions over
Monroe Lake for four low-cloud Sentinel-2 scenes.

## Dataset
COPERNICUS/S2_HARMONIZED

## Method
Used QA60 bit 10 (opaque cloud) and
bit 11 (cirrus), with a 60 m reduction
over the Monroe Lake NHD polygon.

## Actual results
2017-07-02: 0.50%
2017-09-05: 0.00%
2017-09-20: 0.00%
2017-09-25: 0.00%

## Interpretation
All four dates have low QA60 cloud-flagged
fractions within the NHD lake geometry.

## Limitations
QA60 does not comprehensively identify cloud
shadows, haze, or every cloudy pixel.
Zero QA60 cloud flags does not prove
completely cloud-free imagery.

## Research decision
Use July 2, 2017 as the initial image.
Retain September 5 for potential
within-year surface-water comparison.

## Next action
Verify required bands and valid observation
coverage before downloading imagery.


---

# Step 52 — Sentinel-2 Band and Coverage Verification

## Study area
Monroe Lake, Indiana
NHD objectid: 80983

## Scene
20170702T163319_20170702T163720_T16SEJ

## Available bands
B1, B2, B3, B4, B5, B6, B7, B8, B8A,
B9, B10, B11, B12, QA10, QA20, QA60,
MSK_CLASSI_OPAQUE, MSK_CLASSI_CIRRUS,
MSK_CLASSI_SNOW_ICE

## Actual coverage result
Valid B3/B11 coverage: {'valid': 1}

## Interpretation
Both MNDWI input bands have valid observations
across the sampled lake polygon at 20 m scale.

## Limitations
Valid coverage does not establish cloud-free
imagery or actual water presence.

## Next action
Export B2, B3, B4, B8, and B11 on a common
20 m EPSG:32616 grid, including a 1 km
buffer around Monroe Lake.


---

# Step 53 — Monroe Lake Sentinel-2 Export

## Objective
Export Sentinel-2 imagery for Monroe Lake
and surrounding land for MNDWI analysis.

## Acquisition date
2017-07-02

## Scene
20170702T163319_20170702T163720_T16SEJ

## Exported bands
B2, B3, B4, B8, B11

## Export configuration
Coordinate system: EPSG:32616
Pixel size: 20 m
Region: Monroe Lake with 1 km buffer,
exported as its bounding rectangle
Destination: Google Drive
Folder: IndianaSurfaceWater
File format: GeoTIFF

## Actual terminal output
Export task submitted.
Task ID: YLANLX6QQG5V55TLRWHLCKXF
Task state: READY

## Interpretation
Earth Engine accepted the export request.
The export had not started at the time of submission.

## Next action
Check task status and confirm completion
before transferring the GeoTIFF to Big Red 200.


---

# Step 54 — Earth Engine Export Status

## Task
monroe_lake_s2_20170702

## Task ID
YLANLX6QQG5V55TLRWHLCKXF

## Actual output
State: RUNNING
Error: None

## Interpretation
Earth Engine is processing the export.
No error was reported at the time of checking.

## Next action
Prepare the MNDWI processing script while
the GeoTIFF export is running.


---

# Step 56 — Monroe Lake Sentinel-2 Export Completed

## Earth Engine task
monroe_lake_s2_20170702

## Task ID
YLANLX6QQG5V55TLRWHLCKXF

## Actual terminal output
Task: monroe_lake_s2_20170702
State: COMPLETED
Error: None

## Interpretation
Google Earth Engine successfully completed
the Sentinel-2 image export.

## Export destination
Google Drive / IndianaSurfaceWater

## Next action
Locate the GeoTIFF in Google Drive,
transfer it to Big Red 200,
and verify its raster metadata.


---

# Step 57 — GeoTIFF Located in Google Drive

## Export
monroe_lake_s2_20170702

## Destination
Google Drive / IndianaSurfaceWater

## Reported file size
8.1 MB

## Status
File located in Google Drive.
Transfer to Big Red 200 pending.

## Next action
Download the GeoTIFF using the ThinLinc browser
and verify its local file path.


---

# Step 59B — Monroe Lake Raster Metadata Audit

Source:
Sentinel-2 Harmonized, July 2, 2017

File:
data/raw/sentinel2/monroe_lake_s2_20170702.tif

Raster dimensions:
1039 columns x 814 rows

Total raster cells:
845746

Pixel size:
20 m x 20 m

Projected coordinate system:
EPSG:32616

Raster data type:
UInt16

Band order:
1 - B2
2 - B3
3 - B4
4 - B8
5 - B11

Export footprint:
338.2984 square kilometers

Important distinction:
The export footprint is not the lake's
water surface area.

Next:
Calculate MNDWI and inspect its distribution.


---

# Step 60 — Monroe Lake MNDWI Calculation

## Input
data/raw/sentinel2/monroe_lake_s2_20170702.tif

## Output
data/processed/monroe_lake_MNDWI_20170702.tif

## Formula
MNDWI = (B3 - B11) / (B3 + B11)

## Actual results
Valid pixels: 845746
Invalid pixels: 0
Minimum: -0.7666560411453247
Maximum: 0.891758918762207
Mean: -0.24760057032108307

## Interpretation
MNDWI was calculated for all 845746 raster cells.
The mean describes the entire export footprint,
not Monroe Lake alone.

No water classification or independent accuracy
assessment has yet been performed.

## Next step
Visualize MNDWI in QGIS and compare its spatial
pattern with the Monroe Lake NHD polygon.


---

# Step 62 — MNDWI Inside vs Outside Monroe Lake

Date of satellite observation:
2017-07-02

Reference geometry:
NHD Monroe Lake polygon

Raster:
data/processed/monroe_lake_MNDWI_20170702.tif

Spatial resolution:
20 meters

INSIDE POLYGON
Pixels: 112310
Rasterized area: 44.924 km2
Mean MNDWI: 0.39665454626083374
Median MNDWI: 0.43842363357543945
MNDWI > 0: 97538
Percent MNDWI > 0: 86.84711957973467

OUTSIDE POLYGON
Pixels: 733436
Rasterized area: 293.3744 km2
Mean MNDWI: -0.34625446796417236
Median MNDWI: -0.4031986594200134
MNDWI > 0: 34299
Percent MNDWI > 0: 4.676481656204495

INTERPRETATION
MNDWI is substantially higher inside the
NHD Monroe Lake polygon than outside it.

MNDWI > 0 is an exploratory threshold.

NHD polygon membership is not independent
2017 water/non-water ground truth.

Cloud and shadow contamination have not
been fully excluded.

NEXT
Evaluate threshold agreement with the NHD
polygon and inspect spatial disagreements.


## Step 66 — Sentinel-1 Orbit-121 Coverage Verification

Date: 2026-10-23
Study area: Monroe Lake, Indiana
Period: July 2017
Dataset: COPERNICUS/S1_GRD
Orbit direction: ASCENDING
Relative orbit: 121
Polarizations selected: VV and VH
Coverage band evaluated: VV
Evaluation scale: 20 meters

### Results

Orbit-121 scene count: 2

Scene 1:
S1A_IW_GRDH_1SDV_20170717T233951_20170717T234016_017518_01D4B1_699C
Valid VV coverage fraction: 1.0 (100%)

Scene 2:
S1A_IW_GRDH_1SDV_20170729T233952_20170729T234023_017693_01DA0A_9919
Valid VV coverage fraction: 1.0 (100%)

### Interpretation

Both Sentinel-1 scenes have full valid VV coverage
over the Monroe Lake polygon at the evaluation scale.

The scenes share ascending relative orbit 121,
making them suitable candidates for a temporal
radar composite.

### Limitations

The test evaluated VV coverage over the lake polygon,
not VH coverage or the complete export rectangle.

Full coverage does not establish image quality,
temporal consistency, or classification accuracy.

### Terminal Error

Command: nano documentation/research_log.md
Error: -bash: nano: command not found
Cause: nano is unavailable in the current environment.
Resolution: Append documentation using Bash heredoc.

### Next Step

Verify VV and VH coverage over the full export area,
then prepare the Sentinel-1 median composite.

Status: COMPLETED


---

# Sentinel-1 Monthly Composite: Export and Verification

Date: 2026-10-23
Study area: Monroe Lake, Indiana
Study period: July 2017
Research objective: Prepare Sentinel-1 and Sentinel-2
features for Random Forest surface-water classification.

## Step 69 — Sentinel-1 Composite Export

Dataset: COPERNICUS/S1_GRD

Selected acquisitions:
1. 2017-07-17, ASCENDING, relative orbit 121
2. 2017-07-29, ASCENDING, relative orbit 121

Selection criteria:
- Interferometric Wide Swath (IW) mode
- VV and VH polarizations
- Same ascending relative orbit
- Full valid VV/VH coverage over the pilot export region

Processing:
- Pixelwise median of two radar acquisitions
- Median applied to VV and VH in dB
- Output data type: Float32
- Spatial reference: EPSG:32616
- Pixel resolution: 20 m
- Output dimensions: 1039 columns x 814 rows
- Reference grid: Existing Sentinel-2 GeoTIFF

Export grid:
Origin X: 540360.0
Origin Y: 4331540.0
Pixel width: 20.0 m
Pixel height: -20.0 m

Earth Engine export:
Task ID: TIVQA63CTU7EUKLJTH2JAXEI
Destination: Google Drive / IndianaSurfaceWater
Filename: monroe_lake_s1_july2017.tif

Initial task status: READY

## Step 70 — Earth Engine Export Completion

Task ID: TIVQA63CTU7EUKLJTH2JAXEI
Final status: COMPLETED
Error: None

Interpretation:
Earth Engine successfully generated and exported
the Sentinel-1 median composite to Google Drive.

Status: COMPLETED

## Step 71 — Download and Raster Metadata Verification

Local destination:
data/raw/sentinel1/monroe_lake_s1_july2017.tif

Reported file size: 7.2 MB

GDAL verification:
Driver: GTiff/GeoTIFF
Dimensions: 1039 x 814
CRS: EPSG:32616
Origin: (540360.0, 4331540.0)
Pixel size: (20.0, -20.0)
Compression: LZW
Interleave: PIXEL

Raster bands:
Band 1: VV, Float32
Band 2: VH, Float32

Spatial interpretation:
The Sentinel-1 raster has the same reported
dimensions, coordinate reference system,
origin and pixel size as the Sentinel-2
reference raster.

This indicates matching raster grids based
on the inspected metadata.

Limitations:
- Radar pixel values have not yet been statistically checked.
- Local valid-data masks have not yet been evaluated.
- Classification accuracy has not been measured.
- The composite represents two July acquisitions,
  not a single-date radar observation.

Status: COMPLETED

## Step 72 — Radar Pixel Validation

Objective:
Verify exact spatial alignment and inspect VV/VH
pixel distributions and valid-data masks.

Planned checks:
- Exact raster dimensions
- Coordinate reference system equality
- Geotransform equality
- Valid and invalid pixel counts
- Minimum and maximum radar backscatter
- Mean and median radar backscatter

Status: PENDING

## Research Progress

Completed:
- Sentinel-1 acquisition inventory
- Relative-orbit compatibility assessment
- VV/VH coverage verification
- Median composite export
- Earth Engine task completion
- Local GeoTIFF transfer
- GDAL raster metadata inspection

Remaining:
- Radar pixel validation
- Sentinel-2 cloud/shadow-masked composite
- Multisensor feature stacking
- Provisional water/land label preparation
- Spatial train/test split
- Random Forest training and evaluation


## Step 72 — Sentinel-1 Radar Pixel Validation

Date: 2026-10-23
Input: data/raw/sentinel1/monroe_lake_s1_july2017.tif
Reference: data/raw/sentinel2/monroe_lake_s2_20170702.tif

Spatial alignment: PASSED
Raster dimensions: 1039 x 814
Total raster pixels: 845746
Coordinate reference system: EPSG:32616
Pixel resolution: 20 m

VV band (dB):
Valid pixels: 845746
Invalid pixels: 0
Minimum: -29.824675
Maximum: 16.896454
Mean: -9.82149
Median: -8.906094

VH band (dB):
Valid pixels: 845746
Invalid pixels: 0
Minimum: -44.28267
Maximum: 12.681552
Mean: -16.165726
Median: -14.974061

Interpretation:
Both radar bands have valid values throughout
the exported raster and are spatially aligned
with the existing Sentinel-2 reference raster.

Limitations:
Pixel validity does not establish radar quality
or water classification accuracy.
The backscatter distributions have not yet been
evaluated separately for water and land.

Status: COMPLETED

Next step:
Create the July 2017 cloud-masked Sentinel-2
optical composite and verify observation coverage.


## Step 73 — Sentinel-2 Cloud Coverage Assessment

Date: 2026-10-23
Study area: Monroe Lake, Indiana
Period: July 2017

Dataset:
COPERNICUS/S2_HARMONIZED

Number of acquisitions: 4

Method:
Used QA60 bit 10 (opaque cloud) and bit 11
(cirrus) to calculate unflagged area fractions
over Monroe Lake and its 1 km buffered
bounding rectangle.

Results:

2017-07-02
Scene-wide cloud cover: 3.87575024634955%
Lake QA60-unflagged: 99.4992%
Export region QA60-unflagged: 96.2455%

2017-07-07
Scene-wide cloud cover: 10.1479888918749%
Lake QA60-unflagged: 95.0420%
Export region QA60-unflagged: 89.9029%

2017-07-22
Scene-wide cloud cover: 86.7081%
Lake QA60-unflagged: 0.9394%
Export region QA60-unflagged: 1.1316%

2017-07-27
Scene-wide cloud cover: 99.7822867210129%
Lake QA60-unflagged: 0.0618%
Export region QA60-unflagged: 0.0725%

Decision:
Select July 2 and July 7 as candidate
optical acquisitions for the initial
July 2017 composite.

Exclude July 22 and July 27 because
almost the entire study area is flagged.

Limitations:
QA60 screening alone does not establish
complete cloud and shadow removal.

Sentinel-2 selected dates are earlier
than Sentinel-1 dates (July 17 and 29).

Status: COMPLETED


## Steps 75–76 — Optical Scene Availability and Footprint Verification

Date: 2026-10-23
Study area: Monroe Lake, Indiana

Step 75:
Queried COPERNICUS/S2_HARMONIZED and
COPERNICUS/S2_CLOUD_PROBABILITY for
July 1–7, 2017, MGRS tile 16SEJ.

Optical tile records found: 4
Cloud-probability records found: 0

Two additional July 5 optical records
were identified by tile filtering.

Step 76:
Checked the spatial footprint of both
July 5 images against Monroe Lake.

Image:
20170705T164319_20170705T164317_T16SEJ
Lake footprint coverage: 0.0%
Scene cloud cover: 97.25874842183%

Image:
20170705T164319_20170705T165225_T16SEJ
Lake footprint coverage: 0.0%
Scene cloud cover: 97.8264789513836%

Conclusion:
Neither July 5 record covers Monroe Lake.
Both are excluded from the pilot composite.

Initial selected optical acquisitions:
2017-07-02
2017-07-07

The cloud-probability collection returned no
matching records for the queried date/tile.
This does not establish that no alternative
cloud or shadow information exists.

Next:
Investigate available cloud/shadow masking
methods and build the optical composite.

Status: COMPLETED


## Step 78 — Sentinel-2 Quality-Band Validity

Date: 2026-10-23

Selected optical acquisitions:
2017-07-02
2017-07-07

Bands inspected:
QA60
MSK_CLASSI_OPAQUE
MSK_CLASSI_CIRRUS
MSK_CLASSI_SNOW_ICE

Valid-data fractions over Monroe Lake:

                    July 2    July 7
QA60                  1.0       1.0
MSK_CLASSI_OPAQUE     1.0       1.0
MSK_CLASSI_CIRRUS     1.0       1.0
MSK_CLASSI_SNOW_ICE   1.0       1.0

Interpretation:
All four quality bands have valid/unmasked
pixels throughout the evaluated lake polygon.

Important limitation:
Band validity does not establish whether
the stored classifications are meaningful.
Historical MSK_CLASSI bands may contain
placeholder values.

Next:
Inspect actual cloud-flag values before
choosing the optical masking strategy.

Status: COMPLETED


## Step 79 — Sentinel-2 Cloud-Flag Inspection

Date: 2026-10-23
Study area: Monroe Lake, Indiana

Acquisition: 2017-07-02
QA60 opaque-cloud fraction: 0.005008204013917126
MSK_CLASSI_OPAQUE mean: 0.005008204013917126
QA60 cirrus fraction: 0
MSK_CLASSI_CIRRUS mean: 0
MSK_CLASSI_SNOW_ICE mean: 0

Acquisition: 2017-07-07
QA60 opaque-cloud fraction: 0.0495801512203569
MSK_CLASSI_OPAQUE mean: 0.0495801512203569
QA60 cirrus fraction: 0
MSK_CLASSI_CIRRUS mean: 0
MSK_CLASSI_SNOW_ICE mean: 0

Decision:
Use QA60 opaque-cloud and cirrus bits
for the initial optical composite.

The matching QA60 and MSK_CLASSI_OPAQUE
aggregate fractions are encouraging but
do not prove pixel-level equivalence.

Limitations:
Cloud shadows are not explicitly removed.
Further visual and statistical quality
checks are required.

Status: COMPLETED


## Step 80 — Sentinel-2 Composite Export Submission

Date: 2026-10-23

Input collection:
COPERNICUS/S2_HARMONIZED

Selected acquisition dates:
2017-07-02
2017-07-07

Cloud screening:
QA60 opaque-cloud and cirrus flags.

Composite method:
Pixelwise median of unmasked observations.

Output bands:
B2, B3, B4, B8, B11, valid_obs

The valid_obs band counts available
B3 observations per pixel (0, 1 or 2).

Output grid:
EPSG:32616
Resolution: 20 m
Dimensions: 1039 x 814
Reference: Sentinel-1 July 2017 raster

Google Drive folder:
IndianaSurfaceWater

Expected filename:
monroe_lake_s2_july2017_composite.tif

Earth Engine task ID:
RVZ67NMRMYY347H44KANJCSW

Initial status: READY

Limitations:
QA60 does not explicitly remove cloud shadows.
The two optical acquisitions are from early July.
Export completion and local pixel validity
have not yet been verified.

Status: SUBMITTED


## Step 82 — Sentinel-2 Local Raster Verification

Date: 2026-10-23

Input file:
data/raw/sentinel2/monroe_lake_s2_july2017_composite.tif

File size: approximately 11 MB
Format: GeoTIFF
Compression: LZW
Data type: Float32

Raster dimensions: 1039 x 814
CRS: EPSG:32616
Origin: (540360.0, 4331540.0)
Pixel size: (20.0, -20.0)

Bands:
1. B2
2. B3
3. B4
4. B8
5. B11
6. valid_obs

Result:
Local GeoTIFF exists and metadata matches
the Sentinel-1 reference raster grid.

Next:
Verify exact alignment programmatically,
inspect optical observation counts and
evaluate band statistics.

Status: COMPLETED


## Step 83 — Sentinel-2 Pixel Validation

Date: 2026-10-23

Input:
data/raw/sentinel2/monroe_lake_s2_july2017_composite.tif

Spatial alignment with Sentinel-1: PASSED

Total raster pixels: 845746

Reported observation counts:
0 observations: 0
1 observation: 109563
2 observations: 732196

Sum of reported observation counts: 841759
Unaccounted pixels: 3987

Optical band statistics:

B2:
Min 641, Max 6178, Mean 1081.6134
Median 897.5

B3:
Min 416, Max 6166, Mean 977.7741
Median 801.0

B4:
Min 217, Max 6623, Mean 694.39667
Median 458.5

B8:
Min 224, Max 7446, Mean 3279.1326
Median 3698.5

B11:
Min 56, Max 8554, Mean 1730.2635
Median 1762.0

Reported valid pixels per optical band: 841759

Interpretation:
The optical and radar rasters share
the same spatial grid.

Most raster cells have two usable
optical observations, according to
the initial observation-count analysis.

Important unresolved issue:
3987 raster cells are not accounted for
by observation values 0, 1 or 2.

Next:
Inspect NoData values, pixel masks,
NaN values and unexpected counts.

Status: VALIDATION IN PROGRESS


## Step 84 — Investigation of Missing Optical Pixels

Date: 2026-10-23

Input:
data/raw/sentinel2/monroe_lake_s2_july2017_composite.tif

Total raster pixels: 845746
GDAL NoData value: None
GDAL mask flags: 1
Mask-valid pixels: 845746
Masked pixels: 0
NaN pixels: 3987
Infinite pixels: 0

Finite observation counts:
0 observations: 0
1 observation: 109563
2 observations: 732196

Unexpected finite observation values: 0

Finding:
The previously unaccounted 3987 pixels
contain NaN values in the valid_obs band.

The raster does not declare an explicit
NoData value, and GDAL reports all pixels
as mask-valid.

Decision:
Treat non-finite optical observation counts
as missing data and exclude these pixels
from the initial fused feature dataset.

Candidate pixels with >=1 observation:
841759 (approximately 99.53%).

Limitations:
This is a raster validity assessment,
not a complete cloud-shadow or model
accuracy assessment.

Status: COMPLETED


## Step 85 — Multisensor Feature Stack Creation

Date: 2026-10-23
Study area: Monroe Lake, Indiana
Period: July 2017

Output:
data/processed/monroe_lake_fused_features_july2017.tif

Input datasets:
Sentinel-1 July 2017 VV/VH median composite
Sentinel-2 July 2 and 7 QA60-masked composite

Spatial grid:
EPSG:32616
Resolution: 20 m
Dimensions: 1039 x 814

Predictor features:
1. VV
2. VH
3. B2
4. B3
5. B4
6. B8
7. B11
8. NDWI
9. MNDWI
10. NDVI

Additional quality band:
11. valid_obs

Spectral indices:
NDWI = (B3 - B8) / (B3 + B8)
MNDWI = (B3 - B11) / (B3 + B11)
NDVI = (B8 - B4) / (B8 + B4)

Total raster pixels: 845746
Valid fused pixels: 841759
Excluded pixels: 3987
Candidate pixel coverage: approximately 99.53%

Processing:
Checked spatial alignment.
Combined radar and optical measurements.
Calculated normalized-difference indices.
Preserved invalid feature values as NaN.
Exported 11-band Float32 GeoTIFF.

Limitations:
The composite is a preliminary feature product.
Optical cloud shadows have not been fully removed.
Radar and optical acquisitions differ in date.
Independent reference labels are not yet prepared.
Spatial train/test sampling is not yet performed.
Model accuracy has not been evaluated.

Status: CREATED
Next: Verify saved raster and prepare labels.


## Step 86 — Final Fused Feature Raster Validation

Date: 2026-10-23
Study area: Monroe Lake, Indiana

Input:
data/processed/monroe_lake_fused_features_july2017.tif

Raster dimensions: 1039 x 814
Band count: 11
CRS: EPSG:32616
Pixel resolution: 20 m

All bands contain 841759 finite pixels.

Spectral-index ranges:

NDWI:
Minimum: -0.7444933653
Maximum: 0.4738878012

MNDWI:
Minimum: -0.6759335399
Maximum: 0.8457446694

NDVI:
Minimum: -0.4438064098
Maximum: 0.8639881611

Complete feature pixels: 841759
Pixels missing any band: 3987

Results:
- Band count and descriptions verified.
- All spectral indices within [-1, 1].
- All 11 bands share the same finite-pixel count.
- Complete-feature pixel count matches expectation.

Conclusion:
The fused Sentinel-1 and Sentinel-2
feature raster passed structural and
numerical validation.

Limitations:
No independent classification accuracy
has been established.
Cloud-shadow screening remains incomplete.
Radar and optical dates are not identical.

Status: PASSED

Next:
Prepare provisional water/non-water labels
and spatially independent training samples.


## Step 87 — JRC Global Surface Water Inventory

Date: 2026-10-23
Study area: Monroe Lake, Indiana

Dataset:
JRC/GSW1_4/GlobalSurfaceWater

Available bands:
occurrence
change_abs
change_norm
seasonality
recurrence
transition
max_extent

Occurrence statistics within the NHD lake polygon:

Minimum: 0
Maximum: 99
Mean: 91.0820432906424

Interpretation:
JRC occurrence represents historical
water detection frequency, not
July 2017 water extent.

The mean is calculated over the
valid occurrence pixels included
in the reduction.

Proposed provisional-label thresholds:
Water: occurrence >= 90
Land: occurrence <= 5
Uncertain: 5 < occurrence < 90

These thresholds are experimental.
They do not constitute independent
ground truth.

Next:
Quantify candidate label availability
over the complete feature raster extent.

Status: COMPLETED


## Step 88 — JRC Candidate-Label Inventory

Date: 2026-10-23

Study area:
Monroe Lake buffered raster extent

Dataset:
JRC/GSW1_4/GlobalSurfaceWater

Provisional thresholds:
Water: occurrence >= 90
Land: occurrence <= 5
Uncertain: 5 < occurrence < 90

Earth Engine reduction results:
Water candidates: 79320
Land candidates: 113
Uncertain: 16550
Valid occurrence coverage: 95983

Water-to-land candidate ratio:
Approximately 702:1

Finding:
The provisional thresholds produce
severe class imbalance.

Important limitation:
The occurrence layer does not provide
valid values across the entire raster.
Missing occurrence values cannot be
automatically interpreted as land.

Decision:
Do not train Random Forest yet.
Investigate occurrence masking and
JRC max_extent coverage.

Next:
Step 89 - JRC coverage diagnostics.

Status: COMPLETED - LABEL STRATEGY UNDER REVIEW


## Step 89 — JRC Occurrence and Max-Extent Audit

Date: 2026-10-23
Study area: Monroe Lake buffered raster extent

Dataset:
JRC/GSW1_4/GlobalSurfaceWater

Total raster pixels: 845746

JRC coverage:
Ever-water pixels: 118769
Never-water pixels: 726977
Valid max_extent pixels: 845746
Valid occurrence pixels: 95983
Missing occurrence pixels: 726977

Finding:
The occurrence band has substantially
less coverage than the max_extent band.

The max_extent band identifies a large
candidate historical non-water region.

Important distinction:
Never classified as water is not equivalent
to independently confirmed land in July 2017.

Proposed weak-label rules:
Water: occurrence >= 90
Land: max_extent == 0
Uncertain: all other pixels

Decision:
Validate label consistency and overlap
before exporting training labels.

Status: COMPLETED


## Step 90 — Provisional JRC Label Consistency

Date: 2026-10-23

Study area:
Monroe Lake buffered raster extent

Dataset:
JRC/GSW1_4/GlobalSurfaceWater

Provisional weak-label definitions:
Water = occurrence >= 90
Land = max_extent == 0
Uncertain = neither condition

Reported Earth Engine counts:
Water: 79320
Land: 726977
Uncertain: 16663
Overlap: 0

Water/land overlap check: PASSED

Important finding:
The reported categories sum to 822960,
which is 22786 fewer than the expected
845746 raster pixels.

Decision:
Reconcile categorical counts using an
explicitly unmasked label image before
using labels for model training.

Limitations:
JRC-derived labels are historical weak
labels, not independent July 2017 truth.

Next:
Step 91 - Reconcile labels and submit
aligned label raster export.

Status: OVERLAP PASSED; COUNT AUDIT PENDING


## Step 91 — JRC Weak-Label Raster Export

Date: 2026-10-23
Study area: Monroe Lake, Indiana

Dataset:
JRC/GSW1_4/GlobalSurfaceWater

Label definitions:
0 = Provisional land
1 = Provisional water
255 = Uncertain

Reconciled counts:
Land: 726977
Water: 82956
Uncertain: 35813

Total counted pixels: 845746
Expected raster pixels: 845746

Pixel accounting: PASSED

Important observation:
The final categorical counts differ from
the earlier separate-condition reductions.
The discrepancy requires further
investigation before model training.

Earth Engine task ID:
64V5UTGE5XXBPZ6TV5MRCKLP

Initial task status: READY

Output:
monroe_lake_jrc_weak_labels.tif

Destination:
Google Drive / IndianaSurfaceWater

Status:
EXPORT SUBMITTED — COMPLETION PENDING

Next:
Check task completion and verify
the downloaded categorical raster.


## Step 92 — JRC Weak-Label Export Completion

Date: 2026-10-23

Earth Engine task ID:
64V5UTGE5XXBPZ6TV5MRCKLP

Final task status: COMPLETED
Error: None

Export filename:
monroe_lake_jrc_weak_labels.tif

Google Drive folder:
IndianaSurfaceWater

Interpretation:
Earth Engine successfully completed
the JRC weak-label raster export.

Important limitations:
The local GeoTIFF has not yet been verified.
The provisional labels are historical
JRC-derived weak labels, not independently
verified July 2017 ground truth.

Next:
Download the GeoTIFF and validate
its raster metadata, categorical values,
and spatial alignment.

Status: COMPLETED


## Step 93 — Local JRC Label Raster Verification

Date: 2026-10-23

File:
data/reference/monroe_lake_jrc_weak_labels.tif

File size: approximately 22 KB
Format: GeoTIFF
Compression: LZW
Data type: Byte
Band count: 1
Band description: weak_label

Raster dimensions: 1039 x 814
CRS: EPSG:32616
Pixel resolution: 20 m
Origin: (540360, 4331540)

Finding:
The label raster is present in the
expected project directory.

Its dimensions, CRS, origin and pixel
resolution match the feature raster
metadata.

Limitations:
Categorical pixel values have not yet
been independently counted locally.
Exact alignment will be checked in Step 94.

Status: COMPLETED


## Step 94 — Local Weak-Label and Feature Alignment

Date: 2026-10-23
Study area: Monroe Lake, Indiana

Feature raster:
data/processed/monroe_lake_fused_features_july2017.tif

Weak-label raster:
data/reference/monroe_lake_jrc_weak_labels.tif

Spatial alignment: PASSED

Actual label counts:
Land (0): 726977
Water (1): 82956
Uncertain (255): 35813

Counts with complete features:
Land: 722990
Water: 82956
Uncertain: 35813

Complete feature pixels: 841759
Usable labeled pixels: 805946
Missing feature pixels: 3987

All missing-feature pixels occur in
the provisional land category.

Conclusion:
The local feature and weak-label rasters
are aligned and have consistent counts.

Limitations:
JRC labels represent historical weak
supervision, not independent July 2017
ground truth.

Next:
Inventory 2 km spatial blocks before
constructing train/test partitions.

Status: PASSED


## Step 95 — Spatial Block Inventory

Date: 2026-10-23
Study area: Monroe Lake, Indiana

Spatial reference: EPSG:32616
Pixel resolution: 20 m
Spatial block size: 2000 m

Inventory output:
results/inventory/monroe_spatial_blocks_2km.csv

Results:
Total spatial blocks: 99
Blocks containing water: 32
Blocks containing land: 99
Blocks containing both classes: 32
Blocks with at least 100 water pixels: 26

Pixel reconciliation:
Water: 82956
Land: 722990
Uncertain: 35813
Missing features: 3987
Total: 845746

All inventory reconciliation checks passed.

Interpretation:
Water candidates are spatially concentrated
in a subset of the study-area blocks.

Decision:
Use block-level train/test partitioning,
rather than random pixel-level splitting.

Proposed initial split:
70% training blocks
30% testing blocks
Random seed: 42

Limitations:
Spatial separation alone does not provide
independent reference-label accuracy.
Adjacent blocks may retain spatial dependence.

Status: PASSED


## Step 96 — Reproducible Spatial Train/Test Split

Date: 2026-10-23
Study area: Monroe Lake, Indiana

Input:
results/inventory/monroe_spatial_blocks_2km.csv

Output:
results/inventory/monroe_spatial_split_2km_seed42.csv

Method:
2 km projected spatial blocks
Block-level stratification by water presence
Random seed: 42
Approximately 70/30 train/test allocation

Training:
69 blocks
22 blocks containing water
58314 water pixels
509369 land pixels
567683 labeled pixels

Testing:
30 blocks
10 blocks containing water
24642 water pixels
213621 land pixels
238263 labeled pixels

Total:
99 spatial blocks
805946 usable labeled pixels

Interpretation:
Both partitions contain both classes.
No spatial block is assigned to both partitions.
Test class proportions remain close to training.

Limitations:
Adjacent blocks may remain spatially correlated.
JRC weak-label agreement is not independent
July 2017 classification accuracy.

Status: PASSED


---

## Monroe Lake Surface-Water Detection: Steps 98A–100

### Study Configuration

- Study area: Monroe Lake, Indiana
- Study period: July 2017
- Coordinate reference system: EPSG:32616
- Spatial resolution: 20 m
- Raster dimensions: 1,039 × 814 pixels
- Total raster cells: 845,746
- Predictors: Sentinel-1 VV and VH; Sentinel-2 B2, B3, B4, B8, B11; NDWI, MNDWI, NDVI
- Reference labels: JRC Global Surface Water (historical weak labels)
- Spatial partition: 2 km blocks, random seed 42
- Training blocks: 69
- Testing blocks: 30

### Step 98A: NHD Polygon Verification

Input:
data/reference/hydrography/monroe_lake_nhd.geojson

Verification results:
- GeoJSON type: FeatureCollection
- Number of features: 1
- Geometry type: Polygon
- Status: PASSED

The NHD polygon represents the reference lake boundary.
It is not independent ground truth for July 2017.

### Step 98B: Boundary-Based Sampling Audit

The NHD polygon was transformed to EPSG:32616 and
rasterized onto the Sentinel feature grid.

A 60 m approximate shoreline exclusion was applied
using raster-cell distance transforms.

Selection criteria:

Water candidates:
- Inside the lake polygon
- At least approximately 60 m from the rasterized shoreline
- JRC water label = 1
- Complete satellite predictor values

Land candidates:
- Outside the lake polygon
- At least approximately 60 m from the rasterized shoreline
- JRC land label = 0
- Complete satellite predictor values

Audit results:
- Lake polygon pixels: 112,310
- Interior pixels after exclusion: 90,653
- Exterior pixels after exclusion: 710,274

Training candidates:
- Water: 56,380
- Land: 495,014

Testing candidates:
- Water: 24,162
- Land: 206,143

Status: PASSED

### Step 98C: Revised Training Dataset

Output:
data/processed/monroe_rf_training_lakebuffer60m_seed42.npz

Training sample:
- Water: 20,000 pixels
- Land: 20,000 pixels
- Total: 40,000 pixels
- Predictors: 10
- Random seed: 42
- Sampling without replacement
- Test pixels included: 0

Each pixel represents a 20 m × 20 m raster cell,
equivalent to 400 square meters.

The original randomly sampled dataset was preserved
for future comparison.

Status: PASSED

### Step 99: Random Forest Training

Model:
RandomForestClassifier

Configuration:
- n_estimators: 200
- max_features: sqrt
- min_samples_leaf: 2
- random_state: 42
- n_jobs: 4

Model output:
results/models/monroe_rf_lakebuffer60m_july2017_seed42.joblib

Feature importance (impurity-based):
- VH: 0.2586
- NDWI: 0.2350
- VV: 0.1970
- NDVI: 0.1389
- MNDWI: 0.0905
- B8: 0.0485
- B11: 0.0280
- B2: 0.0022
- B4: 0.0010
- B3: 0.0004

VH, NDWI, and VV together account for approximately
69.1% of reported impurity-based feature importance.

These values do not establish causal importance or
the superiority of sensor fusion.

Model reload verification: PASSED

### Step 100: Spatial Holdout Evaluation

Evaluation source:
JRC Global Surface Water historical weak labels

Test configuration:
- Held-out spatial blocks: 30
- Evaluated pixels: 238,263
- JRC land pixels: 213,621
- JRC water pixels: 24,642

Confusion matrix:
- True negatives: 213,360
- False positives: 261
- False negatives: 1
- True positives: 24,641

Evaluation metrics:
- Accuracy: 0.9989
- Balanced accuracy: 0.9994
- Water precision: 0.9895
- Water recall: 1.0000 (rounded)
- Water F1: 0.9947
- Cohen's kappa: 0.9941

Output:
results/evaluation/monroe_rf_lakebuffer60m_test_jrc_metrics.json

Status: PASSED

### Interpretation

The Random Forest achieved very high agreement with
JRC weak labels on held-out spatial blocks.

The result demonstrates agreement with the reference
labeling scheme, not independently validated
July 2017 surface-water detection accuracy.

### Methodological Limitations

1. JRC historical labels are not date-specific July 2017
   observations.

2. Training samples were selected using both the NHD
   polygon and JRC labels.

3. Training and testing blocks belong to the same lake
   and may exhibit spatial dependence.

4. JRC-uncertain pixels were excluded from evaluation.

5. Shoreline exclusion makes the training samples
   comparatively easy and does not establish performance
   on shoreline or mixed pixels.

6. Optical and radar observations were collected on
   different dates during July 2017.

7. Random Forest impurity-based feature importance can
   be affected by correlated predictors.

8. The model has not yet been validated against
   independently interpreted satellite imagery or
   field observations.

### Next Experiment: Step 101

Compare Random Forest with an MNDWI > 0 baseline
using the identical held-out evaluation pixels.

Future work:
- Analyze false positives and false negatives
- Produce spatial prediction and probability maps
- Conduct independent reference validation
- Test additional dates and seasonal conditions
- Extend the analysis to surface-water dynamics
  and wet/dry-year characterization


---

## Step 101: Random Forest vs. MNDWI Baseline

Study area: Monroe Lake, Indiana
Study period: July 2017
Evaluation: 30 held-out 2 km spatial blocks
Test pixels: 238,263
Reference: JRC Global Surface Water historical weak labels

### Methods

Method 1: Random Forest
- 200 trees
- 10 Sentinel-1/Sentinel-2 predictors
- 40,000 balanced training samples
- NHD lake boundary and JRC agreement
- Approximately 60 m shoreline exclusion

Method 2: MNDWI baseline
- Water if MNDWI > 0
- Land otherwise
- Fixed threshold, not optimized

Both methods were evaluated on identical held-out pixels.

### Results

Metric                 Random Forest   MNDWI
Accuracy               0.9989          0.9843
Balanced accuracy      0.9994          0.9573
Water precision        0.9895          0.9251
Water recall           1.0000          0.9231
Water F1               0.9947          0.9241
Cohen's kappa          0.9941          0.9154

Random Forest confusion matrix:
TN = 213360
FP = 261
FN = 1
TP = 24641

MNDWI confusion matrix:
TN = 211779
FP = 1842
FN = 1894
TP = 22748

Total disagreements:
Random Forest = 262
MNDWI = 3736

Relative reduction in disagreements:
Approximately 93.0%

Water F1 improvement:
0.0706 absolute, or 7.06 percentage points.

### Interpretation

The Random Forest demonstrated substantially higher
agreement with historical JRC labels than MNDWI > 0.

This supports the usefulness of the multi-feature
classifier for the current Monroe Lake experiment.

It does not independently establish that:
- Sentinel-1/Sentinel-2 fusion outperforms each sensor alone
- The model generalizes to other lakes or years
- The model accurately detects July 2017 water everywhere
- The model can identify wet and dry years
- The model can forecast future surface-water dynamics

### Limitations

1. Evaluation uses historical JRC weak labels.
2. The MNDWI threshold was fixed at zero, not tuned.
3. Spatial dependence may remain across adjacent blocks.
4. Uncertain JRC labels were excluded.
5. No independent date-specific ground truth was used.
6. The comparison covers one lake and one study period.

### Evidence Files

Random Forest metrics:
results/evaluation/monroe_rf_lakebuffer60m_test_jrc_metrics.json

MNDWI metrics:
results/evaluation/monroe_mndwi_threshold0_test_jrc_metrics.json

Status: Step 101 PASSED.

