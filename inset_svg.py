import svgpathtools
import pyclipper
import numpy as np
import re

# Read the original SVG
svg_file = r"c:\Users\User1\Downloads\svg\sds.svg"

# The path data from the SVG (extracted)
path_d = "m -0.47429,-4.74111 c -0.80408,0.7268 -2.4364,-0.23121 -2.5885,0.44112 -0.18378,0.81237 0.73534,1.63442 1.91673,2.52828 0.68592,0.51897 1.30962,-0.27432 1.8179,0.29739 C 1.32767,-0.73664 0.51119,0.69273 1.18217,0.84706 2.03005,1.04208 2.46354,-0.53661 3.70956,-0.77562 4.34245,-0.89702 4.3993,0.2376 4.93999,0.12624 5.5678,-0.00307 5.44274,-1.27079 6.04655,-1.25696 6.76624,-1.24048 7.41842,-0.6747 7.58698,0.18687 7.77409,1.14322 7.16749,1.28103 6.7579,2.37888 6.50053,3.06873 6.25307,3.76226 6.25307,3.76226 c 0,0 -0.40586,-1.2314 -1.25381,-1.64026 C 3.96908,1.62527 3.74783,1.95098 2.49681,1.95107 1.32723,1.95116 0.89133,1.59046 0.15807,2.12236 -0.35708,2.49605 -1e-5,3.76226 -1e-5,3.76226 c 0,0 0.35707,1.2662 -0.15808,1.6399 -0.73326,0.5319 -1.16916,0.1712 -2.33874,0.17129 -1.25101,9e-5 -1.47227,0.3258 -2.50245,-0.17093 -0.84795,-0.40886 -1.25381,-1.64026 -1.25381,-1.64026 0,0 0.72434,-0.13246 1.45045,-0.2545 1.15555,-0.19421 1.5782,0.26221 2.31287,-0.378 0.66186,-0.57677 0.82574,-1.42446 0.48017,-2.05597 -0.28993,-0.52983 -1.32528,0.21233 -1.75116,-0.26671 -0.36679,-0.41257 0.5874,-1.02911 0.16582,-1.51651 -0.83,-0.95958 -2.41393,-0.54564 -2.66898,-1.37744 -0.20184,-0.65825 1.44428,-0.66584 1.75521,-1.60265 0.24098,-0.72604 -0.75788,-0.86953 -0.6514,-1.72304 0.18341,-1.47005 0.43577,-2.67706 1.23119,-2.92408 0.65831,-0.20444 0.64481,1.68819 1.67627,2.02114 0.93299,0.30117 2.25263,-0.75289 2.25263,-0.75289 0,0 0.25302,1.66988 -0.47429,2.32728 z"

# Transform matrix: matrix(2.0660857,0,0,-2.0660857,24.539911,14.88054)
# This scales by 2.0660857 in x, -2.0660857 in y (flips), then translates
scale_x = 2.0660857
scale_y = -2.0660857
translate_x = 24.539911
translate_y = 14.88054

# Parse the path
path = svgpathtools.parse_path(path_d)

# Sample the path to get polygon points - HIGH RESOLUTION for tessellation
num_samples = 5000
points = []
for i in range(num_samples):
    t = i / num_samples
    point = path.point(t)
    # Apply the transform
    x = point.real * scale_x + translate_x
    y = point.imag * scale_y + translate_y
    points.append((x, y))

# Don't duplicate the first point - pyclipper handles closure

# Convert to pyclipper format (integers, scaled up for precision)
SCALE = 1000000  # pyclipper uses integers
scaled_points = [(int(x * SCALE), int(y * SCALE)) for x, y in points]

# Check orientation - pyclipper needs correct winding for inset direction
orientation = pyclipper.Orientation(scaled_points)
print(f"Polygon orientation: {'CCW' if orientation else 'CW'}")

# Inset amount: 0.1mm = 0.1 in SVG units (viewBox is in mm)
inset_mm = 0.1
inset_scaled = int(inset_mm * SCALE)

# Use pyclipper to compute the offset
# NEGATIVE offset = shrink toward center = true inset
pco = pyclipper.PyclipperOffset()
pco.AddPath(scaled_points, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
inset_paths = pco.Execute(-inset_scaled)  # Negative = inset/shrink

# Convert back to SVG coordinates
def path_to_svg_d(scaled_path):
    """Convert pyclipper path back to SVG path data"""
    if not scaled_path:
        return ""
    points = [(x / SCALE, y / SCALE) for x, y in scaled_path]
    d = f"M {points[0][0]},{points[0][1]}"
    for x, y in points[1:]:
        d += f" L {x},{y}"
    d += " Z"
    return d

# Generate original path in SVG coordinates
original_d = f"M {points[0][0]},{points[0][1]}"
for x, y in points[1:]:
    original_d += f" L {x},{y}"
original_d += " Z"

# Generate original path in SVG coordinates (high res)
original_d = f"M {points[0][0]},{points[0][1]}"
for x, y in points[1:]:
    original_d += f" L {x},{y}"
original_d += " Z"

# Generate inset paths
inset_d_list = [path_to_svg_d(p) for p in inset_paths]

# Create the output SVG - Named layers, original cream, inset black
svg_output = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   width="210mm"
   height="297mm"
   viewBox="0 0 210 297"
   version="1.1"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">
  
  <g inkscape:groupmode="layer" inkscape:label="Original" id="layer-original">
    <path fill="#f2edc2" stroke="none"
      d="{original_d}"/>
  </g>
  
  <g inkscape:groupmode="layer" inkscape:label="Inset_100um" id="layer-inset">
'''

for i, inset_d in enumerate(inset_d_list):
    svg_output += f'''    <path fill="#000000" stroke="none"
      d="{inset_d}"/>
'''

svg_output += '''  </g>
</svg>
'''

# Write output to NEW filename
output_file = r"c:\Users\User1\Downloads\svg\sds_inset_100um.svg"
with open(output_file, 'w') as f:
    f.write(svg_output)

print(f"Created {output_file}")
print(f"Original polygon: {len(points)} points (high res)")
print(f"Inset polygons: {len(inset_paths)}")
for i, p in enumerate(inset_paths):
    print(f"  Inset path {i}: {len(p)} points")

# Calculate area to verify inset went inward (should be smaller)
orig_area = abs(pyclipper.Area(scaled_points)) / (SCALE * SCALE)
for i, p in enumerate(inset_paths):
    inset_area = abs(pyclipper.Area(p)) / (SCALE * SCALE)
    print(f"Original area: {orig_area:.4f} mm^2")
    print(f"Inset area: {inset_area:.4f} mm^2")
    print(f"Area reduction: {orig_area - inset_area:.4f} mm^2 ({'CORRECT - inset is smaller' if inset_area < orig_area else 'ERROR - inset is larger!'})")
    print(f"  Inset path {i}: {len(p)} points")
