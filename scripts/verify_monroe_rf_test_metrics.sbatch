#!/bin/bash
#SBATCH --job-name=monroe_rf_eval
#SBATCH --output=logs/monroe_rf_eval_%j.out
#SBATCH --error=logs/monroe_rf_eval_%j.err
#SBATCH --time=00:20:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G

set -euo pipefail

cd /N/project/persl/indiana_surface_water/anaprad
source .venv/bin/activate

echo "=== Monroe Lake RF Test Evaluation ==="
echo "Compute node: $(hostname)"
echo "Start time: $(date)"

python scripts/verify_monroe_rf_test_metrics.py

echo "End time: $(date)"
