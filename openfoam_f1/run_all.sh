#!/bin/bash
#SBATCH --job-name=OF_Sweep
#SBATCH --partition=gpp             # Target the General Purpose Partition
#SBATCH --nodes=1                   # Number of nodes you want to use
#SBATCH --ntasks-per-node=112       # MN5 GPP has 112 cores per node
#SBATCH --time=00:30:00             # Max wall-clock time (HH:MM:SS)
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err
#SBATCH --qos=gp_debug
#SBATCH --account=nct_293

# Capture the STL file passed from the submit script
STL_FILE=$1

# If no STL was passed, exit to prevent running a blank case
if [ -z "$STL_FILE" ]; then
    echo "Error: No STL file provided."
    exit 1
fi

BASENAME=$(basename "$STL_FILE" .stl)
echo "Starting simulation for: $BASENAME"

# 0. Pre-Run Cleanup & Geometry Setup
# Ensure the folder is spotless before starting
./Allclean
mkdir constant/triSurface
# Copy the specific geometry for this run and name it FrontWing.stl 
# so snappyHexMeshDict doesn't need to be changed
cp "../Geometries/$STL_FILE" constant/triSurface/FrontWing.stl

# 1. Load the OpenFOAM module
module purge
module load oneapi/2023.2.0
module load  openfoam/v2312
source /apps/GPP/OPENFOAM/v2312/INTEL/IMPI/etc/bashrc
source $WM_PROJECT_DIR/bin/tools/RunFunctions

# 2. Sequential Pre-processing
echo "Starting sequential pre-processing..."
surfaceFeatureExtract
blockMesh
decomposePar -decomposeParDict system/decomposeParDict.6 -force

# 3. Parallel Execution
echo "Starting parallel meshing and solving..."
srun snappyHexMesh -decomposeParDict system/decomposeParDict.6 -overwrite -parallel
srun topoSet -decomposeParDict system/decomposeParDict.6 -parallel

restore0Dir -processor

srun patchSummary -decomposeParDict system/decomposeParDict.6 -parallel
srun potentialFoam -decomposeParDict system/decomposeParDict.6 -writephi -parallel
srun checkMesh -decomposeParDict system/decomposeParDict.6 -writeFields '(nonOrthoAngle)' -constant -parallel

# Replace simpleFoam if you are using a different solver
srun simpleFoam -decomposeParDict system/decomposeParDict.6 -parallel

# 4. Sequential Post-processing
echo "Reconstructing mesh and fields..."
reconstructParMesh -constant
reconstructPar -latestTime

# 5. Extract Data & Post-Run Cleanup
echo "Extracting coefficients..."
# Ensure the results directory exists one level up
mkdir -p ../Results_Summary2

# NOTE: Verify this path matches your forceCoeffs output!
# simpleFoam puts forceCoeffs in postProcessing/forceCoeffs/0/coefficient.dat by default
cp postProcessing/forceCoeffs1/0/coefficient.dat "../Results_Summary/${BASENAME}_coeffs.dat"

echo "Simulation complete. Wiping directory to save space..."
./Allclean

echo "Job for $BASENAME finished successfully!"
