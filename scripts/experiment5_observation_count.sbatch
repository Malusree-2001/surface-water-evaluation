#!/bin/bash
#SBATCH --job-name=monroe_exp5a
#SBATCH --output=logs/monroe_exp5a_%j.out
#SBATCH --error=logs/monroe_exp5a_%j.err
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00

set -euo pipefail

cd /N/project/persl/indiana_surface_water/anaprad
source .venv/bin/activate

export OMP_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1

echo "=== MONROE LAKE RANDOM FOREST EXPERIMENT ==="
echo "Compute node: $(hostname)"
echo "Start time: $(date)"

python -u scripts/experiment5_observation_count_sensitivity.py

echo "End time: $(date)"
echo "=== EXPERIMENT FINISHED ==="
