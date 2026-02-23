from wing_deformer import apply_wing_deformations

# Define your tweaks right in the code
my_tweaks = [
    {"action": "flare_endplates_outward", "amount": 0.08}
]

# Run it! Set show_plot=False to keep it running quietly in the background
final_stl = apply_wing_deformations(
    input_stl="FrontWing.stl", 
    output_stl="Variation_001.stl", 
    transforms=my_tweaks, 
    show_plot=True
)


"""
How to call it from terminal:

# With plotting enabled
python wing_deformer.py -i FrontWing.stl -o DeformedWing.stl -t tweaks.json -p

# Without plotting (runs silently, faster for automated generation)
python wing_deformer.py -i FrontWing.stl -o DeformedWing.stl -t tweaks.json
"""