#!/bin/bash
#SBATCH --job-name=monroe_sample_size
#SBATCH --output=logs/monroe_sample_size_%j.out
#SBATCH --error=logs/monroe_sample_size_%j.err
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00

set -euo pipefail

cd /N/project/persl/indiana_surface_water/anaprad

source .venv/bin/activate

export OMP_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1

echo "=== MONROE LAKE TRAINING-DATA SENSITIVITY ==="
echo "Compute node: $(hostname)"
echo "Start time: $(date)"

python -u scripts/ablation_monroe_rf_sample_sizes.py

echo "End time: $(date)"
echo "=== EXPERIMENT FINISHED ==="
