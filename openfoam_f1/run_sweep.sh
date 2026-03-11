#!/bin/bash

cd f2_template

PREV_JOB_ID=""

for stl_path in ../Geometries/wing_*.stl; do
    
    # Get filename
    stl_file=$(basename "$stl_path")
    
    if [ -z "$PREV_JOB_ID" ]; then
        # Submit normally
        PREV_JOB_ID=$(sbatch --parsable run_all.sh "$stl_file")
        echo "Submitted $stl_file with Job ID: $PREV_JOB_ID"
    else
        # Wait for the previous job to finish
        PREV_JOB_ID=$(sbatch --parsable --dependency=afterany:$PREV_JOB_ID run_all.sh "$stl_file")
        echo "Submitted $stl_file with Job ID: $PREV_JOB_ID (Waiting on previous)"
    fi

done

echo "All 50 jobs have been daisy-chained in the queue!"
cd ..
