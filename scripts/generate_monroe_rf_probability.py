import joblib
import numpy as np
import rasterio

MODEL_PATH = "results/models/monroe_rf_lakebuffer60m_july2017_seed42.joblib"
INPUT_PATH = "data/processed/monroe_lake_fused_features_july2017.tif"
OUTPUT_PATH = "results/maps/monroe_rf_water_probability_july2017.tif"

saved = joblib.load(MODEL_PATH)
model = saved["model"]
feature_names = saved["feature_names"]

with rasterio.open(INPUT_PATH) as src:
    descriptions = list(src.descriptions)

    # Select predictor bands by their names, not by assumed positions.
    band_indices = [descriptions.index(name) + 1 for name in feature_names]

    print("Predictor bands:", feature_names)
    print("Band indices:", band_indices)

    if model.n_features_in_ != len(band_indices):
        raise ValueError("Model feature count does not match raster features.")

    if 1 not in model.classes_:
        raise ValueError("Water class (1) not found in model.")

    water_class_index = list(model.classes_).index(1)

    profile = src.profile.copy()
    profile.update(
        count=1,
        dtype="float32",
        nodata=np.nan,
        compress="deflate"
    )

    # Refuse to overwrite an existing probability raster.
    import os
    if os.path.exists(OUTPUT_PATH):
        raise FileExistsError(f"Output already exists: {OUTPUT_PATH}")

    with rasterio.open(OUTPUT_PATH, "w", **profile) as dst:
        dst.set_band_description(1, "RF_water_probability")

        for _, window in src.block_windows(1):
            features = src.read(band_indices, window=window)
            valid_obs = src.read(descriptions.index("valid_obs") + 1, window=window)

            height, width = features.shape[1:]
            X = features.reshape(len(band_indices), -1).T

            # Predict only where observations exist and all features are finite.
            valid = (
                np.all(np.isfinite(X), axis=1)
                & np.isfinite(valid_obs.ravel())
                & (valid_obs.ravel() > 0)
            )

            probabilities = np.full(X.shape[0], np.nan, dtype=np.float32)

            if valid.any():
                probabilities[valid] = model.predict_proba(
                    X[valid]
                )[:, water_class_index].astype(np.float32)

            dst.write(probabilities.reshape(height, width), 1, window=window)

print("Saved:", OUTPUT_PATH)
