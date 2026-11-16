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
    jaccard_score,
    balanced_accuracy_score,
)

FEATURE_PATH = "data/processed/monroe_lake_fused_features_july2017.tif"
LABEL_PATH = "data/reference/monroe_lake_jrc_monthly_july2017.tif"
FOLD_PATH = "results/inventory/monroe_monthly_jrc_spatial_folds_5.csv"

OUTPUT_DIR = "results/monthly_jrc_rf_ablation"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SEED = 42
BUFFER_METERS = 200
SAMPLES_PER_CLASS = 20000

EXPERIMENTS = {
    "A1_S1_only": [
        "VV", "VH"
    ],
    "A2_S2_only": [
        "B2", "B3", "B4", "B8", "B11"
    ],
    "A3_S2_indices": [
        "B2", "B3", "B4", "B8", "B11",
        "NDWI", "MNDWI", "NDVI"
    ],
    "A4_S1_S2_bands": [
        "VV", "VH",
        "B2", "B3", "B4", "B8", "B11"
    ],
    "A5_all_features": [
        "VV", "VH",
        "B2", "B3", "B4", "B8", "B11",
        "NDWI", "MNDWI", "NDVI"
    ]
}

print("=== RANDOM FOREST FEATURE-GROUP ABLATION ===", flush=True)

with rasterio.open(FEATURE_PATH) as src:
    data = src.read()
    names = list(src.descriptions)
    transform = src.transform
    height, width = src.height, src.width
    pixel_size = src.res

with rasterio.open(LABEL_PATH) as src:
    labels = src.read(1)

folds = pd.read_csv(FOLD_PATH)

assert names[-1] == "valid_obs"

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

X = np.moveaxis(data[:-1], 0, -1)
X_flat = X.reshape(-1, X.shape[-1])
y_flat = labels.reshape(-1)

all_results = []

# Outer loop over folds ensures identical sampled training
# pixels across all feature-group experiments.
for fold in range(5):

    print(f"\n=== SPATIAL FOLD {fold} ===", flush=True)

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

    y_train = y_flat[training_positions]
    y_val = y_flat[validation_positions]

    for experiment_name, selected_features in EXPERIMENTS.items():

        indices = [names.index(name) for name in selected_features]

        X_train = X_flat[training_positions][:, indices]
        X_val = X_flat[validation_positions][:, indices]

        print(
            f"Training {experiment_name} "
            f"with {len(selected_features)} features...",
            flush=True
        )

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
            "experiment": experiment_name,
            "fold": fold,
            "n_features": len(selected_features),
            "train_samples": len(y_train),
            "validation_samples": len(y_val),
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
            "precision": precision_score(
                y_val, predictions, zero_division=0
            ),
            "recall": recall_score(
                y_val, predictions, zero_division=0
            ),
            "f1": f1_score(
                y_val, predictions, zero_division=0
            ),
            "iou": jaccard_score(
                y_val, predictions, zero_division=0
            ),
            "balanced_accuracy": balanced_accuracy_score(
                y_val, predictions
            )
        }

        all_results.append(metrics)

        print(
            f"F1={metrics['f1']:.4f}, "
            f"IoU={metrics['iou']:.4f}, "
            f"Precision={metrics['precision']:.4f}, "
            f"Recall={metrics['recall']:.4f}",
            flush=True
        )

        del model, X_train, X_val

    # Save intermediate results after every completed fold.
    pd.DataFrame(all_results).to_csv(
        f"{OUTPUT_DIR}/fold_metrics.csv",
        index=False
    )

results_df = pd.DataFrame(all_results)

summary = (
    results_df
    .groupby("experiment")
    .agg(
        n_features=("n_features", "first"),
        precision_mean=("precision", "mean"),
        precision_std=("precision", "std"),
        recall_mean=("recall", "mean"),
        recall_std=("recall", "std"),
        f1_mean=("f1", "mean"),
        f1_std=("f1", "std"),
        iou_mean=("iou", "mean"),
        iou_std=("iou", "std"),
        balanced_accuracy_mean=("balanced_accuracy", "mean")
    )
    .reset_index()
)

summary.to_csv(
    f"{OUTPUT_DIR}/feature_group_comparison.csv",
    index=False
)

print("\n=== FEATURE-GROUP ABLATION SUMMARY ===", flush=True)
print(summary.to_string(index=False), flush=True)

print("\nABLATION EXPERIMENT COMPLETE", flush=True)
