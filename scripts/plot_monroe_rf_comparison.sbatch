#!/bin/bash
#SBATCH --job-name=monroe_rf_fig
#SBATCH --output=logs/monroe_rf_fig_%j.out
#SBATCH --error=logs/monroe_rf_fig_%j.err
#SBATCH --time=00:10:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --account=r02219

set -euo pipefail

cd /N/project/persl/indiana_surface_water/anaprad
source .venv/bin/activate

export MPLBACKEND=Agg

python scripts/plot_monroe_rf_comparison.py
