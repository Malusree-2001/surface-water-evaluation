import os
import json

import numpy as np
import pandas as pd
import rasterio

from scipy.ndimage import distance_transform_edt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    balanced_accuracy_score,
    jaccard_score,
)

FEATURE_PATH = "data/processed/monroe_lake_fused_features_july2017.tif"
LABEL_PATH = "data/reference/monroe_lake_jrc_monthly_july2017.tif"
FOLD_PATH = "results/inventory/monroe_monthly_jrc_spatial_folds_5.csv"

OUTPUT_DIR = "results/monthly_jrc_rf_cv"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SEED = 42
BUFFER_METERS = 200
SAMPLES_PER_CLASS = 20000

print("Loading satellite features...", flush=True)

with rasterio.open(FEATURE_PATH) as src:
    data = src.read()
    transform = src.transform
    height, width = src.height, src.width
    pixel_size = src.res
    feature_names = list(src.descriptions[:-1])

with rasterio.open(LABEL_PATH) as src:
    labels = src.read(1)

folds = pd.read_csv(FOLD_PATH)

valid = (
    (data[-1] > 0)
    & np.all(np.isfinite(data[:-1]), axis=0)
    & np.isin(labels, [0, 1])
)

rows, cols = np.indices((height, width))

x = transform.c + (cols + 0.5) * transform.a
y = transform.f + (rows + 0.5) * transform.e

block_x = np.floor(x / 2000).astype(np.int32)
block_y = np.floor(y / 2000).astype(np.int32)

fold_map = np.full((height, width), -1, dtype=np.int8)

for row in folds.itertuples():
    mask = (
        (block_x == row.block_x)
        & (block_y == row.block_y)
    )
    fold_map[mask] = row.fold

assert np.all(fold_map[valid] >= 0)

# Convert raster from bands x rows x columns to
# rows x columns x features.
X = np.moveaxis(data[:-1], 0, -1)

results = []

for fold in range(5):

    print(f"\n=== FOLD {fold} ===", flush=True)

    rng = np.random.default_rng(SEED + fold)

    validation = valid & (fold_map == fold)
    training = valid & (fold_map != fold)

    distance = distance_transform_edt(
        ~validation,
        sampling=pixel_size
    )

    training &= distance > BUFFER_METERS

    land_positions = np.flatnonzero(
        training & (labels == 0)
    )

    water_positions = np.flatnonzero(
        training & (labels == 1)
    )

    land_sample = rng.choice(
        land_positions,
        size=min(SAMPLES_PER_CLASS, len(land_positions)),
        replace=False
    )

    water_sample = rng.choice(
        water_positions,
        size=min(SAMPLES_PER_CLASS, len(water_positions)),
        replace=False
    )

    training_positions = np.concatenate(
        [land_sample, water_sample]
    )

    rng.shuffle(training_positions)

    validation_positions = np.flatnonzero(validation)

    X_flat = X.reshape(-1, X.shape[-1])
    y_flat = labels.reshape(-1)

    X_train = X_flat[training_positions]
    y_train = y_flat[training_positions]

    X_val = X_flat[validation_positions]
    y_val = y_flat[validation_positions]

    print("Training samples:", len(y_train), flush=True)
    print("Validation samples:", len(y_val), flush=True)

    model = RandomForestClassifier(
        n_estimators=200,
        min_samples_leaf=2,
        max_features="sqrt",
        random_state=SEED,
        n_jobs=4
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_val)

    tn, fp, fn, tp = confusion_matrix(
        y_val,
        predictions,
        labels=[0, 1]
    ).ravel()

    metrics = {
        "fold": fold,
        "train_samples": int(len(y_train)),
        "validation_samples": int(len(y_val)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "precision": float(
            precision_score(y_val, predictions, zero_division=0)
        ),
        "recall": float(
            recall_score(y_val, predictions, zero_division=0)
        ),
        "f1": float(
            f1_score(y_val, predictions, zero_division=0)
        ),
        "iou": float(
            jaccard_score(y_val, predictions, zero_division=0)
        ),
        "balanced_accuracy": float(
            balanced_accuracy_score(y_val, predictions)
        ),
    }

    results.append(metrics)

    print(json.dumps(metrics, indent=2), flush=True)

    del model, X_train, X_val, y_train, y_val

results_df = pd.DataFrame(results)

results_df.to_csv(
    f"{OUTPUT_DIR}/fold_metrics.csv",
    index=False
)

print("\n=== FIVE-FOLD RESULTS ===", flush=True)
print(results_df.to_string(index=False), flush=True)

print("\nMEAN METRICS", flush=True)

for metric in [
    "precision",
    "recall",
    "f1",
    "iou",
    "balanced_accuracy"
]:
    print(
        f"{metric}: "
        f"{results_df[metric].mean():.4f} "
        f"+/- {results_df[metric].std():.4f}",
        flush=True
    )

print("\nEXPERIMENT COMPLETE", flush=True)
