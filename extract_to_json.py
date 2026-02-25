import csv
import json
import argparse

def convert_csv_to_json(csv_file, row_index, output_json):
    """
    Reads a specific row from the dataset CSV and converts it into 
    the exact JSON format required by wing_deformer.py
    """
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if row_index < 0 or row_index >= len(rows):
        print(f"Error: Row index {row_index} is out of bounds. The CSV has {len(rows)} rows.")
        return

    target_row = rows[row_index]
    
    move_points = {}
    move_syms = {}
    functions = []

    for col_name, value_str in target_row.items():
        # Skip non-numerical metadata columns
        if col_name in ['filename', 'is_valid', 'failure_reason', '']:
            continue
            
        try:
            val = float(value_str)
        except ValueError:
            continue
            
        # Skip zero movements to keep the JSON clean and fast!
        if val == 0.0:
            continue

        # Parse Single Points (e.g., pt_body_nose_front_dx)
        if col_name.startswith('pt_'):
            # Split off 'pt_' and then separate the name from the axis
            parts = col_name[3:].rsplit('_', 1) 
            p_name = parts[0]
            axis = parts[1] # dx, dy, or dz
            
            if p_name not in move_points:
                move_points[p_name] = {"action": "move_point", "point_name": p_name, "dx": 0.0, "dy": 0.0, "dz": 0.0}
            move_points[p_name][axis] = val

        # Parse Symmetric Pairs (e.g., sym_body_front_wing_dz)
        elif col_name.startswith('sym_'):
            parts = col_name[4:].rsplit('_', 1)
            b_name = parts[0]
            axis = parts[1]
            
            if b_name not in move_syms:
                move_syms[b_name] = {"action": "move_symmetric_pair", "base_name": b_name, "dx": 0.0, "dy": 0.0, "dz": 0.0}
            move_syms[b_name][axis] = val

        # Parse Global Functions (e.g., func_steepen_upper_flaps)
        elif col_name.startswith('func_'):
            func_name = col_name[5:]
            functions.append({"action": func_name, "amount": val})

    # Combine everything into a single list
    final_tweaks = functions + list(move_points.values()) + list(move_syms.values())

    # Save to JSON
    with open(output_json, 'w') as f:
        json.dump(final_tweaks, f, indent=4)
        
    print(f"✅ Successfully extracted {len(final_tweaks)} transformations from row {row_index} into '{output_json}'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a row from your dataset CSV into a PyGeM JSON config.")
    parser.add_argument("-c", "--csv", required=True, help="Path to your parameters_log.csv")
    parser.add_argument("-r", "--row", type=int, required=True, help="Row index to extract (0 is the first wing)")
    parser.add_argument("-o", "--output", default="extracted_tweaks.json", help="Output JSON filename")
    args = parser.parse_args()

    convert_csv_to_json(args.csv, args.row, args.output)



"python extract_to_json.py -c Wing_Dataset_LHS/parameters_log.csv -r 2 -o wing3_config.json"