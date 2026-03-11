import json
import argparse
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from pygem import RBF
from smithers import io
import plotly.graph_objects as go

class WingController:
    def __init__(self):
        self.points = {}
        self.deltas = {}
    
    def setup_default_points(self):
        """Loads your specific front wing anchor and control points."""
        # Reference points
        self.add_point('anchor_rear_up', 2, 0, 0.78)
        self.add_point('anchor_rear_down', 2, 0, 0.25)

        # Body points
        self.add_point('body_nose_front', -0.17, 0, 0.053)

        self.add_point('body_front_wing_left', -0.12, -0.11, 0.06)
        self.add_point('body_front_wing_right', -0.12, 0.11, 0.06)
        self.add_point('body_mid_wing_left', 0.03, -0.13, 0.09)
        self.add_point('body_mid_wing_right', 0.03, 0.13, 0.09)
        self.add_point('body_back_wing_left', 0.17, -0.14, 0.19)
        self.add_point('body_back_wing_right', 0.17, 0.14, 0.19)

        self.add_point('body_mid_left', 0.546, -0.15, 0.32)
        self.add_point('body_mid_right', 0.546, 0.15, 0.32)
        self.add_point('body_back_left', 1.34, -0.17, 0.5)
        self.add_point('body_back_right', 1.34, 0.17, 0.5)

        self.add_point('body_top_wing', 0.126, 0, 0.25)
        self.add_point('body_top_mid', 0.468, 0, 0.42)
        self.add_point('body_top_back', 1.28, 0, 0.687)

        # Wing points
        self.add_point('wing_point', -0.248, 0, 0.04)

        self.add_point('wing_l1_r1_left', -0.135, -0.42, 0.03)
        self.add_point('wing_l1_r1_right', -0.135, 0.42, 0.03)
        self.add_point('wing_l1_r2_left', 0, -0.797, 0.03)
        self.add_point('wing_l1_r2_right', 0, 0.797, 0.03)
        self.add_point('wing_l1_r3_left', 0.1, -1.08, 0.024)
        self.add_point('wing_l1_r3_right', 0.1, 1.08, 0.024)

        self.add_point('wing_l2_r1_left', -0.02, -0.407, 0.058)
        self.add_point('wing_l2_r1_right', -0.02, 0.407, 0.058)
        self.add_point('wing_l2_r2_left', 0.15, -0.76, 0.06)
        self.add_point('wing_l2_r2_right', 0.15, 0.76, 0.06)
        self.add_point('wing_l2_r3_left', 0.21, -1.036, 0.053)
        self.add_point('wing_l2_r3_right', 0.21, 1.036, 0.053)

        self.add_point('wing_l3_r1_left', 0.07, -0.374, 0.092)
        self.add_point('wing_l3_r1_right', 0.07, 0.374, 0.092)
        self.add_point('wing_l3_r2_left', 0.255, -0.72, 0.091)
        self.add_point('wing_l3_r2_right', 0.255, 0.72, 0.091)
        self.add_point('wing_l3_r3_left', 0.3, -1.05, 0.078)
        self.add_point('wing_l3_r3_right', 0.3, 1.05, 0.078)

        self.add_point('wing_l4_r1_left', 0.164, -0.4, 0.145)
        self.add_point('wing_l4_r1_right', 0.164, 0.4, 0.145)
        self.add_point('wing_l4_r2_left', 0.36, -0.736, 0.1456)
        self.add_point('wing_l4_r2_right', 0.36, 0.736, 0.1456)
        self.add_point('wing_l4_r3_left', 0.386, -1.1, 0.11)
        self.add_point('wing_l4_r3_right', 0.386, 1.1, 0.11)

        self.add_point('wing_l5_r1_left', 0.228, -0.404, 0.193)
        self.add_point('wing_l5_r1_right', 0.228, 0.404, 0.193)
        self.add_point('wing_l5_r2_left', 0.415, -0.742, 0.206)
        self.add_point('wing_l5_r2_right', 0.415, 0.742, 0.206)
        self.add_point('wing_l5_r3_left', 0.45, -1.092, 0.1384)
        self.add_point('wing_l5_r3_right', 0.45, 1.092, 0.1384)

        # Endplate points

        self.add_point('end_down_front_left', 0.134, -1.258, 0.129)
        self.add_point('end_down_front_right', 0.134, 1.258, 0.129)
        self.add_point('end_down_back_left', 0.466, -1.242, 0.1679)
        self.add_point('end_down_back_right', 0.466, 1.242, 0.1679)

        self.add_point('end_up_front_left', 0.2778, -1.249, 0.352)
        self.add_point('end_up_front_right', 0.2778, 1.249, 0.352)
        self.add_point('end_up_back_left', 0.467, -1.24, 0.392)
        self.add_point('end_up_back_right', 0.467, 1.24, 0.392)


    # --- ADD POINT ---
    def add_point(self, name, x, y, z):
        self.points[name] = np.array([x, y, z], dtype=float)
        self.deltas[name] = np.array([0, 0, 0], dtype=float)
        
    def reset_deformations(self):
        for name in self.deltas:
            self.deltas[name] = np.array([0, 0, 0], dtype=float)


    # --- POINT TRANSFORMATIONS ---
    def move_point(self, point_name, dx, dy, dz):
        """
        Moves a specific individual point by exact X, Y, Z amounts.
        """
        if point_name in self.deltas:
            self.deltas[point_name][0] += dx
            self.deltas[point_name][1] += dy
            self.deltas[point_name][2] += dz
        else:
            print(f"Warning: Point '{point_name}' not found!")

    def move_symmetric_pair(self, base_name, dx, dy, dz):
        """
        Moves a left/right pair of points symmetrically.
        Automatically finds the '_left' and '_right' versions of the base_name.
        Mirrors the Y-axis (span) movement so they pull apart or push together symmetrically.
        """
        left_name = f"{base_name}_left"
        right_name = f"{base_name}_right"
        
        # Apply to left side (Y movement is inverted for symmetry)
        if left_name in self.deltas:
            self.deltas[left_name][0] += dx
            self.deltas[left_name][1] -= dy  # Mirror the Y direction!
            self.deltas[left_name][2] += dz
        else:
            print(f"Warning: Symmetric point '{left_name}' not found!")
            
        # Apply to right side
        if right_name in self.deltas:
            self.deltas[right_name][0] += dx
            self.deltas[right_name][1] += dy
            self.deltas[right_name][2] += dz
        else:
            print(f"Warning: Symmetric point '{right_name}' not found!")


    def get_arrays(self):
        orig_list = []
        def_list = []
        for name in self.points:
            orig_pos = self.points[name]
            movement = self.deltas[name]
            orig_list.append(orig_pos)
            def_list.append(orig_pos + movement)
        return np.array(orig_list), np.array(def_list)



def plot_wing(data, rbf=None):
    """Visualizes the wing and RBF vectors using plotly."""
    points = np.array(data['points'])
    cells = np.array(data['cells'])
    
    # 1. Render the Wing Mesh
    fig = go.Figure(data=[go.Mesh3d(
        x=points[:, 0], y=points[:, 1], z=points[:, 2],
        i=cells[:, 0], j=cells[:, 1], k=cells[:, 2],
        color='blue', opacity=0.3, flatshading=True, name='Wing'
    )])
    
    # 2. Render the RBF Points and Vectors
    if rbf is not None:
        orig_pts = rbf.original_control_points
        def_pts = rbf.deformed_control_points
        
        # Original points (Green)
        fig.add_trace(go.Scatter3d(
            x=orig_pts[:, 0], y=orig_pts[:, 1], z=orig_pts[:, 2],
            mode='markers', marker=dict(color='green', size=6), name='Original'
        ))
        
        # Deformed points (Red)
        fig.add_trace(go.Scatter3d(
            x=def_pts[:, 0], y=def_pts[:, 1], z=def_pts[:, 2],
            mode='markers', marker=dict(color='red', size=6), name='Deformed'
        ))
        
        # Draw the dashed movement lines
        line_x, line_y, line_z = [], [], []
        for i in range(len(orig_pts)):
            line_x.extend([orig_pts[i, 0], def_pts[i, 0], None])
            line_y.extend([orig_pts[i, 1], def_pts[i, 1], None])
            line_z.extend([orig_pts[i, 2], def_pts[i, 2], None])
            
        fig.add_trace(go.Scatter3d(
            x=line_x, y=line_y, z=line_z,
            mode='lines', line=dict(color='black', width=4, dash='dash'), name='Movement'
        ))
        
    fig.update_layout(
        scene=dict(aspectmode='data'), # Keeps the wing from looking squashed
        margin=dict(l=0, r=0, b=0, t=0) # Makes the plot fill the screen
    )
    
    fig.show()

def apply_wing_deformations(input_stl, output_stl=None, transforms=[], show_plot=False, radius=0.2, floor_clearance=0.01):
    """Core function to apply deformations. Can be imported by other scripts."""
    print(f"Loading {input_stl}...")
    stl_file = io.STLHandler.read(input_stl)
    points = np.array(stl_file['points'])

    wing = WingController()
    wing.setup_default_points()

    # Process requested transformations
    for t in transforms:
        action = t.get('action')
        
        if hasattr(wing, action):
            if action == "move_point":
                p_name = t.get('point_name')
                dx, dy, dz = t.get('dx', 0), t.get('dy', 0), t.get('dz', 0)
                wing.move_point(p_name, dx, dy, dz)
                
            elif action == "move_symmetric_pair":
                base_name = t.get('base_name')
                dx, dy, dz = t.get('dx', 0), t.get('dy', 0), t.get('dz', 0)
                wing.move_symmetric_pair(base_name, dx, dy, dz)
                
            else:
                amount = t.get('amount')
                getattr(wing, action)(amount)
        else:
            print(f"Warning: Function '{action}' not found in WingController.")

    # Execute RBF
    orig_pts, def_pts = wing.get_arrays()
    rbf = RBF(original_control_points=orig_pts, deformed_control_points=def_pts, func='gaussian_spline', radius=radius)
    
    print("Calculating mesh deformation...")
    stl_file['points'] = rbf(points)

    # Find the absolute lowest Z coordinate in the whole mesh
    min_z = np.min(stl_file['points'][:, 2])
    
    # 2. If it is below our safe clearance, lift the entire wing
    if min_z < floor_clearance:
        lift_amount = floor_clearance - min_z
        print(f"⚠️ Wing dropped too low (min Z: {min_z:.4f}). Lifting entire mesh by {lift_amount:.4f} in Z.")
        
        # Shift all Z-coordinates upward by the exact deficit
        stl_file['points'][:, 2] += lift_amount

    if output_stl:
        io.STLHandler.write(output_stl, stl_file)
        print(f"Saved deformed wing to: {output_stl}")

    if show_plot:
        plot_wing(stl_file, rbf=rbf)

    return stl_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply RBF deformations to an F1 Wing STL.")
    parser.add_argument("-i", "--input", required=True, help="Path to original STL file")
    parser.add_argument("-o", "--output", help="Path to save the deformed STL")
    parser.add_argument("-t", "--transforms", required=True, help="Path to JSON file with transformations")
    parser.add_argument("-p", "--plot", action="store_true", help="Toggle to show the 3D plot")
    args = parser.parse_args()

    # Load JSON file
    with open(args.transforms, 'r') as f:
        config = json.load(f)

    apply_wing_deformations(args.input, args.output, config, args.plot)