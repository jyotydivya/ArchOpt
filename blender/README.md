# HoloEarth 🌍 — ArchOpt 3D Procedural Campus Generation (Person 6)

## Overview

The `blender/` module converts Contract 9 Blueprint JSON into a complete, procedural 3D campus using Blender and Python (`bpy`).

The system uses procedural geometry without requiring external 3D model assets or direct database access:
> **AI decides WHERE things go. Blender decides HOW they are visualized.**

---

## 🎨 P6 — Blender Automation Features

- 🏢 **Procedural Buildings**: Generates architectural buildings with floor divisions, wall textures, window arrays, roof details, and zone-based materials.
- 🛣️ **Roads & Pathways**: Generates primary and secondary circulation networks connecting campus entrances to building access points.
- 🚗 **Parking Areas**: Creates marked parking lots with asphalt textures, stall lines, and vehicle spacing.
- 🌳 **Green Areas & Trees**: Procedurally creates vegetation plots, grass materials, and 3D tree canopies.
- 🚪 **Campus Entrances**: Places security gates, access portals, and boundary markers at campus entrance coordinates.
- 💡 **Street Lights & Site Furniture**: Adds illumination poles and exterior lighting fixtures along roadways.
- 📷 **Architectural Cameras**: Configures perspective overview and aerial cameras framing the entire campus site.
- ☀️ **Lighting & Environment**: Sun lamp, sky illumination, and ambient color management (`AgX` transform where available).
- 🎥 **Automated Headless Rendering**: CLI-driven batch rendering producing `.png` images and `.blend` project files.

---

## 📄 Contract 9 Blueprint Specification

The procedural generation is driven strictly by Contract 9 Blueprint JSON (`GET /api/layouts/{layoutId}/blueprint`):

```text
Blueprint JSON (Contract 9)
      ↓
blender/generator.py
      ↓
Procedural 3D Campus
      ↓
campus.blend + campus_render.png
```

Each building in the blueprint contains:
- `id`: integer building ID
- `name`: string display name (e.g., "Academic Block A")
- `type`: building type (e.g., "academic", "library", "hostel")
- `zone`: campus zone (e.g., "academic", "residential")
- `x`, `y`: bottom-left placement coordinates (meters)
- `width`, `depth`, `height`: spatial dimensions (meters)
- `rotation`: orientation angle in degrees
- `floorCount`: number of building storeys

Site boundary is defined in `site: {"width": float, "height": float}` with entrance coordinates in `entrances: [{"x": float, "y": float, "width": float}]`.

---

## 📂 Directory Structure

```
blender/
├── generator.py            # Primary procedural campus generator script
├── README.md               # Person 6 documentation and usage guide
├── input/
│   └── sample_blueprint.json # Validated Contract 9 sample blueprint
└── output/
    └── .gitkeep            # Output directory for campus.blend and campus_render.png
```

---

## 🛠️ Execution & CLI Options

Execute headless procedural generation using Blender's Python interface:

```bash
# Basic run with default sample blueprint:
blender -b -P blender/generator.py

# Specify custom blueprint and output targets:
blender -b -P blender/generator.py -- --input blender/input/sample_blueprint.json --output-blend blender/output/campus.blend --output-render blender/output/campus_render.png

# Select render engine (EEVEE or CYCLES):
blender -b -P blender/generator.py -- --engine EEVEE
```

### CLI Arguments:
| Argument | Default | Description |
|---|---|---|
| `--input <path>` | `blender/input/sample_blueprint.json` | Path to Contract 9 Blueprint JSON |
| `--output-blend <path>` | `blender/output/campus.blend` | Target `.blend` project save location |
| `--output-render <path>` | `blender/output/campus_render.png` | Target rendered image output path |
| `--engine <EEVEE\|CYCLES>` | `EEVEE` | Blender rendering engine |

---

## 🔌 Architecture & Production Integration Flow

```
FastAPI Backend (P4)
       ↓  GET /api/layouts/{layoutId}/blueprint
Contract 9 Blueprint JSON
       ↓
blender/generator.py
       ↓
3D Campus (.blend + .png)
```
