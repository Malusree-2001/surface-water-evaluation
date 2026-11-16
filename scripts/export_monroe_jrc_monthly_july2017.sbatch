#!/bin/bash
#SBATCH --job-name=jrc_monthly
#SBATCH --output=logs/jrc_monthly_%j.out
#SBATCH --error=logs/jrc_monthly_%j.err
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:20:00

set -euo pipefail

cd /N/project/persl/indiana_surface_water/anaprad
source .venv/bin/activate

python scripts/export_monroe_jrc_monthly_july2017.py
