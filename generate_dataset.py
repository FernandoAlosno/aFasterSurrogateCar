import os
from scipy.stats import qmc
from wing_deformer import apply_wing_deformations
import trimesh

def validate_stl_for_cfd(filepath):
    """
    Checks an STL for common artifacts that crash OpenFOAM.
    Returns: (bool is_valid, str reason)
    """
    try:
        # Load the mesh
        mesh = trimesh.load_mesh(filepath)
        
        # 1. Empty mesh check
        if mesh.is_empty:
            return False, "Mesh is completely empty."
            
        # 2. Watertight check (Crucial for snappyHexMesh to find inside/outside)
        if not mesh.is_watertight:
            return False, "Not watertight (contains holes or non-manifold edges)."
            
        # 3. Normal winding (If faces point inwards, CFD will mesh the wrong side)
        if not mesh.is_winding_consistent:
            return False, "Inconsistent face winding (flipped normals)."
            
        # 4. Volume check (Did the RBF accidentally crush the wing into a flat 2D plane?)
        if mesh.volume < 1e-6:
            return False, "Zero or negative volume (crushed or inverted mesh)."

        return True, "Valid"
        
    except Exception as e:
        return False, f"File read error: {str(e)}"


def generate_lhs_dataset(input_stl="FrontWing.stl", num_samples=300):
    output_dir = "Wings_Dataset"
    os.makedirs(output_dir, exist_ok=True)

    params_config = [
        # Body points
        {"action": "move_point", "type": "move_point", "point_name": "body_nose_front", "axis": "dx", "bound": [-0.03, 0.03]},
        {"action": "move_point", "type": "move_point", "point_name": "body_nose_front", "axis": "dz", "bound": [-0.00, 0.03]},


        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "body_front_wing", "axis": "dx", "bound": [-0.03, 0.03]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "body_front_wing", "axis": "dy", "bound": [-0.03, 0.03]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "body_front_wing", "axis": "dz", "bound": [-0.00, 0.03]},

        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "body_mid_wing", "axis": "dx", "bound": [-0.03, 0.03]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "body_mid_wing", "axis": "dy", "bound": [-0.03, 0.03]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "body_mid_wing", "axis": "dz", "bound": [-0.00, 0.03]},

        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "body_back_wing", "axis": "dx", "bound": [-0.03, 0.03]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "body_back_wing", "axis": "dy", "bound": [-0.03, 0.03]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "body_back_wing", "axis": "dz", "bound": [-0.03, 0.03]},


        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "body_mid", "axis": "dx", "bound": [-0.03, 0.03]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "body_mid", "axis": "dy", "bound": [-0.03, 0.03]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "body_mid", "axis": "dz", "bound": [-0.03, 0.03]},

        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "body_back", "axis": "dx", "bound": [-0.03, 0.03]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "body_back", "axis": "dy", "bound": [-0.03, 0.03]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "body_back", "axis": "dz", "bound": [-0.03, 0.03]},


        {"action": "move_point", "type": "move_point", "point_name": "body_top_wing", "axis": "dx", "bound": [-0.03, 0.03]},
        {"action": "move_point", "type": "move_point", "point_name": "body_top_wing", "axis": "dz", "bound": [-0.03, 0.03]},

        {"action": "move_point", "type": "move_point", "point_name": "body_top_mid", "axis": "dx", "bound": [-0.03, 0.03]},
        {"action": "move_point", "type": "move_point", "point_name": "body_top_mid", "axis": "dz", "bound": [-0.03, 0.03]},

        {"action": "move_point", "type": "move_point", "point_name": "body_top_back", "axis": "dx", "bound": [-0.03, 0.03]},
        {"action": "move_point", "type": "move_point", "point_name": "body_top_back", "axis": "dz", "bound": [-0.03, 0.03]},

        # Wing points

        {"action": "move_point", "type": "move_point", "point_name": "wing_point", "axis": "dx", "bound": [-0.03, 0.03]},
        {"action": "move_point", "type": "move_point", "point_name": "wing_point", "axis": "dz", "bound": [0.00, 0.03]},


        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l1_r1", "axis": "dx", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l1_r1", "axis": "dy", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l1_r1", "axis": "dz", "bound": [0.00, 0.02]},

        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l1_r2", "axis": "dx", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l1_r2", "axis": "dy", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l1_r2", "axis": "dz", "bound": [0.00, 0.02]},

        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l1_r3", "axis": "dx", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l1_r3", "axis": "dy", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l1_r3", "axis": "dz", "bound": [0.00, 0.02]},

        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l2_r1", "axis": "dx", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l2_r1", "axis": "dy", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l2_r1", "axis": "dz", "bound": [-0.00, 0.02]},

        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l2_r2", "axis": "dx", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l2_r2", "axis": "dy", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l2_r2", "axis": "dz", "bound": [-0.00, 0.02]},

        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l2_r3", "axis": "dx", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l2_r3", "axis": "dy", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l2_r3", "axis": "dz", "bound": [-0.00, 0.02]},

        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l3_r1", "axis": "dx", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l3_r1", "axis": "dy", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l3_r1", "axis": "dz", "bound": [-0.00, 0.02]},

        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l3_r2", "axis": "dx", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l3_r2", "axis": "dy", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l3_r2", "axis": "dz", "bound": [-0.00, 0.02]},

        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l3_r3", "axis": "dx", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l3_r3", "axis": "dy", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l3_r3", "axis": "dz", "bound": [-0.00, 0.02]},

        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l4_r1", "axis": "dx", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l4_r1", "axis": "dy", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l4_r1", "axis": "dz", "bound": [-0.02, 0.02]},

        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l4_r2", "axis": "dx", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l4_r2", "axis": "dy", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l4_r2", "axis": "dz", "bound": [-0.02, 0.02]},

        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l4_r3", "axis": "dx", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l4_r3", "axis": "dy", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l4_r3", "axis": "dz", "bound": [-0.02, 0.02]},

        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l5_r1", "axis": "dx", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l5_r1", "axis": "dy", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l5_r1", "axis": "dz", "bound": [-0.02, 0.02]},

        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l5_r2", "axis": "dx", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l5_r2", "axis": "dy", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l5_r2", "axis": "dz", "bound": [-0.02, 0.02]},

        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l5_r3", "axis": "dx", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l5_r3", "axis": "dy", "bound": [-0.02, 0.02]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "wing_l5_r3", "axis": "dz", "bound": [-0.02, 0.02]},

        #Endplate points

        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "end_down_front", "axis": "dx", "bound": [-0.03, 0.03]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "end_down_front", "axis": "dy", "bound": [-0.03, 0.03]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "end_down_front", "axis": "dz", "bound": [-0.03, 0.03]},

        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "end_down_back", "axis": "dx", "bound": [-0.03, 0.03]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "end_down_back", "axis": "dy", "bound": [-0.03, 0.03]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "end_down_back", "axis": "dz", "bound": [-0.03, 0.03]},

        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "end_up_front", "axis": "dx", "bound": [-0.03, 0.03]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "end_up_front", "axis": "dy", "bound": [-0.03, 0.03]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "end_up_front", "axis": "dz", "bound": [-0.03, 0.03]},

        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "end_up_back", "axis": "dx", "bound": [-0.03, 0.03]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "end_up_back", "axis": "dy", "bound": [-0.03, 0.03]},
        {"action": "move_symmetric_pair", "type": "move_symmetric_pair", "base_name": "end_up_back", "axis": "dz", "bound": [-0.03, 0.03]},

    ]
    
    print(f"Setting up Latin Hypercube Sampling for {num_samples} wings...")

    # Extract bounds for the LHS
    lower_bounds = [p["bound"][0] for p in params_config]
    upper_bounds = [p["bound"][1] for p in params_config]
    
    # Automatically Generate the CSV Header based on your config
    csv_headers = ["filename"]
    for p in params_config:
        if p["type"] == "function":
            csv_headers.append(f"func_{p['action']}")
        elif p["type"] == "move_point":
            csv_headers.append(f"pt_{p['point_name']}_{p['axis']}")
        elif p["type"] == "move_symmetric_pair":
            csv_headers.append(f"sym_{p['base_name']}_{p['axis']}") 
    
    # Open the log file and write the headers
    log_file = open(os.path.join(output_dir, "parameters_log.csv"), "w")
    log_file.write(",".join(csv_headers) + "\n")

    # Generate the LHS matrix
    sampler = qmc.LatinHypercube(d=len(params_config))
    sample = sampler.random(n=num_samples)
    scaled_samples = qmc.scale(sample, lower_bounds, upper_bounds)
    
    # Generate the dataset
    for i in range(num_samples):
        filename = f"wing_{i+1:03d}.stl"
        filepath = os.path.join(output_dir, filename)
        
        my_tweaks = []
        csv_row = [filename]
        
        # Build the tweaks list and CSV row for this specific wing
        for j, p in enumerate(params_config):
            val = scaled_samples[i][j]
            csv_row.append(f"{val:.6f}")
            
            if p["type"] == "function":
                my_tweaks.append({"action": p["action"], "amount": val})
                
            elif p["type"] in ["move_point", "move_symmetric_pair"]:
                dx, dy, dz = 0.0, 0.0, 0.0

                if p["axis"] == "dx": dx = val
                elif p["axis"] == "dy": dy = val
                elif p["axis"] == "dz": dz = val
                
                if p["type"] == "move_point":
                    my_tweaks.append({
                        "action": "move_point",
                        "point_name": p["point_name"],
                        "dx": dx, "dy": dy, "dz": dz
                    })
                elif p["type"] == "move_symmetric_pair":
                    my_tweaks.append({
                        "action": "move_symmetric_pair",
                        "base_name": p["base_name"],
                        "dx": dx, "dy": dy, "dz": dz
                    })
        
        print(f"\n--- Generating {filename} ---")
        
        # Call the function from wing_deformer.py script
        apply_wing_deformations(
            input_stl=input_stl, 
            output_stl=filepath, 
            transforms=my_tweaks, 
            show_plot=False, 
            radius=0.2 
        )

        # Validate the mesh
        is_valid, reason = validate_stl_for_cfd(filepath)
        
        if is_valid:
            print("✅ Mesh is valid and ready for OpenFOAM!")
            # Add 'Valid' flag to the CSV row
            csv_row.append("True")
            csv_row.append("None")
        else:
            print(f"❌ MESH REJECTED: {reason}")
            # Delete the broken STL
            os.remove(filepath) 
            
            # Log the failure in the CSV so the ML model knows this geometry is impossible
            csv_row.append("False") 
            csv_row.append(reason)
        
        # Log the completed row to the CSV
        log_file.write(",".join(csv_row) + "\n")
        
    log_file.close()
    print(f"\nDataset generation complete! Generated {num_samples} wings in '{output_dir}'.")

if __name__ == "__main__":
    generate_lhs_dataset(input_stl="FrontWing.stl", num_samples=300)
