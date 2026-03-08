"""
SVG Inset Tool
- Load SVG files
- Set inset distance (micrometres)
- Preview and export
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import svgpathtools
import pyclipper
import re
import os
from xml.etree import ElementTree as ET

class SVGInsetTool:
    def __init__(self, root):
        self.root = root
        self.root.title("SVG Inset Tool")
        self.root.geometry("900x750")
        self.root.minsize(800, 650)
        self.root.configure(bg="#2b2b2b")
        
        # State
        self.svg_path = None
        self.original_paths = []  # List of (path_d, transform) tuples
        self.inset_paths = []
        self.original_points = []
        self.SCALE = 1000000
        
        self.setup_ui()
    
    def setup_ui(self):
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background="#2b2b2b")
        style.configure("TLabel", background="#2b2b2b", foreground="#ffffff", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("TEntry", font=("Segoe UI", 10))
        style.configure("TScale", background="#2b2b2b")
        
        # Main container
        main = ttk.Frame(self.root, padding=20)
        main.pack(fill=tk.BOTH, expand=True)
        
        # Header
        ttk.Label(main, text="SVG Inset Tool", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(main, text="Create mathematically precise parallel insets", foreground="#888888").pack(anchor=tk.W, pady=(0, 20))
        
        # File section
        file_frame = ttk.Frame(main)
        file_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(file_frame, text="SVG File:").pack(side=tk.LEFT)
        
        self.file_var = tk.StringVar(value="No file selected")
        self.file_label = ttk.Label(file_frame, textvariable=self.file_var, foreground="#888888", width=50)
        self.file_label.pack(side=tk.LEFT, padx=(10, 10))
        
        ttk.Button(file_frame, text="Browse...", command=self.browse_file).pack(side=tk.LEFT)
        
        # Inset settings
        settings_frame = ttk.Frame(main)
        settings_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(settings_frame, text="Inset Distance:").pack(side=tk.LEFT)
        
        self.inset_var = tk.StringVar(value="100")
        inset_entry = ttk.Entry(settings_frame, textvariable=self.inset_var, width=10)
        inset_entry.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Label(settings_frame, text="µm (micrometres)").pack(side=tk.LEFT)
        
        # Quick presets
        preset_frame = ttk.Frame(main)
        preset_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(preset_frame, text="Presets:").pack(side=tk.LEFT)
        for val in [50, 100, 200, 500, 1000]:
            ttk.Button(preset_frame, text=f"{val}µm", width=8,
                      command=lambda v=val: self.inset_var.set(str(v))).pack(side=tk.LEFT, padx=2)
        
        # Resolution setting
        res_frame = ttk.Frame(main)
        res_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(res_frame, text="Resolution:").pack(side=tk.LEFT)
        
        self.resolution_var = tk.StringVar(value="5000")
        res_entry = ttk.Entry(res_frame, textvariable=self.resolution_var, width=10)
        res_entry.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Label(res_frame, text="sample points (higher = smoother, slower)").pack(side=tk.LEFT)
        
        # Preview canvas
        preview_frame = ttk.Frame(main)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.canvas = tk.Canvas(preview_frame, bg="#1e1e1e", highlightthickness=1, highlightbackground="#444444")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Action buttons - BEFORE canvas so they're always visible
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.preview_btn = ttk.Button(btn_frame, text="Generate Preview", command=self.generate_preview)
        self.preview_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.export_btn = ttk.Button(btn_frame, text="Export SVG", command=self.export_svg)
        self.export_btn.pack(side=tk.LEFT, padx=(0, 20))
        
        # Status
        self.status_var = tk.StringVar(value="Load an SVG file to begin")
        ttk.Label(btn_frame, textvariable=self.status_var, foreground="#888888").pack(side=tk.LEFT)
        
        # Info panel
        self.info_var = tk.StringVar(value="")
        info_label = ttk.Label(main, textvariable=self.info_var, foreground="#66bb6a")
        info_label.pack(anchor=tk.W, pady=(0, 10))
    
    def browse_file(self):
        path = filedialog.askopenfilename(
            title="Select SVG File",
            filetypes=[("SVG Files", "*.svg"), ("All Files", "*.*")]
        )
        if path:
            self.svg_path = path
            self.file_var.set(os.path.basename(path))
            self.status_var.set(f"Loaded: {path}")
            self.load_svg()
    
    def load_svg(self):
        """Parse SVG and extract path data"""
        try:
            tree = ET.parse(self.svg_path)
            root = tree.getroot()
            
            # Handle namespace
            ns = {'svg': 'http://www.w3.org/2000/svg'}
            
            # Find all path elements
            paths = root.findall('.//{http://www.w3.org/2000/svg}path')
            if not paths:
                paths = root.findall('.//path')
            
            self.original_paths = []
            for path_elem in paths:
                d = path_elem.get('d')
                transform = path_elem.get('transform', '')
                
                # Check parent groups for transforms
                parent = path_elem
                while parent is not None:
                    parent = self.get_parent(root, parent)
                    if parent is not None:
                        parent_transform = parent.get('transform', '')
                        if parent_transform:
                            transform = parent_transform + ' ' + transform
                
                if d:
                    self.original_paths.append((d, transform.strip()))
            
            self.status_var.set(f"Found {len(self.original_paths)} path(s)")
            self.draw_preview()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load SVG: {e}")
    
    def get_parent(self, root, child):
        """Find parent element"""
        for parent in root.iter():
            if child in list(parent):
                return parent
        return None
    
    def parse_transform(self, transform_str):
        """Parse SVG transform string into components"""
        if not transform_str:
            return {'scale_x': 1, 'scale_y': 1, 'translate_x': 0, 'translate_y': 0}
        
        # Look for matrix transform
        matrix_match = re.search(r'matrix\s*\(\s*([^)]+)\s*\)', transform_str)
        if matrix_match:
            vals = [float(x) for x in re.split(r'[\s,]+', matrix_match.group(1).strip())]
            if len(vals) >= 6:
                return {
                    'scale_x': vals[0],
                    'scale_y': vals[3],
                    'translate_x': vals[4],
                    'translate_y': vals[5]
                }
        
        return {'scale_x': 1, 'scale_y': 1, 'translate_x': 0, 'translate_y': 0}
    
    def path_to_points(self, path_d, transform, num_samples):
        """Convert SVG path to list of points"""
        try:
            path = svgpathtools.parse_path(path_d)
            t = self.parse_transform(transform)
            
            points = []
            for i in range(num_samples):
                param = i / num_samples
                point = path.point(param)
                x = point.real * t['scale_x'] + t['translate_x']
                y = point.imag * t['scale_y'] + t['translate_y']
                points.append((x, y))
            
            return points
        except Exception as e:
            print(f"Error parsing path: {e}")
            return []
    
    def compute_inset(self, points, inset_mm):
        """Compute inset polygon using Clipper"""
        if len(points) < 3:
            return []
        
        scaled_points = [(int(x * self.SCALE), int(y * self.SCALE)) for x, y in points]
        inset_scaled = int(inset_mm * self.SCALE)
        
        pco = pyclipper.PyclipperOffset()
        pco.AddPath(scaled_points, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
        
        # Negative offset for inset
        inset_paths = pco.Execute(-inset_scaled)
        
        # Convert back
        result = []
        for path in inset_paths:
            result.append([(x / self.SCALE, y / self.SCALE) for x, y in path])
        
        return result
    
    def draw_preview(self):
        """Draw preview on canvas"""
        self.canvas.delete("all")
        
        if not self.original_paths:
            return
        
        # Get canvas size
        self.canvas.update()
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        
        # Sample at lower resolution for preview
        all_points = []
        for path_d, transform in self.original_paths:
            points = self.path_to_points(path_d, transform, 500)
            if points:
                all_points.extend(points)
                self.original_points.append(points)
        
        if not all_points:
            return
        
        # Calculate bounds
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        # Calculate scale to fit canvas with margin
        margin = 40
        scale_x = (cw - 2 * margin) / (max_x - min_x) if max_x != min_x else 1
        scale_y = (ch - 2 * margin) / (max_y - min_y) if max_y != min_y else 1
        scale = min(scale_x, scale_y)
        
        # Transform function
        def tx(x, y):
            return (
                margin + (x - min_x) * scale,
                margin + (y - min_y) * scale
            )
        
        # Draw original paths
        for path_d, transform in self.original_paths:
            points = self.path_to_points(path_d, transform, 500)
            if len(points) > 2:
                coords = []
                for x, y in points:
                    px, py = tx(x, y)
                    coords.extend([px, py])
                self.canvas.create_polygon(coords, fill="#f2edc2", outline="#666666", width=1)
    
    def generate_preview(self):
        """Generate and display inset preview"""
        if not self.original_paths:
            messagebox.showwarning("Warning", "Load an SVG file first")
            return
        
        try:
            inset_um = float(self.inset_var.get())
            inset_mm = inset_um / 1000.0
            num_samples = int(self.resolution_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid inset or resolution value")
            return
        
        self.status_var.set("Generating inset...")
        self.root.update()
        
        self.canvas.delete("all")
        
        # Get canvas size
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        
        all_original = []
        all_inset = []
        self.inset_paths = []
        self.original_points = []
        
        for path_d, transform in self.original_paths:
            points = self.path_to_points(path_d, transform, num_samples)
            if points:
                self.original_points.append(points)
                all_original.extend(points)
                
                inset_polys = self.compute_inset(points, inset_mm)
                self.inset_paths.append(inset_polys)
                for poly in inset_polys:
                    all_inset.extend(poly)
        
        if not all_original:
            return
        
        # Calculate bounds from original
        xs = [p[0] for p in all_original]
        ys = [p[1] for p in all_original]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        margin = 40
        scale_x = (cw - 2 * margin) / (max_x - min_x) if max_x != min_x else 1
        scale_y = (ch - 2 * margin) / (max_y - min_y) if max_y != min_y else 1
        scale = min(scale_x, scale_y)
        
        def tx(x, y):
            return (
                margin + (x - min_x) * scale,
                margin + (y - min_y) * scale
            )
        
        # Draw original (cream)
        for points in self.original_points:
            if len(points) > 2:
                coords = []
                for x, y in points:
                    px, py = tx(x, y)
                    coords.extend([px, py])
                self.canvas.create_polygon(coords, fill="#f2edc2", outline="", width=0)
        
        # Draw inset (black)
        for polys in self.inset_paths:
            for poly in polys:
                if len(poly) > 2:
                    coords = []
                    for x, y in poly:
                        px, py = tx(x, y)
                        coords.extend([px, py])
                    self.canvas.create_polygon(coords, fill="#000000", outline="", width=0)
        
        # Calculate areas
        total_orig_area = 0
        total_inset_area = 0
        
        for points in self.original_points:
            scaled = [(int(x * self.SCALE), int(y * self.SCALE)) for x, y in points]
            total_orig_area += abs(pyclipper.Area(scaled)) / (self.SCALE * self.SCALE)
        
        for polys in self.inset_paths:
            for poly in polys:
                scaled = [(int(x * self.SCALE), int(y * self.SCALE)) for x, y in poly]
                total_inset_area += abs(pyclipper.Area(scaled)) / (self.SCALE * self.SCALE)
        
        self.status_var.set(f"Preview generated with {num_samples} samples")
        self.info_var.set(f"Original: {total_orig_area:.2f} mm²  |  Inset: {total_inset_area:.2f} mm²  |  Reduction: {total_orig_area - total_inset_area:.2f} mm²")
    
    def export_svg(self):
        """Export the inset SVG"""
        if not self.inset_paths:
            messagebox.showwarning("Warning", "Generate preview first")
            return
        
        # Get save path
        inset_um = self.inset_var.get()
        default_name = os.path.splitext(os.path.basename(self.svg_path))[0] + f"_inset_{inset_um}um.svg"
        
        save_path = filedialog.asksaveasfilename(
            title="Export SVG",
            defaultextension=".svg",
            initialfile=default_name,
            filetypes=[("SVG Files", "*.svg")]
        )
        
        if not save_path:
            return
        
        # Generate SVG
        def points_to_d(points):
            if not points:
                return ""
            d = f"M {points[0][0]},{points[0][1]}"
            for x, y in points[1:]:
                d += f" L {x},{y}"
            d += " Z"
            return d
        
        svg = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   width="210mm"
   height="297mm"
   viewBox="0 0 210 297"
   version="1.1"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">
  
  <g inkscape:groupmode="layer" inkscape:label="Original" id="layer-original">
'''
        
        for points in self.original_points:
            d = points_to_d(points)
            svg += f'    <path fill="#f2edc2" stroke="none" d="{d}"/>\n'
        
        svg += '''  </g>
  
  <g inkscape:groupmode="layer" inkscape:label="Inset_''' + inset_um + '''um" id="layer-inset">
'''
        
        for polys in self.inset_paths:
            for poly in polys:
                d = points_to_d(poly)
                svg += f'    <path fill="#000000" stroke="none" d="{d}"/>\n'
        
        svg += '''  </g>
</svg>
'''
        
        with open(save_path, 'w') as f:
            f.write(svg)
        
        self.status_var.set(f"Exported: {save_path}")
        messagebox.showinfo("Success", f"Exported to:\n{save_path}")


def main():
    root = tk.Tk()
    app = SVGInsetTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
