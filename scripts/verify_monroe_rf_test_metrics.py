import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import rasterio
from sklearn.metrics import confusion_matrix, accuracy_score

feature_path = "data/processed/monroe_lake_fused_features_july2017.tif"
label_path = "data/reference/monroe_lake_jrc_weak_labels.tif"
split_path = "results/inventory/monroe_spatial_split_2km_seed42.csv"
model_path = "results/models/monroe_rf_lakebuffer60m_july2017_seed42.joblib"

output_path = Path(
    "results/evaluation/monroe_rf_independent_test_recalculation.json"
)

# Load original saved model
saved = joblib.load(model_path)
model = saved["model"]

# Load spatial block assignments
split = pd.read_csv(split_path)
test_blocks = set(
    zip(
        split.loc[split["split"] == "test", "block_x"],
        split.loc[split["split"] == "test", "block_y"]
    )
)

# Read aligned rasters
with rasterio.open(feature_path) as src:
    features = src.read()
    transform = src.transform
    height, width = src.height, src.width

with rasterio.open(label_path) as src:
    labels = src.read(1)

# Use only the 10 predictors expected by the saved model
X = np.moveaxis(features[:10], 0, -1)

# Build geographic coordinates for every pixel center
rows, cols = np.indices((height, width))

xs = transform.c + (cols + 0.5) * transform.a
ys = transform.f + (rows + 0.5) * transform.e

# Reconstruct spatial block IDs
block_x = np.floor(xs / 2000).astype(int)
block_y = np.floor(ys / 2000).astype(int)

# Select pixels belonging to test blocks
test_mask = np.zeros((height, width), dtype=bool)

for bx, by in test_blocks:
    test_mask |= (block_x == bx) & (block_y == by)

# Select usable reference labels
label_mask = (labels == 0) | (labels == 1)

# Select pixels with finite model features
feature_mask = np.isfinite(X).all(axis=2)

# Final evaluation population
evaluation_mask = test_mask & label_mask & feature_mask

X_test = X[evaluation_mask]
y_test = labels[evaluation_mask]

# Predict using the saved Random Forest
predictions = model.predict(X_test)

tn, fp, fn, tp = confusion_matrix(
    y_test, predictions, labels=[0, 1]
).ravel()

results = {
    "evaluation_type": "recalculated_JRC_weak_label_agreement",
    "test_blocks": len(test_blocks),
    "test_pixels": int(len(y_test)),
    "jrc_land": int((y_test == 0).sum()),
    "jrc_water": int((y_test == 1).sum()),
    "tn": int(tn),
    "fp": int(fp),
    "fn": int(fn),
    "tp": int(tp),
    "accuracy": float(accuracy_score(y_test, predictions))
}

output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, "w") as f:
    json.dump(results, f, indent=2)

print("=== INDEPENDENT TEST METRIC RECALCULATION ===")
for key, value in results.items():
    print(f"{key}: {value}")

print("\nSaved:", output_path)
