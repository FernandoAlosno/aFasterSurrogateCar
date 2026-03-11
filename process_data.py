import os
import csv

def append_aerodynamic_data(csv_file, dat_folder, output_file):
    # 1. Read the original CSV
    # Using 'utf-8-sig' cleanly removes any hidden Byte Order Marks from the file
    with open(csv_file, 'r', newline='', encoding='utf-8-sig') as f:
        reader = list(csv.reader(f))
    
    if not reader:
        print("Error: CSV file is empty.")
        return

    headers = reader[0]
    rows = reader[1:]

    # 2. Define the new columns we want to add
    new_columns = ['Cd', 'Cl', 'CmPitch', 'L_D_Ratio', 'Reached_500']
    
    # Append new columns to header if they aren't already there
    for col in new_columns:
        if col not in headers:
            headers.append(col)
            
    # Find the exact index of our columns
    idx_cd = headers.index('Cd')
    idx_cl = headers.index('Cl')
    idx_cmpitch = headers.index('CmPitch')
    idx_ld = headers.index('L_D_Ratio')
    idx_reached_500 = headers.index('Reached_500')

    success_count = 0

    # 3. Process each row in the CSV
    for row in rows:
        # The filename is in the first column (index 0)
        stl_filename = row[0].strip()
        
        # Skip empty rows
        if not stl_filename:
            continue
            
        # Transform "wing_001.stl" into "wing_001_coeffs.dat"
        base_name = stl_filename.replace('.stl', '')
        dat_filename = f"{base_name}_coeffs.dat"
        
        # Build the full path to the .dat file
        dat_filepath = os.path.join(dat_folder, dat_filename)
        
        # Check if the dat file exists in the specified folder
        if not os.path.exists(dat_filepath):
            print(f"Skipping {stl_filename}: Could not find '{dat_filename}' in folder '{dat_folder}'")
            continue
            
        # 4. Parse the corresponding .dat file
        with open(dat_filepath, 'r') as f_dat:
            lines = f_dat.readlines()
            
        # Read from bottom up to find the last valid line of data
        last_data_line = None
        for line in reversed(lines):
            line = line.strip()
            # Ignore empty lines and OpenFOAM comment lines
            if line and not line.startswith('#'):
                last_data_line = line
                break
                
        if last_data_line:
            parts = last_data_line.split()
            # Ensure the line has enough columns to grab Cd, Cl, and CmPitch
            if len(parts) >= 8:
                # Get the iteration number (first column) to check if it reached 500
                try:
                    iteration = int(parts[0])
                    reached_500 = iteration >= 500
                except ValueError:
                    reached_500 = False

                cd = float(parts[1])
                cl = float(parts[4])
                cm_pitch = float(parts[7])
                ld_ratio = cl / cd if cd != 0 else 0.0
                
                # Expand the row in case it doesn't have empty slots for the new columns yet
                while len(row) < len(headers):
                    row.append("")
                
                # Insert the values into the correct slots
                row[idx_cd] = cd
                row[idx_cl] = cl
                row[idx_cmpitch] = cm_pitch
                row[idx_ld] = ld_ratio
                row[idx_reached_500] = reached_500
                
                success_count += 1
                print(f"Matched {stl_filename} -> Added Cd: {cd:.4f}, Cl: {cl:.4f}, CmPitch: {cm_pitch:.4f}, L/D: {ld_ratio:.4f}, Reached 500: {reached_500}")
            else:
                print(f"Error: {dat_filename} has an unexpected format.")

    # 5. Write everything to the new CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"\nDone! Successfully updated {success_count} rows.")
    print(f"Saved the results to: {output_file}")


if __name__ == "__main__":
    # --- CONFIGURATION ---
    CSV_NAME = 'validation_log_IT3.csv'
    
    # Put the path to the folder containing the .dat files here. 
    # Use '.' if they are in the exact same folder as the script.
    # If they are inside a folder, change this to the folder name (e.g., 'dat_files')
    DAT_FOLDER = 'Results_Summary/' 
    
    OUTPUT_NAME = 'IT3_Results.csv'
    # ---------------------
    
    append_aerodynamic_data(CSV_NAME, DAT_FOLDER, OUTPUT_NAME)