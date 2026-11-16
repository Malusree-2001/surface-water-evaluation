#!/bin/bash
#SBATCH --job-name=water_test
#SBATCH --account=r02219
#SBATCH --partition=general
#SBATCH --qos=allocated
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:05:00
#SBATCH --output=logs/test_%j.out

module load python/3.12.11

echo "=== Indiana Surface Water HPC Test ==="
echo "Compute node: $(hostname)"
echo "Date: $(date)"
echo "Python: $(python --version)"

python - <<'PY'
import numpy as np

# Simulate a tiny 2D raster
raster = np.array([
    [0, 1, 1, 0],
    [0, 1, 0, 0],
    [1, 1, 0, 0],
    [0, 0, 0, 1]
])

# 1 represents water; 0 represents non-water
water_pixels = np.sum(raster == 1)
total_pixels = raster.size

print("Total pixels:", total_pixels)
print("Water pixels:", water_pixels)
print("Water fraction:", water_pixels / total_pixels)
PY
