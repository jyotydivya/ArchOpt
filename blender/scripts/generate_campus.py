import bpy
import json
import os
import math


# --------------------------------------------------
# 1. Find the Blueprint JSON
# --------------------------------------------------

# Find the actual saved Blender Python file
text_block = bpy.data.texts.get("generate_campus.py")

if text_block is None:
    raise RuntimeError("generate_campus.py text block not found")

if not text_block.filepath:
    raise RuntimeError(
        "Please save generate_campus.py before running it."
    )

SCRIPT_DIR = os.path.dirname(
    os.path.abspath(text_block.filepath)
)

PROJECT_DIR = os.path.abspath(
    os.path.join(SCRIPT_DIR, "..", "..")
)

BLUEPRINT_PATH = os.path.join(
    PROJECT_DIR,
    "blender",
    "input",
    "sample_blueprint.json"
)

# --------------------------------------------------
# 2. Load Blueprint
# --------------------------------------------------

print("====================================")
print("HoloEarth P6 Blender Generator")
print("====================================")

print(f"Loading blueprint: {BLUEPRINT_PATH}")

with open(BLUEPRINT_PATH, "r", encoding="utf-8") as file:
    blueprint = json.load(file)

print("Blueprint loaded successfully!")


# --------------------------------------------------
# 3. Clear default Blender scene
# --------------------------------------------------

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

print("Default scene cleared.")


# --------------------------------------------------
# 4. Create campus ground
# --------------------------------------------------

site_width = blueprint["site"]["width"]
site_height = blueprint["site"]["height"]

bpy.ops.mesh.primitive_cube_add(
    location=(site_width / 2, site_height / 2, -0.5)
)

ground = bpy.context.object
ground.name = "Campus_Ground"

ground.dimensions = (
    site_width,
    site_height,
    1
)

bpy.ops.object.transform_apply(
    location=False,
    rotation=False,
    scale=True
)

print(f"Campus size: {site_width}m x {site_height}m")


# --------------------------------------------------
# 5. Create buildings from Blueprint
# --------------------------------------------------

for building in blueprint["buildings"]:

    x = building["x"]
    y = building["y"]

    width = building["width"]
    depth = building["depth"]
    height = building["height"]

    rotation = building["rotation"]

    name = building["name"]
    building_type = building["type"]

    # Create building
    bpy.ops.mesh.primitive_cube_add(
        location=(
            x + width / 2,
            y + depth / 2,
            height / 2
        )
    )

    obj = bpy.context.object

    obj.name = name

    # Set dimensions
    obj.dimensions = (
        width,
        depth,
        height
    )

    # Apply rotation
    obj.rotation_euler[2] = math.radians(rotation)

    # Apply dimensions
    bpy.ops.object.transform_apply(
        location=False,
        rotation=False,
        scale=True
    )

    # Store useful metadata
    obj["building_id"] = building["buildingId"]
    obj["building_type"] = building_type

    print(
        f"Created: {name} | "
        f"Type: {building_type} | "
        f"Position: ({x}, {y})"
    )


# --------------------------------------------------
# 6. Finish
# --------------------------------------------------

print("====================================")
print("HoloEarth campus generation complete!")
print("====================================")