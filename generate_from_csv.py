import os
import csv
import trimesh
from wing_deformer import apply_wing_deformations

def validate_stl_for_cfd(filepath):
    """Checks an STL for common artifacts that crash OpenFOAM."""
    try:
        mesh = trimesh.load_mesh(filepath)
        if mesh.is_empty:
            return False, "Mesh is completely empty."
        if not mesh.is_watertight:
            return False, "Not watertight (contains holes or non-manifold edges)."
        if not mesh.is_winding_consistent:
            return False, "Inconsistent face winding (flipped normals)."
        if mesh.volume < 1e-6:
            return False, "Zero or negative volume (crushed or inverted mesh)."
        return True, "Valid"
    except Exception as e:
        return False, f"File read error: {str(e)}"

def parse_row_to_tweaks(row_dict):
    """Converts a CSV row dictionary into the PyGeM transformation format."""
    move_points = {}
    move_syms = {}
    functions = []

    for col_name, value_str in row_dict.items():
        if col_name in ['filename', 'is_valid', 'failure_reason', '']:
            continue
            
        try:
            val = float(value_str)
        except ValueError:
            continue
            
        # Skip zero movements to optimize execution
        if val == 0.0:
            continue

        if col_name.startswith('pt_'):
            parts = col_name[3:].rsplit('_', 1) 
            p_name = parts[0]
            axis = parts[1]
            if p_name not in move_points:
                move_points[p_name] = {"action": "move_point", "point_name": p_name, "dx": 0.0, "dy": 0.0, "dz": 0.0}
            move_points[p_name][axis] = val

        elif col_name.startswith('sym_'):
            parts = col_name[4:].rsplit('_', 1)
            b_name = parts[0]
            axis = parts[1]
            if b_name not in move_syms:
                move_syms[b_name] = {"action": "move_symmetric_pair", "base_name": b_name, "dx": 0.0, "dy": 0.0, "dz": 0.0}
            move_syms[b_name][axis] = val

        elif col_name.startswith('func_'):
            func_name = col_name[5:]
            functions.append({"action": func_name, "amount": val})

    return functions + list(move_points.values()) + list(move_syms.values())

def generate_dataset_from_csv(input_stl="FrontWing.stl", input_csv="predicted_better_wings.csv", output_dir="Predicted_Dataset"):
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Reading transformations from {input_csv}...")
    
    # Read the input CSV
    with open(input_csv, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        input_headers = reader.fieldnames
        
    if not input_headers:
        print("Error: Could not read headers from the CSV.")
        return

    # Setup the output log file
    log_file_path = os.path.join(output_dir, "validation_log.csv")
    log_file = open(log_file_path, "w")
    
    # Write new headers (Originals + filename + validation flags)
    output_headers = ["filename"] + input_headers + ["is_valid", "failure_reason"]
    # Ensure no duplicates in headers just in case
    output_headers = list(dict.fromkeys(output_headers)) 
    log_file.write(",".join(output_headers) + "\n")

    print(f"Found {len(rows)} wing configurations to generate.\n")

    # Generate the dataset
    for i, row in enumerate(rows):
        filename = f"pred_wing_{i+1:03d}.stl"
        filepath = os.path.join(output_dir, filename)
        
        # 1. Parse the row into exactly what wing_deformer expects
        my_tweaks = parse_row_to_tweaks(row)
        
        print(f"--- Generating {filename} ({i+1}/{len(rows)}) ---")
        
        # 2. Call the function from wing_deformer.py
        apply_wing_deformations(
            input_stl=input_stl, 
            output_stl=filepath, 
            transforms=my_tweaks, 
            show_plot=False, 
            radius=0.2 
        )

        # 3. Validate the mesh
        is_valid, reason = validate_stl_for_cfd(filepath)
        
        # 4. Prepare the row for the output CSV
        output_row = [filename]
        for header in input_headers:
            output_row.append(str(row.get(header, "")))
        
        if is_valid:
            print("✅ Mesh is valid and ready for OpenFOAM!")
            output_row.extend(["True", "None"])
        else:
            print(f"❌ MESH REJECTED: {reason}")
            os.remove(filepath) # Delete the broken STL
            output_row.extend(["False", reason])
        
        # Log to CSV
        log_file.write(",".join(output_row) + "\n")
        
    log_file.close()
    print(f"\nGeneration complete! Valid wings and log saved in '{output_dir}'.")

if __name__ == "__main__":
    # You can change the filenames here if needed
    generate_dataset_from_csv(
        input_stl="FrontWing.stl", 
        input_csv="01_pred_old.csv", 
        output_dir="Wings_IT3"
    )