#!/bin/bash
#SBATCH --job-name=monroe_rf_prob
#SBATCH --output=logs/monroe_rf_prob_%j.out
#SBATCH --error=logs/monroe_rf_prob_%j.err
#SBATCH --time=00:20:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G

set -euo pipefail

cd /N/project/persl/indiana_surface_water/anaprad
source .venv/bin/activate

python scripts/generate_monroe_rf_probability.py
