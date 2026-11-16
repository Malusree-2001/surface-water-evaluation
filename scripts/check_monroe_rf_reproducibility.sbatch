#!/bin/bash
#SBATCH --job-name=monroe_rf_repro
#SBATCH --output=logs/monroe_rf_repro_%j.out
#SBATCH --error=logs/monroe_rf_repro_%j.err
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G

set -euo pipefail

cd /N/project/persl/indiana_surface_water/anaprad
source .venv/bin/activate

echo "=== Monroe Lake RF Reproducibility ==="
echo "Compute node: $(hostname)"
echo "Start time: $(date)"

python scripts/check_monroe_rf_reproducibility.py

echo "End time: $(date)"
