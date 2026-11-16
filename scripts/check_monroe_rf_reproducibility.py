import json
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.base import clone

# Input files
model_path = Path(
    "results/models/monroe_rf_lakebuffer60m_july2017_seed42.joblib"
)
archive_path = Path(
    "data/processed/monroe_rf_training_lakebuffer60m_seed42.npz"
)

# Output file
output_path = Path(
    "results/evaluation/monroe_rf_reproducibility_seed42.json"
)

# Load the original model
saved = joblib.load(model_path)
original_model = saved["model"]

# Load the archived training samples
with np.load(archive_path, allow_pickle=False) as data:
    X = data["X"]
    y = data["y"]
    feature_names = data["feature_names"].tolist()

# Verify feature compatibility
assert feature_names == saved["feature_names"]
assert X.shape == (40000, 10)
assert np.isfinite(X).all()

print("=== RANDOM FOREST REPRODUCIBILITY TEST ===", flush=True)
print("Training samples:", len(y), flush=True)
print("Features:", len(feature_names), flush=True)
print("scikit-learn version:", sklearn.__version__, flush=True)

# Clone the original model's configuration.
# The cloned model has the same hyperparameters but no fitted trees.
reproduced_model = clone(original_model)

# Retrain on archived samples
print("\nTraining reproduced model...", flush=True)
reproduced_model.fit(X, y)
print("Training completed.", flush=True)

# Compare predictions
original_predictions = original_model.predict(X)
reproduced_predictions = reproduced_model.predict(X)

prediction_agreement = float(
    np.mean(original_predictions == reproduced_predictions)
)

# Compare water probabilities
original_probabilities = original_model.predict_proba(X)[:, 1]
reproduced_probabilities = reproduced_model.predict_proba(X)[:, 1]

absolute_difference = np.abs(
    original_probabilities - reproduced_probabilities
)

results = {
    "evaluation_type": "training_archive_reproducibility",
    "samples_compared": int(len(y)),
    "features": feature_names,
    "sklearn_version": sklearn.__version__,
    "prediction_agreement": prediction_agreement,
    "mean_absolute_probability_difference": float(
        absolute_difference.mean()
    ),
    "max_absolute_probability_difference": float(
        absolute_difference.max()
    ),
    "original_training_agreement": float(
        np.mean(original_predictions == y)
    ),
    "reproduced_training_agreement": float(
        np.mean(reproduced_predictions == y)
    )
}

output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, "w") as f:
    json.dump(results, f, indent=2)

print("\n=== RESULTS ===", flush=True)

for key, value in results.items():
    print(f"{key}: {value}", flush=True)

print("\nSaved results to:", output_path, flush=True)
