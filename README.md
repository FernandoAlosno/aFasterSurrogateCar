# aFasterSurrogateCar

This project is a computational aerodynamics pipeline designed to optimize the Lift-to-Drag ratio ($C_l/C_d$) of a wing. It achieves this by procedurally generating different wing deformations, running Computational Fluid Dynamics (CFD) simulations, and leveraging surrogate modeling to find the absolute optimal geometry.

## How does it work

The complete pipeline follows a rigorous process from geometry generation to machine learning optimization. Currently, the geometry generation and validation modules are fully implemented.

![Pipeline](photos_wing/Pipeline.jpg)

### 1. Design of Experiments (LHS)
To ensure we explore the design space efficiently without generating redundant wing shapes, we use **Latin Hypercube Sampling (LHS)** via `scipy.stats.qmc`. This generates a highly uniform distribution of deformation parameters.


### 2. Wing Deformation (RBF)
The core manipulation is handled by `wing_deformer.py`, which utilizes **Radial Basis Functions (RBF)** from the PyGeM library. By defining anchor points and control points on the original wing geometry (`FrontWing.stl`), we can seamlessly warp the mesh to flare endplates, steepen flaps, or adjust nose height without breaking the underlying surface smoothness.
![Wing Points](photos_wing/Wing_points.jpg)
<!--![Board Points](photos_wing/Board_points.jpg)-->

*Safety Feature:* The deformer includes a floor collision avoidance system. If a deformation pushes the wing too close to the ground (below the safe clearance), it automatically shifts the entire mesh upward along the Z-axis.

### 3. Mesh Validation for CFD
Before any geometry is sent to the supercomputer, it must pass a strict validation check in `generate_dataset.py`. The script evaluates the STL for:
* Watertightness (no holes or non-manifold edges)
* Consistent face winding (normals pointing outward)
* Positive volume (ensuring the RBF didn't crush or invert the mesh)

Invalid meshes (like the one below) are automatically rejected and logged, saving valuable compute hours.
![Goofy Wing](photos_wing/Goofy_wing.jpg)

### 4. CFD Simulation on MN5 (WIP)
Valid meshes are passed to **OpenFOAM** running on the MareNostrum 5 (MN5) supercomputer. The aerodynamics of the wing are simulated to extract Lift ($C_l$) and Drag ($C_d$) coefficients.
![Parallelism Metrics](photos_wing/Parallelism.jpg)
![First Simulation](photos_wing/First_simulation.jpg)

### 5. Surrogate Modeling (WIP)
Because running OpenFOAM on thousands of variations is computationally expensive, the resulting dataset will be used to train a **Surrogate Model** (e.g., Neural Network or Gaussian Process). This model will quickly predict the $C_l/C_d$ ratio for new parameter combinations, allowing us to find the optimal shape in seconds rather than days.

---

## How to use it

### Repository Structure
* **`generate_dataset.py`**: The main driver for bulk-generating wing variations. It applies LHS, calls the deformer, validates the meshes, and logs successful generations.
* **`wing_deformer.py`**: The RBF deformation engine. Can be used standalone or imported into other scripts.
* **`extract_to_json.py`**: A utility script to parse a specific row from a generated `parameters_log.csv` and convert it into a JSON configuration for easy reproducibility.
* **`main.py`**: A simple testing script to try out individual tweaks quickly.

---

## An example usage

### 1. Generating a Dataset
To generate a batch of wings using Latin Hypercube Sampling and automatically validate them for CFD:
```bash
python generate_dataset.py
```

This will create a Wings_Dataset/ directory containing the valid STLs and a CSV log.
### 2. Extracting a specific configuration

If you find a wing in your dataset that performed exceptionally well (or poorly) and want to extract its exact parameters:
```Bash
python extract_to_json.py -c parameters_log.csv -r 5 -o my_tweaks.json
# (Where -r 5 is the 5th wing generated in your dataset).
```
### 3. How to use the Wing Deformer manually
From the terminal:

With plotting enabled (to visually inspect the deformation):
Bash

```bash
python wing_deformer.py -i FrontWing.stl -o DeformedWing.stl -t tweaks.json -p
```
Without plotting (runs silently, faster for automated generation):
Bash
```bash
python wing_deformer.py -i FrontWing.stl -o DeformedWing.stl -t tweaks.json
```
From a Python script:

```python
from wing_deformer import apply_wing_deformations

# Define your tweaks right in the code
my_tweaks = [
    {"action": "flare_endplates", "amount": 40},
    {"action": "adjust_nose_height", "amount": 50}
]

# Run it! Set show_plot=False to keep it running quietly in the background
final_stl = apply_wing_deformations(
    input_stl="FrontWing.stl", 
    output_stl="Variation_001.stl", 
    transforms=my_tweaks, 
    show_plot=False
)