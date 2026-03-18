# SVG Insetter

A tool to create mathematically precise parallel insets of SVG shapes using polygon offsetting.

## Download

**[⬇ Download SVGInsetTool.exe](https://github.com/Blendermaestro/svginsetter/releases/download/v1.0/SVGInsetTool.exe)** — Windows, no Python required.

## Features

- Load any SVG file
- Set inset distance in micrometres (µm)
- High resolution sampling for tessellation-ready output
- Preview with original (cream) and inset (black) layers
- Export with named Inkscape-compatible layers
- Standalone Windows executable

## Usage

### GUI Application

Run `svg_inset_tool.py` or use the compiled `SVG_Inset_Tool.exe`:

1. Click **Browse** to load an SVG file
2. Set the **Inset Distance** in micrometres (presets: 50, 100, 200, 500, 1000 µm)
3. Adjust **Resolution** for smoother curves (default: 5000 samples)
4. Click **Generate Preview** to see the result
5. Click **Export SVG** to save

### Command Line

For batch processing, use `inset_svg.py` directly (edit the script to set input/output paths).

## Output

The exported SVG contains two layers:
- **Original** - The original shape (cream fill)
- **Inset_XXXum** - The mathematically computed inset (black fill)

## Requirements

- Python 3.8+
- svgpathtools
- pyclipper
- numpy

Install dependencies:
```bash
pip install svgpathtools pyclipper numpy
```

## Building the Executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "SVG_Inset_Tool" svg_inset_tool.py
```

The exe will be in the `dist/` folder.

## How It Works

1. Parse SVG path data and transforms
2. Sample the path at high resolution to create a polygon
3. Use Clipper library to compute the parallel offset (inset)
4. Export both original and inset as separate layers

## License

MIT
