import json
import argparse
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from pygem import RBF
from smithers import io

class WingController:
    def __init__(self):
        self.points = {}
        self.deltas = {}
    
    def setup_default_points(self):
        """Loads your specific front wing anchor and control points."""
        self.add_point('left_endplate', -1356, 418, 118)
        self.add_point('right_endplate', 1356, 418, 118)
        self.add_point('left_back_body', -132, 1836, 585)
        self.add_point('right_back_body', 132, 1836, 585)
        self.add_point('left_mid_body', -103, 1000, 386)
        self.add_point('right_mid_body', 103, 1000, 386)
        self.add_point('left_front_body', -144, 111, 5)
        self.add_point('right_front_body', 144, 111, 5)
        self.add_point('center_front', 0, -175, -65)
        self.add_point('left_wing_top', -788, 418, 86)
        self.add_point('right_wing_top', 788, 418, 86)  # Minus sign corrected!
        self.add_point('left_wing_mid', -796, 237, -8)
        self.add_point('right_wing_mid', 796, 237, -8)
        self.add_point('left_wing_bot', -813, -6, -67)
        self.add_point('right_wing_bot', 813, -6, -67)
        self.add_point('anchor_rear', 0, 2000, 500)

    def add_point(self, name, x, y, z):
        self.points[name] = np.array([x, y, z], dtype=float)
        self.deltas[name] = np.array([0, 0, 0], dtype=float)
        
    def reset_deformations(self):
        for name in self.deltas:
            self.deltas[name] = np.array([0, 0, 0], dtype=float)

    # --- CUSTOM TRANSFORMATIONS ---
    def change_span(self, amount):
        self.deltas['left_endplate'][0] -= amount
        self.deltas['right_endplate'][0] += amount
        for level in ['top', 'mid', 'bot']:
            self.deltas[f'left_wing_{level}'][0] -= amount
            self.deltas[f'right_wing_{level}'][0] += amount

    def flare_endplates(self, amount):
        self.deltas['left_endplate'][0] -= amount
        self.deltas['right_endplate'][0] += amount

    def adjust_nose_height(self, amount):
        self.deltas['center_front'][2] += amount
        self.deltas['left_front_body'][2] += amount
        self.deltas['right_front_body'][2] += amount

    def adjust_upper_flaps(self, amount):
        self.deltas['left_wing_top'][2] += amount
        self.deltas['right_wing_top'][2] += amount
        self.deltas['left_wing_top'][1] += (amount * 0.5) 
        self.deltas['right_wing_top'][1] += (amount * 0.5)

    def get_arrays(self):
        orig_list = []
        def_list = []
        for name in self.points:
            orig_pos = self.points[name]
            movement = self.deltas[name]
            orig_list.append(orig_pos)
            def_list.append(orig_pos + movement)
        return np.array(orig_list), np.array(def_list)

def plot_wing(data, rbf=None, color=None):
    """Visualizes the wing and RBF vectors."""
    if color is None: color = (0, 0, 1, 0.1)
    
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    points = np.array(data['points'])
    verts = [points[cell] for cell in data['cells']]
    
    faces = Poly3DCollection(verts, linewidths=0.1, edgecolors=(0, 0, 0, 0.2))
    faces.set_facecolor(color)
    ax.add_collection3d(faces)

    if rbf is not None:
        orig_pts = rbf.original_control_points
        def_pts = rbf.deformed_control_points
        ax.scatter3D(orig_pts[:, 0], orig_pts[:, 1], orig_pts[:, 2], color='green', s=60, label='Original')
        ax.scatter3D(def_pts[:, 0], def_pts[:, 1], def_pts[:, 2], color='red', s=60, label='Deformed')

        for i in range(len(orig_pts)):
            ax.plot([orig_pts[i, 0], def_pts[i, 0]], [orig_pts[i, 1], def_pts[i, 1]], [orig_pts[i, 2], def_pts[i, 2]],
                    color='black', linestyle='--', linewidth=2)
        ax.legend()

    min_pts, max_pts = points.min(axis=0), points.max(axis=0)
    mid_pts = (max_pts + min_pts) / 2
    max_range = (max_pts - min_pts).max() / 2.0
    ax.set_xlim3d(mid_pts[0] - max_range, mid_pts[0] + max_range)
    ax.set_ylim3d(mid_pts[1] - max_range, mid_pts[1] + max_range)
    ax.set_zlim3d(mid_pts[2] - max_range, mid_pts[2] + max_range)
    ax.set_aspect('equal')
    plt.show()

def apply_wing_deformations(input_stl, output_stl=None, transforms=[], show_plot=False, radius=800.0):
    """Core function to apply deformations. Can be imported by other scripts."""
    print(f"Loading {input_stl}...")
    stl_file = io.STLHandler.read(input_stl)
    points = np.array(stl_file['points'])

    wing = WingController()
    wing.setup_default_points()

    # Process requested transformations
    for t in transforms:
        action = t.get('action')
        amount = t.get('amount')
        if hasattr(wing, action):
            print(f"Applying: {action} ({amount})")
            getattr(wing, action)(amount)
        else:
            print(f"Warning: Function '{action}' not found in WingController.")

    # Execute RBF
    orig_pts, def_pts = wing.get_arrays()
    rbf = RBF(original_control_points=orig_pts, deformed_control_points=def_pts, func='gaussian_spline', radius=radius)
    
    print("Calculating mesh deformation...")
    stl_file['points'] = rbf(points)

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