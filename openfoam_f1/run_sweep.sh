#!/bin/bash

# Navigate into the template folder where the run script lives
cd f2_template

# Variable to hold the ID of the previous job
PREV_JOB_ID=""

# Loop through the STLs
for stl_path in ../Geometries/wing_*.stl; do
    
    # Get just the filename (e.g., wing_001.stl)
    stl_file=$(basename "$stl_path")
    
    if [ -z "$PREV_JOB_ID" ]; then
        # First job: Submit normally and capture its SLURM Job ID
        PREV_JOB_ID=$(sbatch --parsable run_all.sh "$stl_file")
        echo "Submitted $stl_file with Job ID: $PREV_JOB_ID"
    else
        # Subsequent jobs: Tell SLURM to wait for the previous job to finish
        PREV_JOB_ID=$(sbatch --parsable --dependency=afterany:$PREV_JOB_ID run_all.sh "$stl_file")
        echo "Submitted $stl_file with Job ID: $PREV_JOB_ID (Waiting on previous)"
    fi

done

echo "All 50 jobs have been daisy-chained in the queue!"
cd ..
