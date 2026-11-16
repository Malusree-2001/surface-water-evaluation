#!/bin/bash
#SBATCH --job-name=monroe_ablation
#SBATCH --output=logs/monroe_ablation_%j.out
#SBATCH --error=logs/monroe_ablation_%j.err
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00

set -euo pipefail

cd /N/project/persl/indiana_surface_water/anaprad
source .venv/bin/activate

export OMP_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1

echo "=== MONROE LAKE FEATURE-GROUP ABLATION ==="
echo "Compute node: $(hostname)"
echo "Start time: $(date)"

python -u scripts/ablation_monroe_rf_feature_groups.py

echo "End time: $(date)"
echo "=== ABLATION EXPERIMENT FINISHED ==="
