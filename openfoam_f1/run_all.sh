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

STL_FILE=$1

if [ -z "$STL_FILE" ]; then
    echo "Error: No STL file provided."
    exit 1
fi

BASENAME=$(basename "$STL_FILE" .stl)
echo "Starting simulation for: $BASENAME"


# Preparation
./Allclean
mkdir constant/triSurface
cp "../Geometries/$STL_FILE" constant/triSurface/FrontWing.stl

# Load OpenFOAM module
module purge
module load oneapi/2023.2.0
module load  openfoam/v2312
source /apps/GPP/OPENFOAM/v2312/INTEL/IMPI/etc/bashrc
source $WM_PROJECT_DIR/bin/tools/RunFunctions

echo "Starting sequential pre-processing..."
surfaceFeatureExtract
blockMesh
decomposePar -decomposeParDict system/decomposeParDict.6 -force

echo "Starting parallel meshing and solving..."
srun snappyHexMesh -decomposeParDict system/decomposeParDict.6 -overwrite -parallel
srun topoSet -decomposeParDict system/decomposeParDict.6 -parallel

restore0Dir -processor

srun patchSummary -decomposeParDict system/decomposeParDict.6 -parallel
srun potentialFoam -decomposeParDict system/decomposeParDict.6 -writephi -parallel
srun checkMesh -decomposeParDict system/decomposeParDict.6 -writeFields '(nonOrthoAngle)' -constant -parallel

srun simpleFoam -decomposeParDict system/decomposeParDict.6 -parallel

echo "Reconstructing mesh and fields..."
reconstructParMesh -constant
reconstructPar -latestTime

echo "Extracting coefficients..."

mkdir -p ../Results_Summary2
cp postProcessing/forceCoeffs1/0/coefficient.dat "../Results_Summary/${BASENAME}_coeffs.dat"

echo "Simulation complete. Wiping directory to save space..."

# Reclean porsiaca
./Allclean

echo "Job for $BASENAME finished successfully!"
