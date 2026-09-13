import bpy
import json
import math
import os
import sys
import random

from mathutils import Vector


# ============================================================
# HOLOEARTH / ARCHOPT
# PERSON 6 - ULTIMATE PROCEDURAL CAMPUS GENERATOR
#
# Contract 9 Blueprint JSON
#             ↓
#      Procedural Blender
#             ↓
#       campus.blend
#       campus_render.png
#
# Blender 5.2 compatible
# No database access
# No external assets
# Deterministic generation
#
# Default renderer: EEVEE
# Optional: --engine CYCLES
# ============================================================


# ============================================================
# 1. COMMAND LINE ARGUMENTS
# ============================================================

def parse_arguments():

    args = sys.argv

    if "--" in args:
        args = args[args.index("--") + 1:]
    else:
        args = []

    input_path = None
    output_blend = None
    output_render = None
    engine = "EEVEE"

    i = 0

    while i < len(args):

        if args[i] == "--input" and i + 1 < len(args):
            input_path = args[i + 1]
            i += 2
            continue

        if args[i] == "--output-blend" and i + 1 < len(args):
            output_blend = args[i + 1]
            i += 2
            continue

        if args[i] == "--output-render" and i + 1 < len(args):
            output_render = args[i + 1]
            i += 2
            continue

        if args[i] == "--engine" and i + 1 < len(args):
            engine = args[i + 1].upper()
            i += 2
            continue

        i += 1

    return (
        input_path,
        output_blend,
        output_render,
        engine
    )


CLI_INPUT, CLI_BLEND, CLI_RENDER, CLI_ENGINE = (
    parse_arguments()
)


# ============================================================
# 2. FIND SCRIPT DIRECTORY
# ============================================================

def find_script_directory():
    """
    Resolve the actual blender/ directory reliably when running:
    1. Blender Text Editor
    2. Blender Python console
    3. blender -P generator.py
    """

    # 1. If generator.py itself has a real filesystem path
    try:
        file_path = os.path.abspath(__file__)

        if (
            os.path.isfile(file_path)
            and os.path.basename(file_path).lower() == "generator.py"
        ):
            return os.path.dirname(file_path)
    except Exception:
        pass

    # 2. Look through Blender Text Editor blocks
    try:
        for text in bpy.data.texts:
            if text.filepath:
                path = os.path.abspath(bpy.path.abspath(text.filepath))

                if (
                    os.path.isfile(path)
                    and os.path.basename(path).lower() == "generator.py"
                ):
                    return os.path.dirname(path)
    except Exception:
        pass

    # 3. If the current .blend is:
    #    blender/output/campus.blend
    #    then the Blender directory is one level above output.
    try:
        blend_path = bpy.data.filepath

        if blend_path:
            blend_path = os.path.abspath(blend_path)

            output_dir = os.path.dirname(blend_path)

            if os.path.basename(output_dir).lower() == "output":
                blender_dir = os.path.dirname(output_dir)

                if os.path.isdir(blender_dir):
                    return blender_dir
    except Exception:
        pass

    # 4. Final fallback: current working directory
    return os.getcwd()


SCRIPT_DIR = find_script_directory()

INPUT_DIR = os.path.join(
    SCRIPT_DIR,
    "input"
)

OUTPUT_DIR = os.path.join(
    SCRIPT_DIR,
    "output"
)

os.makedirs(
    INPUT_DIR,
    exist_ok=True
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


BLUEPRINT_PATH = (
    os.path.abspath(CLI_INPUT)
    if CLI_INPUT
    else os.path.join(
        INPUT_DIR,
        "sample_blueprint.json"
    )
)


BLEND_OUTPUT_PATH = (
    os.path.abspath(CLI_BLEND)
    if CLI_BLEND
    else os.path.join(
        OUTPUT_DIR,
        "campus.blend"
    )
)


RENDER_OUTPUT_PATH = (
    os.path.abspath(CLI_RENDER)
    if CLI_RENDER
    else os.path.join(
        OUTPUT_DIR,
        "campus_render.png"
    )
)


os.makedirs(
    os.path.dirname(BLEND_OUTPUT_PATH),
    exist_ok=True
)

os.makedirs(
    os.path.dirname(RENDER_OUTPUT_PATH),
    exist_ok=True
)


# ============================================================
# 3. LOAD BLUEPRINT
# ============================================================

print("")
print("=" * 78)
print("HOLOEARTH - ULTIMATE 3D CAMPUS GENERATOR")
print("=" * 78)
print("")
print("Blueprint:")
print(BLUEPRINT_PATH)


if not os.path.exists(BLUEPRINT_PATH):

    raise FileNotFoundError(
        "Blueprint JSON not found:\n"
        + BLUEPRINT_PATH
    )


with open(
    BLUEPRINT_PATH,
    "r",
    encoding="utf-8"
) as f:

    blueprint = json.load(f)


# ============================================================
# 4. CONTRACT 9 VALIDATION
# ============================================================

def validate_blueprint(data):

    required = [
        "projectId",
        "layoutId",
        "site",
        "buildings",
        "roads",
        "greenAreas",
        "parkingAreas",
        "entrances"
    ]

    for key in required:

        if key not in data:

            raise ValueError(
                f"Missing Contract 9 field: {key}"
            )


    if "width" not in data["site"]:

        raise ValueError(
            "Missing site.width"
        )


    if "height" not in data["site"]:

        raise ValueError(
            "Missing site.height"
        )


    if not isinstance(
        data["buildings"],
        list
    ):

        raise ValueError(
            "buildings must be a list"
        )


    building_fields = [
        "id",
        "name",
        "type",
        "zone",
        "x",
        "y",
        "width",
        "depth",
        "height",
        "rotation",
        "floorCount"
    ]


    for index, building in enumerate(
        data["buildings"]
    ):

        for field in building_fields:

            if field not in building:

                raise ValueError(
                    f"Building {index} "
                    f"missing field: {field}"
                )


validate_blueprint(
    blueprint
)


# ============================================================
# 5. BASIC SITE DATA
# ============================================================

site_width = max(
    10.0,
    float(
        blueprint["site"]["width"]
    )
)


site_height = max(
    10.0,
    float(
        blueprint["site"]["height"]
    )
)


project_id = int(
    blueprint["projectId"]
)


layout_id = int(
    blueprint["layoutId"]
)


# Deterministic random generation.
random.seed(
    layout_id
)


buildings = sorted(
    blueprint["buildings"],
    key=lambda b: int(
        b["id"]
    )
)


# ============================================================
# 6. COLLECTION SYSTEM
# ============================================================

# Only remove our generated collection.
# Do not wipe the user's entire Blender file.

old_root = bpy.data.collections.get(
    "Campus_Root"
)

if old_root:

    bpy.data.collections.remove(
        old_root,
        do_unlink=True
    )


CAMPUS_ROOT = bpy.data.collections.new(
    "Campus_Root"
)

bpy.context.scene.collection.children.link(
    CAMPUS_ROOT
)


def create_collection(name):

    collection = bpy.data.collections.new(
        name
    )

    CAMPUS_ROOT.children.link(
        collection
    )

    return collection


SITE_COLL = create_collection(
    "01_Site"
)

BUILDINGS_COLL = create_collection(
    "02_Buildings"
)

ROADS_COLL = create_collection(
    "03_Roads"
)

GREEN_COLL = create_collection(
    "04_GreenAreas"
)

PARKING_COLL = create_collection(
    "05_Parking"
)

ENTRANCES_COLL = create_collection(
    "06_Entrances"
)

LIGHTING_COLL = create_collection(
    "07_Lighting"
)

CAMERAS_COLL = create_collection(
    "08_Cameras"
)


# ============================================================
# 7. MATERIAL SYSTEM
# ============================================================

def create_pbr_material(
    name,
    color,
    roughness=0.5,
    metallic=0.0,
    bump_strength=0.0,
    noise_scale=25.0
):

    material = bpy.data.materials.get(
        name
    )

    if material is None:

        material = bpy.data.materials.new(
            name=name
        )

    material.use_nodes = True

    nodes = material.node_tree.nodes
    links = material.node_tree.links

    nodes.clear()


    output = nodes.new(
        "ShaderNodeOutputMaterial"
    )

    output.location = (
        500,
        0
    )


    bsdf = nodes.new(
        "ShaderNodeBsdfPrincipled"
    )

    bsdf.location = (
        150,
        0
    )


    links.new(
        bsdf.outputs["BSDF"],
        output.inputs["Surface"]
    )


    bsdf.inputs[
        "Base Color"
    ].default_value = color


    bsdf.inputs[
        "Roughness"
    ].default_value = roughness


    if "Metallic" in bsdf.inputs:

        bsdf.inputs[
            "Metallic"
        ].default_value = metallic


    if bump_strength > 0:

        texcoord = nodes.new(
            "ShaderNodeTexCoord"
        )

        texcoord.location = (
            -700,
            0
        )


        noise = nodes.new(
            "ShaderNodeTexNoise"
        )

        noise.location = (
            -500,
            0
        )

        noise.inputs[
            "Scale"
        ].default_value = noise_scale

        noise.inputs[
            "Detail"
        ].default_value = 5.0

        noise.inputs[
            "Roughness"
        ].default_value = 0.65


        bump = nodes.new(
            "ShaderNodeBump"
        )

        bump.location = (
            -150,
            -150
        )

        bump.inputs[
            "Strength"
        ].default_value = bump_strength

        bump.inputs[
            "Distance"
        ].default_value = 0.08


        links.new(
            texcoord.outputs["Object"],
            noise.inputs["Vector"]
        )

        links.new(
            noise.outputs["Fac"],
            bump.inputs["Height"]
        )

        links.new(
            bump.outputs["Normal"],
            bsdf.inputs["Normal"]
        )


    material.diffuse_color = color

    return material


def create_glass_material():

    material = bpy.data.materials.get(
        "MAT_Architectural_Glass"
    )

    if material is None:

        material = bpy.data.materials.new(
            name="MAT_Architectural_Glass"
        )


    material.use_nodes = True

    nodes = material.node_tree.nodes

    bsdf = nodes.get(
        "Principled BSDF"
    )


    if bsdf:

        bsdf.inputs[
            "Base Color"
        ].default_value = (
            0.20,
            0.45,
            0.65,
            1.0
        )

        bsdf.inputs[
            "Roughness"
        ].default_value = 0.08


        if "Metallic" in bsdf.inputs:

            bsdf.inputs[
                "Metallic"
            ].default_value = 0.15


        if "Transmission Weight" in bsdf.inputs:

            bsdf.inputs[
                "Transmission Weight"
            ].default_value = 0.55


        if "IOR" in bsdf.inputs:

            bsdf.inputs[
                "IOR"
            ].default_value = 1.45


    return material


# ------------------------------------------------------------
# Environment
# ------------------------------------------------------------

ASPHALT_MAT = create_pbr_material(
    "MAT_Asphalt",
    (0.035, 0.042, 0.052, 1),
    0.82,
    0.0,
    0.10,
    45
)


ROAD_MARK_MAT = create_pbr_material(
    "MAT_RoadMarking",
    (0.92, 0.92, 0.86, 1),
    0.60,
    0.0,
    0.02,
    50
)


CURB_MAT = create_pbr_material(
    "MAT_Concrete",
    (0.34, 0.36, 0.39, 1),
    0.78,
    0.0,
    0.06,
    30
)


WALKWAY_MAT = create_pbr_material(
    "MAT_Walkway",
    (0.45, 0.43, 0.40, 1),
    0.76,
    0.0,
    0.08,
    28
)


GRASS_MAT = create_pbr_material(
    "MAT_Grass",
    (0.025, 0.20, 0.035, 1),
    0.90,
    0.0,
    0.15,
    55
)


PARKING_MAT = create_pbr_material(
    "MAT_Parking",
    (0.055, 0.065, 0.080, 1),
    0.82,
    0.0,
    0.08,
    45
)


SOIL_MAT = create_pbr_material(
    "MAT_Soil",
    (0.18, 0.075, 0.035, 1),
    0.95,
    0.0,
    0.18,
    30
)


# ------------------------------------------------------------
# Architectural materials
# ------------------------------------------------------------

ACADEMIC_MAT = create_pbr_material(
    "MAT_Academic_Facade",
    (0.055, 0.20, 0.60, 1),
    0.38,
    0.08,
    0.025,
    18
)


RESIDENTIAL_MAT = create_pbr_material(
    "MAT_Residential_Facade",
    (0.72, 0.30, 0.15, 1),
    0.50,
    0.04,
    0.04,
    20
)


SPORTS_MAT = create_pbr_material(
    "MAT_Sports_Facade",
    (0.78, 0.06, 0.16, 1),
    0.32,
    0.15,
    0.025,
    18
)


ADMIN_MAT = create_pbr_material(
    "MAT_Admin_Facade",
    (0.78, 0.80, 0.84, 1),
    0.30,
    0.15,
    0.015,
    12
)


LIBRARY_MAT = create_pbr_material(
    "MAT_Library_Facade",
    (0.08, 0.38, 0.47, 1),
    0.32,
    0.10,
    0.025,
    18
)


DEFAULT_FACADE_MAT = create_pbr_material(
    "MAT_Default_Facade",
    (0.55, 0.58, 0.62, 1),
    0.48,
    0.05,
    0.035,
    18
)


DARK_METAL_MAT = create_pbr_material(
    "MAT_Dark_Aluminium",
    (0.035, 0.045, 0.055, 1),
    0.25,
    0.85,
    0.01,
    15
)


ROOF_MAT = create_pbr_material(
    "MAT_Roof",
    (0.065, 0.075, 0.090, 1),
    0.88,
    0.05,
    0.10,
    60
)


GLASS_MAT = create_glass_material()


SOLAR_MAT = create_pbr_material(
    "MAT_SolarPanels",
    (0.008, 0.018, 0.055, 1),
    0.15,
    0.70,
    0.01,
    20
)


HVAC_MAT = create_pbr_material(
    "MAT_HVAC",
    (0.55, 0.58, 0.60, 1),
    0.36,
    0.60,
    0.025,
    25
)


ACCENT_MAT = create_pbr_material(
    "MAT_EntranceAccent",
    (0.90, 0.55, 0.06, 1),
    0.28,
    0.30,
    0.01,
    15
)


WOOD_MAT = create_pbr_material(
    "MAT_Wood",
    (0.25, 0.10, 0.035, 1),
    0.75,
    0.0,
    0.12,
    35
)


# ------------------------------------------------------------
# Trees
# ------------------------------------------------------------

BARK_MAT = create_pbr_material(
    "MAT_Tree_Bark",
    (0.16, 0.075, 0.035, 1),
    0.95,
    0.0,
    0.25,
    35
)


LEAF_MAT = create_pbr_material(
    "MAT_Tree_Leaves",
    (0.025, 0.25, 0.035, 1),
    0.62,
    0.0,
    0.04,
    20
)


# ------------------------------------------------------------
# Cars
# ------------------------------------------------------------

CAR_MATS = [
    create_pbr_material(
        "MAT_Car_White",
        (0.88, 0.90, 0.93, 1),
        0.22,
        0.45
    ),
    create_pbr_material(
        "MAT_Car_Blue",
        (0.02, 0.08, 0.32, 1),
        0.22,
        0.45
    ),
    create_pbr_material(
        "MAT_Car_Red",
        (0.62, 0.025, 0.018, 1),
        0.22,
        0.45
    ),
    create_pbr_material(
        "MAT_Car_Grey",
        (0.18, 0.20, 0.22, 1),
        0.22,
        0.45
    )
]


CAR_GLASS_MAT = create_pbr_material(
    "MAT_Car_Glass",
    (0.015, 0.035, 0.050, 1),
    0.18,
    0.35
)


# ============================================================
# 8. GEOMETRY HELPERS
# ============================================================

def link_object(
    obj,
    collection
):

    for col in list(
        obj.users_collection
    ):

        col.objects.unlink(
            obj
        )

    collection.objects.link(
        obj
    )


def create_box(
    name,
    location,
    dimensions,
    material,
    collection,
    rotation=0.0,
    bevel=0.0
):

    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=location,
        rotation=(
            0.0,
            0.0,
            rotation
        )
    )

    obj = bpy.context.active_object

    obj.name = name

    obj.dimensions = dimensions

    bpy.ops.object.transform_apply(
        location=False,
        rotation=False,
        scale=True
    )


    if bevel > 0.005:

        modifier = obj.modifiers.new(
            name="Architectural_Bevel",
            type="BEVEL"
        )

        modifier.width = bevel

        modifier.segments = 2

        modifier.limit_method = "ANGLE"

        modifier.angle_limit = math.radians(
            35
        )


    if material:

        obj.data.materials.append(
            material
        )


    link_object(
        obj,
        collection
    )

    return obj


def create_cylinder(
    name,
    location,
    radius,
    depth,
    material,
    collection,
    vertices=16,
    rotation=None
):

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
        location=location
    )

    obj = bpy.context.active_object

    obj.name = name


    if rotation:

        obj.rotation_euler = rotation


    if material:

        obj.data.materials.append(
            material
        )


    link_object(
        obj,
        collection
    )

    return obj


def create_ico_sphere(
    name,
    location,
    radius,
    material,
    collection
):

    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=2,
        radius=radius,
        location=location
    )

    obj = bpy.context.active_object

    obj.name = name

    if material:

        obj.data.materials.append(
            material
        )

    link_object(
        obj,
        collection
    )

    return obj


# ============================================================
# 9. COORDINATE HELPERS
# ============================================================

def building_center(
    x,
    y,
    width,
    depth
):

    # Contract 9:
    # x/y represent the lower-left footprint position.

    return (
        x + width / 2.0,
        y + depth / 2.0
    )


def local_to_world(
    local_x,
    local_y,
    center_x,
    center_y,
    rotation
):

    c = math.cos(
        rotation
    )

    s = math.sin(
        rotation
    )

    return (
        center_x
        + local_x * c
        - local_y * s,

        center_y
        + local_x * s
        + local_y * c
    )


def clamp(
    value,
    low,
    high
):

    return max(
        low,
        min(
            high,
            value
        )
    )


# ============================================================
# 10. BUILDING MATERIAL SELECTION
# ============================================================

def get_building_material(
    building
):

    zone = str(
        building.get(
            "zone",
            ""
        )
    ).lower()

    btype = str(
        building.get(
            "type",
            ""
        )
    ).lower()


    if (
        "academic" in zone
        or "academic" in btype
    ):

        return ACADEMIC_MAT


    if (
        "residential" in zone
        or "hostel" in zone
        or "hostel" in btype
    ):

        return RESIDENTIAL_MAT


    if (
        "sport" in zone
        or "sport" in btype
        or "recreation" in zone
    ):

        return SPORTS_MAT


    if (
        "admin" in zone
        or "administration" in zone
        or "admin" in btype
        or "administration" in btype
    ):

        return ADMIN_MAT


    if (
        "library" in zone
        or "library" in btype
    ):

        return LIBRARY_MAT


    return DEFAULT_FACADE_MAT


# ============================================================
# 11. BUILDING GENERATOR
# ============================================================

def generate_building(
    building
):

    bid = int(
        building["id"]
    )

    name = str(
        building["name"]
    ).replace(
        " ",
        "_"
    )


    x = float(
        building["x"]
    )

    y = float(
        building["y"]
    )


    width = max(
        6.0,
        float(
            building["width"]
        )
    )

    depth = max(
        6.0,
        float(
            building["depth"]
        )
    )

    height = max(
        3.0,
        float(
            building["height"]
        )
    )


    rotation_deg = float(
        building.get(
            "rotation",
            0.0
        )
    )

    rotation = math.radians(
        rotation_deg
    )


    floors = max(
        1,
        int(
            building.get(
                "floorCount",
                round(
                    height / 3.5
                )
            )
        )
    )


    # Correct Contract 9 center.
    cx, cy = building_center(
        x,
        y,
        width,
        depth
    )


    floor_height = (
        height / floors
    )


    facade = get_building_material(
        building
    )


    # --------------------------------------------------------
    # Main Mass
    # --------------------------------------------------------

    body = create_box(
        f"Bldg_{bid}_{name}_Mass",
        (
            cx,
            cy,
            height / 2
        ),
        (
            width,
            depth,
            height
        ),
        facade,
        BUILDINGS_COLL,
        rotation,
        0.12
    )


    # Store Blueprint metadata.
    body["blueprint_id"] = bid
    body["blueprint_name"] = str(
        building["name"]
    )
    body["blueprint_type"] = str(
        building["type"]
    )
    body["blueprint_zone"] = str(
        building["zone"]
    )
    body["blueprint_x"] = x
    body["blueprint_y"] = y
    body["blueprint_width"] = width
    body["blueprint_depth"] = depth
    body["blueprint_height"] = height
    body["blueprint_rotation"] = rotation_deg
    body["blueprint_floor_count"] = floors


    # --------------------------------------------------------
    # Floor slabs
    # --------------------------------------------------------

    for floor in range(
        1,
        floors + 1
    ):

        z = (
            floor
            * floor_height
        )


        create_box(
            (
                f"Bldg_{bid}_"
                f"FloorSlab_{floor}"
            ),
            (
                cx,
                cy,
                z
            ),
            (
                width + 0.28,
                depth + 0.28,
                0.18
            ),
            DARK_METAL_MAT,
            BUILDINGS_COLL,
            rotation,
            0.035
        )


    # --------------------------------------------------------
    # Windows
    # --------------------------------------------------------

    window_width = clamp(
        width / 11.0,
        1.3,
        3.0
    )

    window_height = clamp(
        floor_height * 0.52,
        1.15,
        2.35
    )


    front_columns = max(
        2,
        int(
            width / 5.5
        )
    )


    side_columns = max(
        2,
        int(
            depth / 5.5
        )
    )


    for floor in range(
        floors
    ):

        z = (
            floor * floor_height
            + floor_height * 0.54
        )


        # Front and back.
        for col in range(
            front_columns
        ):

            lx = (
                -width / 2
                + width
                * (
                    col + 1
                )
                / (
                    front_columns + 1
                )
            )


            for side_name, ly in [
                (
                    "Front",
                    -depth / 2
                ),
                (
                    "Back",
                    depth / 2
                )
            ]:

                wx, wy = local_to_world(
                    lx,
                    ly,
                    cx,
                    cy,
                    rotation
                )


                # Glass.
                create_box(
                    (
                        f"Bldg_{bid}_"
                        f"{side_name}_"
                        f"Glass_{floor}_{col}"
                    ),
                    (
                        wx,
                        wy,
                        z
                    ),
                    (
                        window_width,
                        0.07,
                        window_height
                    ),
                    GLASS_MAT,
                    BUILDINGS_COLL,
                    rotation,
                    0.0
                )


                # Vertical mullion.
                create_box(
                    (
                        f"Bldg_{bid}_"
                        f"{side_name}_"
                        f"Mullion_{floor}_{col}"
                    ),
                    (
                        wx,
                        wy,
                        z
                    ),
                    (
                        0.08,
                        0.13,
                        window_height + 0.12
                    ),
                    DARK_METAL_MAT,
                    BUILDINGS_COLL,
                    rotation,
                    0.01
                )


        # Left and right sides.
        for col in range(
            side_columns
        ):

            ly = (
                -depth / 2
                + depth
                * (
                    col + 1
                )
                / (
                    side_columns + 1
                )
            )


            for side_name, lx in [
                (
                    "Left",
                    -width / 2
                ),
                (
                    "Right",
                    width / 2
                )
            ]:

                wx, wy = local_to_world(
                    lx,
                    ly,
                    cx,
                    cy,
                    rotation
                )


                create_box(
                    (
                        f"Bldg_{bid}_"
                        f"{side_name}_"
                        f"Glass_{floor}_{col}"
                    ),
                    (
                        wx,
                        wy,
                        z
                    ),
                    (
                        0.07,
                        window_width,
                        window_height
                    ),
                    GLASS_MAT,
                    BUILDINGS_COLL,
                    rotation,
                    0.0
                )


    # --------------------------------------------------------
    # Entrance canopy
    # --------------------------------------------------------

    entrance_width = clamp(
        width * 0.28,
        3.0,
        10.0
    )


    canopy_x, canopy_y = local_to_world(
        0,
        -(
            depth / 2
            + 1.9
        ),
        cx,
        cy,
        rotation
    )


    create_box(
        f"Bldg_{bid}_EntranceCanopy",
        (
            canopy_x,
            canopy_y,
            3.5
        ),
        (
            entrance_width,
            3.6,
            0.30
        ),
        DARK_METAL_MAT,
        BUILDINGS_COLL,
        rotation,
        0.05
    )


    # Glass doors.
    door_x, door_y = local_to_world(
        0,
        -(
            depth / 2
            + 0.08
        ),
        cx,
        cy,
        rotation
    )


    create_box(
        f"Bldg_{bid}_GlassEntrance",
        (
            door_x,
            door_y,
            1.5
        ),
        (
            min(
                5.5,
                entrance_width * 0.72
            ),
            0.10,
            2.8
        ),
        GLASS_MAT,
        BUILDINGS_COLL,
        rotation,
        0.0
    )


    # Entrance accent strip.
    accent_x, accent_y = local_to_world(
        0,
        -(
            depth / 2
            + 0.14
        ),
        cx,
        cy,
        rotation
    )


    create_box(
        f"Bldg_{bid}_EntranceAccent",
        (
            accent_x,
            accent_y,
            0.35
        ),
        (
            entrance_width + 0.8,
            0.18,
            0.35
        ),
        ACCENT_MAT,
        BUILDINGS_COLL,
        rotation,
        0.02
    )


    # --------------------------------------------------------
    # Hostel balconies
    # --------------------------------------------------------

    btype = str(
        building["type"]
    ).lower()

    zone = str(
        building["zone"]
    ).lower()


    if (
        "hostel" in btype
        or "residential" in zone
    ):

        for floor in range(
            1,
            floors
        ):

            z = (
                floor
                * floor_height
                - 0.35
            )


            bx, by = local_to_world(
                0,
                -(
                    depth / 2
                    + 0.55
                ),
                cx,
                cy,
                rotation
            )


            create_box(
                (
                    f"Bldg_{bid}_"
                    f"Balcony_{floor}"
                ),
                (
                    bx,
                    by,
                    z
                ),
                (
                    width * 0.58,
                    1.0,
                    0.14
                ),
                DARK_METAL_MAT,
                BUILDINGS_COLL,
                rotation,
                0.025
            )


            # Balcony railing.
            create_box(
                (
                    f"Bldg_{bid}_"
                    f"BalconyRail_{floor}"
                ),
                (
                    bx,
                    by - 0.40,
                    z + 0.50
                ),
                (
                    width * 0.58,
                    0.08,
                    1.0
                ),
                DARK_METAL_MAT,
                BUILDINGS_COLL,
                rotation,
                0.02
            )


    # --------------------------------------------------------
    # Roof
    # --------------------------------------------------------

    roof_z = (
        height + 0.25
    )


    create_box(
        f"Bldg_{bid}_Roof",
        (
            cx,
            cy,
            roof_z
        ),
        (
            width + 0.35,
            depth + 0.35,
            0.45
        ),
        ROOF_MAT,
        BUILDINGS_COLL,
        rotation,
        0.05
    )


    # --------------------------------------------------------
    # Parapet
    # --------------------------------------------------------

    parapet_height = 1.0
    parapet_thickness = 0.30


    parapets = [
        (
            "North",
            0,
            depth / 2,
            width + 0.35,
            parapet_thickness
        ),
        (
            "South",
            0,
            -depth / 2,
            width + 0.35,
            parapet_thickness
        ),
        (
            "East",
            width / 2,
            0,
            parapet_thickness,
            depth
        ),
        (
            "West",
            -width / 2,
            0,
            parapet_thickness,
            depth
        )
    ]


    for pname, lx, ly, pw, pd in parapets:

        px, py = local_to_world(
            lx,
            ly,
            cx,
            cy,
            rotation
        )


        create_box(
            (
                f"Bldg_{bid}_"
                f"Parapet_{pname}"
            ),
            (
                px,
                py,
                height
                + parapet_height / 2
                + 0.35
            ),
            (
                pw,
                pd,
                parapet_height
            ),
            DARK_METAL_MAT,
            BUILDINGS_COLL,
            rotation,
            0.03
        )


    # --------------------------------------------------------
    # Rooftop HVAC
    # --------------------------------------------------------

    if (
        width >= 14
        and depth >= 14
    ):

        hx, hy = local_to_world(
            width * 0.22,
            depth * 0.18,
            cx,
            cy,
            rotation
        )


        create_box(
            f"Bldg_{bid}_HVAC",
            (
                hx,
                hy,
                height + 1.45
            ),
            (
                3.8,
                2.5,
                1.7
            ),
            HVAC_MAT,
            BUILDINGS_COLL,
            rotation,
            0.08
        )


        # HVAC fins.
        for fin in range(
            4
        ):

            fx, fy = local_to_world(
                width * 0.08
                + fin * 0.45,
                depth * 0.18,
                cx,
                cy,
                rotation
            )


            create_box(
                (
                    f"Bldg_{bid}_"
                    f"HVACFin_{fin}"
                ),
                (
                    fx,
                    fy,
                    height + 2.35
                ),
                (
                    0.08,
                    2.0,
                    0.55
                ),
                DARK_METAL_MAT,
                BUILDINGS_COLL,
                rotation,
                0.01
            )


    # --------------------------------------------------------
    # Solar panels
    # --------------------------------------------------------

    if (
        width >= 18
        and depth >= 16
    ):

        solar_rows = min(
            3,
            max(
                1,
                int(
                    depth / 8
                )
            )
        )


        for row in range(
            solar_rows
        ):

            sx, sy = local_to_world(
                -width * 0.20,
                -depth * 0.22
                + row * 3.0,
                cx,
                cy,
                rotation
            )


            create_box(
                (
                    f"Bldg_{bid}_"
                    f"Solar_{row}"
                ),
                (
                    sx,
                    sy,
                    height + 0.70
                ),
                (
                    width * 0.34,
                    1.75,
                    0.10
                ),
                SOLAR_MAT,
                BUILDINGS_COLL,
                rotation,
                0.015
            )


    print(
        f"  Building {bid}: "
        f"{building['name']} | "
        f"{width:.1f} x "
        f"{depth:.1f} x "
        f"{height:.1f} m | "
        f"{floors} floors"
    )


# ============================================================
# 12. BUILDINGS
# ============================================================

print("")
print("Generating architectural buildings...")

for building in buildings:

    generate_building(
        building
    )


# ============================================================
# 13. BUILDING COLLISION CHECK
# ============================================================

def point_inside_building(
    px,
    py,
    building,
    padding=0.0
):

    x = float(
        building["x"]
    )

    y = float(
        building["y"]
    )

    width = max(
        1.0,
        float(
            building["width"]
        )
    )

    depth = max(
        1.0,
        float(
            building["depth"]
        )
    )


    rotation = math.radians(
        float(
            building.get(
                "rotation",
                0
            )
        )
    )


    cx, cy = building_center(
        x,
        y,
        width,
        depth
    )


    dx = px - cx
    dy = py - cy


    c = math.cos(
        rotation
    )

    s = math.sin(
        rotation
    )


    local_x = (
        dx * c
        + dy * s
    )

    local_y = (
        -dx * s
        + dy * c
    )


    return (
        abs(local_x)
        <= width / 2
        + padding
        and
        abs(local_y)
        <= depth / 2
        + padding
    )


def inside_any_building(
    x,
    y,
    padding=0.0
):

    for building in buildings:

        if point_inside_building(
            x,
            y,
            building,
            padding
        ):

            return True

    return False


# ============================================================
# 14. SITE GROUND
# ============================================================

create_box(
    "Site_Ground",
    (
        site_width / 2,
        site_height / 2,
        -0.55
    ),
    (
        site_width,
        site_height,
        1.0
    ),
    GRASS_MAT,
    SITE_COLL,
    0,
    0
)


# ============================================================
# 15. GREEN AREAS
# ============================================================

def create_green_area(
    name,
    x,
    y,
    width,
    height
):

    width = max(
        1.0,
        width
    )

    height = max(
        1.0,
        height
    )


    create_box(
        name,
        (
            x + width / 2,
            y + height / 2,
            0.035
        ),
        (
            width,
            height,
            0.07
        ),
        GRASS_MAT,
        GREEN_COLL,
        0,
        0.025
    )


    return (
        x,
        y,
        width,
        height
    )


green_rectangles = []


blueprint_green = blueprint.get(
    "greenAreas",
    []
)


if blueprint_green:

    print("")
    print(
        "Using Blueprint green areas..."
    )


    for index, area in enumerate(
        blueprint_green
    ):

        try:

            gx = float(
                area["x"]
            )

            gy = float(
                area["y"]
            )

            gw = max(
                1.0,
                float(
                    area["width"]
                )
            )

            gh = max(
                1.0,
                float(
                    area["height"]
                )
            )


            green_rectangles.append(
                create_green_area(
                    f"Green_Blueprint_{index}",
                    gx,
                    gy,
                    gw,
                    gh
                )
            )

        except Exception as exc:

            print(
                "WARNING: Invalid green area "
                f"{index}: {exc}"
            )


else:

    print("")
    print(
        "greenAreas[] empty."
    )

    print(
        "Generating procedural green fallback."
    )


    # Central campus quad.
    central_w = site_width * 0.24
    central_h = site_height * 0.18

    central_x = (
        site_width
        - central_w
    ) / 2

    central_y = (
        site_height
        - central_h
    ) / 2


    green_rectangles.append(
        create_green_area(
            "Green_Fallback_Central",
            central_x,
            central_y,
            central_w,
            central_h
        )
    )


    # Four corner landscape pockets.
    pocket_w = site_width * 0.11
    pocket_h = site_height * 0.10


    fallback_positions = [
        (
            site_width * 0.035,
            site_height * 0.035
        ),
        (
            site_width
            - pocket_w
            - site_width * 0.035,
            site_height * 0.035
        ),
        (
            site_width * 0.035,
            site_height
            - pocket_h
            - site_height * 0.035
        ),
        (
            site_width
            - pocket_w
            - site_width * 0.035,
            site_height
            - pocket_h
            - site_height * 0.035
        )
    ]


    for index, (
        gx,
        gy
    ) in enumerate(
        fallback_positions
    ):

        green_rectangles.append(
            create_green_area(
                (
                    f"Green_Fallback_"
                    f"Pocket_{index}"
                ),
                gx,
                gy,
                pocket_w,
                pocket_h
            )
        )


# ============================================================
# 16. ORGANIC TREES
# ============================================================

def create_tree(
    name,
    x,
    y,
    scale=1.0
):

    trunk_height = (
        2.8
        * scale
    )

    trunk_radius = (
        0.22
        * scale
    )


    create_cylinder(
        f"{name}_Trunk",
        (
            x,
            y,
            trunk_height / 2
        ),
        trunk_radius,
        trunk_height,
        BARK_MAT,
        GREEN_COLL,
        12
    )


    clusters = [
        (
            0.0,
            0.0,
            trunk_height + 0.9 * scale,
            1.35 * scale
        ),
        (
            -0.55 * scale,
            0.20 * scale,
            trunk_height + 0.55 * scale,
            1.0 * scale
        ),
        (
            0.50 * scale,
            -0.25 * scale,
            trunk_height + 0.60 * scale,
            1.05 * scale
        ),
        (
            0.0,
            0.20 * scale,
            trunk_height + 1.55 * scale,
            0.95 * scale
        )
    ]


    for index, (
        ox,
        oy,
        oz,
        radius
    ) in enumerate(
        clusters
    ):

        crown = create_ico_sphere(
            (
                f"{name}_Canopy_{index}"
            ),
            (
                x + ox,
                y + oy,
                oz
            ),
            radius,
            LEAF_MAT,
            GREEN_COLL
        )


        variation = (
            0.90
            + (
                (
                    index
                    * 17
                    + int(x)
                    + int(y)
                )
                % 20
            )
            / 100.0
        )


        crown.scale = (
            variation,
            1.0 / variation,
            0.90 + variation * 0.08
        )


# Trees only inside designated green areas.

print("")
print("Generating landscaping...")


tree_id = 0


for rect_index, rect in enumerate(
    green_rectangles
):

    gx, gy, gw, gh = rect


    spacing = clamp(
        min(
            gw,
            gh
        ) / 2.8,
        7.0,
        11.0
    )


    margin = min(
        3.5,
        gw * 0.20,
        gh * 0.20
    )


    x = gx + margin


    while x <= gx + gw - margin:

        y = gy + margin


        while y <= gy + gh - margin:

            # Deterministic jitter.
            jitter_x = random.uniform(
                -1.1,
                1.1
            )

            jitter_y = random.uniform(
                -1.1,
                1.1
            )


            tx = x + jitter_x
            ty = y + jitter_y


            if not inside_any_building(
                tx,
                ty,
                padding=2.0
            ):

                scale = random.uniform(
                    0.85,
                    1.25
                )


                create_tree(
                    f"Tree_{tree_id}",
                    tx,
                    ty,
                    scale
                )


                tree_id += 1


            y += spacing


        x += spacing


# ============================================================
# 17. ROAD GENERATION
# ============================================================

def create_road(
    name,
    x,
    y,
    width,
    length,
    rotation_deg
):

    width = max(
        3.0,
        width
    )

    length = max(
        1.0,
        length
    )


    rotation = math.radians(
        rotation_deg
    )


    dx = math.cos(
        rotation
    )

    dy = math.sin(
        rotation
    )


    cx = (
        x
        + dx * length / 2
    )

    cy = (
        y
        + dy * length / 2
    )


    # Road surface.
    create_box(
        name,
        (
            cx,
            cy,
            0.09
        ),
        (
            length,
            width,
            0.18
        ),
        ASPHALT_MAT,
        ROADS_COLL,
        rotation,
        0.035
    )


    # Curbs.
    curb_offset = (
        width / 2
        + 0.18
    )


    for side in [
        -1,
        1
    ]:

        lx = (
            -dy
            * curb_offset
            * side
        )

        ly = (
            dx
            * curb_offset
            * side
        )


        create_box(
            (
                f"{name}_Curb_{side}"
            ),
            (
                cx + lx,
                cy + ly,
                0.20
            ),
            (
                length,
                0.32,
                0.25
            ),
            CURB_MAT,
            ROADS_COLL,
            rotation,
            0.025
        )


    # Centerline only on reasonably wide roads.
    if width >= 6:

        dash_length = 4.0
        gap = 4.0

        distance = 2.0
        dash_id = 0


        while distance < length - 1:

            segment = min(
                dash_length,
                length - distance
            )


            sx = (
                x
                + dx
                * (
                    distance
                    + segment / 2
                )
            )

            sy = (
                y
                + dy
                * (
                    distance
                    + segment / 2
                )
            )


            create_box(
                (
                    f"{name}_CenterLine_"
                    f"{dash_id}"
                ),
                (
                    sx,
                    sy,
                    0.20
                ),
                (
                    segment,
                    0.16,
                    0.025
                ),
                ROAD_MARK_MAT,
                ROADS_COLL,
                rotation,
                0
            )


            distance += (
                dash_length
                + gap
            )

            dash_id += 1


# ============================================================
# 18. BLUEPRINT ROADS OR FALLBACK
# ============================================================

blueprint_roads = blueprint.get(
    "roads",
    []
)


if blueprint_roads:

    print("")
    print(
        "Using roads from Blueprint..."
    )


    for index, road in enumerate(
        blueprint_roads
    ):

        try:

            create_road(
                (
                    f"Road_Blueprint_"
                    f"{index}"
                ),
                float(
                    road["x"]
                ),
                float(
                    road["y"]
                ),
                float(
                    road["width"]
                ),
                float(
                    road["length"]
                ),
                float(
                    road.get(
                        "rotation",
                        0
                    )
                )
            )

        except Exception as exc:

            print(
                "WARNING: Road "
                f"{index} failed: {exc}"
            )


else:

    print("")
    print(
        "roads[] empty."
    )

    print(
        "Generating intelligent procedural road network."
    )


    # Main entrance.
    if blueprint.get(
        "entrances"
    ):

        first_entrance = blueprint[
            "entrances"
        ][0]

        entrance_x = float(
            first_entrance["x"]
        )

        entrance_y = float(
            first_entrance["y"]
        )

    else:

        entrance_x = (
            site_width / 2
        )

        entrance_y = 0


    # Main north-south spine.
    spine_width = clamp(
        site_width * 0.035,
        8.0,
        12.0
    )


    spine_x = entrance_x


    create_road(
        "Road_Fallback_EntranceSpine",
        spine_x,
        entrance_y,
        spine_width,
        site_height * 0.72,
        90
    )


    # Main east-west arterial.
    arterial_width = clamp(
        site_width * 0.030,
        7.0,
        10.0
    )


    create_road(
        "Road_Fallback_CentralArterial",
        site_width * 0.10,
        site_height * 0.50,
        arterial_width,
        site_width * 0.80,
        0
    )


    # Connect buildings intelligently to nearest road.
    for building in buildings:

        bx, by = building_center(
            float(
                building["x"]
            ),
            float(
                building["y"]
            ),
            float(
                building["width"]
            ),
            float(
                building["depth"]
            )
        )


        # Horizontal connection.
        road_y = site_height * 0.50


        distance = abs(
            by - road_y
        )


        if distance > 8:

            if by < road_y:

                start_y = (
                    by
                    + float(
                        building["depth"]
                    ) / 2
                    + 2.0
                )

                direction = 90

            else:

                start_y = (
                    by
                    - float(
                        building["depth"]
                    ) / 2
                    - 2.0
                )

                direction = 270


            create_road(
                (
                    f"Road_Fallback_"
                    f"Building_{building['id']}"
                ),
                bx,
                start_y,
                max(
                    4.5,
                    site_width * 0.016
                ),
                distance,
                direction
            )


# ============================================================
# 19. WALKWAYS
# ============================================================

def create_walkway(
    name,
    x1,
    y1,
    x2,
    y2,
    width=3.0
):

    dx = x2 - x1
    dy = y2 - y1


    length = math.sqrt(
        dx * dx
        + dy * dy
    )


    if length < 0.1:

        return


    angle = math.atan2(
        dy,
        dx
    )


    create_box(
        name,
        (
            (x1 + x2) / 2,
            (y1 + y2) / 2,
            0.14
        ),
        (
            length,
            width,
            0.10
        ),
        WALKWAY_MAT,
        ROADS_COLL,
        angle,
        0.025
    )


# Main pedestrian spine.
create_walkway(
    "Walkway_MainSpine",
    site_width / 2,
    0,
    site_width / 2,
    site_height * 0.80,
    3.0
)


# Central pedestrian cross.
create_walkway(
    "Walkway_CentralCross",
    site_width * 0.18,
    site_height * 0.50,
    site_width * 0.82,
    site_height * 0.50,
    3.0
)


# ============================================================
# 20. CARS
# ============================================================

def create_car(
    name,
    x,
    y,
    rotation=0.0,
    color_index=0
):

    body_material = CAR_MATS[
        color_index
        % len(CAR_MATS)
    ]


    create_box(
        f"{name}_Body",
        (
            x,
            y,
            0.58
        ),
        (
            2.0,
            4.1,
            0.65
        ),
        body_material,
        PARKING_COLL,
        rotation,
        0.12
    )


    create_box(
        f"{name}_Cabin",
        (
            x,
            y - 0.15,
            1.05
        ),
        (
            1.55,
            2.05,
            0.60
        ),
        CAR_GLASS_MAT,
        PARKING_COLL,
        rotation,
        0.08
    )


    # Wheels need rotation-aware placement.
    for lx in [
        -0.88,
        0.88
    ]:

        for ly in [
            -1.25,
            1.25
        ]:

            wheel_x, wheel_y = local_to_world(
                lx,
                ly,
                x,
                y,
                rotation
            )


            wheel = create_cylinder(
                (
                    f"{name}_Wheel_"
                    f"{lx}_{ly}"
                ),
                (
                    wheel_x,
                    wheel_y,
                    0.34
                ),
                0.30,
                0.20,
                DARK_METAL_MAT,
                PARKING_COLL,
                16,
                (
                    0,
                    math.radians(90),
                    rotation
                )
            )


# ============================================================
# 21. PARKING
# ============================================================

def create_parking(
    name,
    x,
    y,
    width,
    height,
    rotation=0.0
):

    width = max(
        8.0,
        width
    )

    height = max(
        8.0,
        height
    )


    rotation_rad = math.radians(
        rotation
    )


    # Parking surface.
    create_box(
        name,
        (
            x + width / 2,
            y + height / 2,
            0.07
        ),
        (
            width,
            height,
            0.14
        ),
        PARKING_MAT,
        PARKING_COLL,
        rotation_rad,
        0.025
    )


    bay_width = 2.7
    bay_depth = 5.2


    columns = max(
        1,
        int(
            width / bay_width
        )
    )


    rows = max(
        1,
        int(
            height / bay_depth
        )
    )


    car_id = 0


    for row in range(
        rows
    ):

        for col in range(
            columns
        ):

            local_x = (
                -width / 2
                + (
                    col + 0.5
                )
                * bay_width
            )


            local_y = (
                -height / 2
                + (
                    row + 0.5
                )
                * bay_depth
            )


            px, py = local_to_world(
                local_x,
                local_y,
                x + width / 2,
                y + height / 2,
                rotation_rad
            )


            # Stall separator.
            line_x, line_y = local_to_world(
                local_x
                - bay_width / 2
                + 0.10,
                local_y,
                x + width / 2,
                y + height / 2,
                rotation_rad
            )


            create_box(
                (
                    f"{name}_Line_"
                    f"{row}_{col}"
                ),
                (
                    line_x,
                    line_y,
                    0.16
                ),
                (
                    0.08,
                    bay_depth * 0.88,
                    0.025
                ),
                ROAD_MARK_MAT,
                PARKING_COLL,
                rotation_rad,
                0
            )


            # Leave approximately 30% spaces empty.
            if (
                (
                    car_id
                    + row
                    + col
                )
                % 3
                != 2
            ):

                create_car(
                    (
                        f"{name}_Car_"
                        f"{car_id}"
                    ),
                    px,
                    py,
                    rotation_rad,
                    car_id
                )


                car_id += 1


# ============================================================
# 22. BLUEPRINT PARKING OR FALLBACK
# ============================================================

blueprint_parking = blueprint.get(
    "parkingAreas",
    []
)


if blueprint_parking:

    print("")
    print(
        "Using parking areas from Blueprint..."
    )


    for index, parking in enumerate(
        blueprint_parking
    ):

        try:

            create_parking(
                (
                    f"Parking_Blueprint_"
                    f"{index}"
                ),
                float(
                    parking["x"]
                ),
                float(
                    parking["y"]
                ),
                float(
                    parking["width"]
                ),
                float(
                    parking["height"]
                ),
                float(
                    parking.get(
                        "rotation",
                        0
                    )
                )
            )

        except Exception as exc:

            print(
                "WARNING: Parking "
                f"{index} failed: {exc}"
            )


else:

    print("")
    print(
        "parkingAreas[] empty."
    )

    print(
        "Generating procedural parking."
    )


    parking_width = (
        site_width * 0.23
    )

    parking_height = (
        site_height * 0.13
    )


    parking_x = (
        site_width
        * 0.385
    )

    parking_y = (
        site_height
        * 0.055
    )


    create_parking(
        "Parking_Fallback_Main",
        parking_x,
        parking_y,
        parking_width,
        parking_height
    )


# ============================================================
# 23. CAMPUS ENTRANCES
# ============================================================

def create_entrance(
    entrance,
    index
):

    ex = float(
        entrance["x"]
    )

    ey = float(
        entrance["y"]
    )

    ew = max(
        6.0,
        float(
            entrance.get(
                "width",
                10
            )
        )
    )


    pillar_height = 4.5


    # South.
    if ey <= 2:

        create_box(
            f"Gate_{index}_Left",
            (
                ex - ew / 2,
                ey,
                pillar_height / 2
            ),
            (
                1.2,
                1.5,
                pillar_height
            ),
            DARK_METAL_MAT,
            ENTRANCES_COLL,
            0,
            0.08
        )


        create_box(
            f"Gate_{index}_Right",
            (
                ex + ew / 2,
                ey,
                pillar_height / 2
            ),
            (
                1.2,
                1.5,
                pillar_height
            ),
            DARK_METAL_MAT,
            ENTRANCES_COLL,
            0,
            0.08
        )


        create_box(
            f"Gate_{index}_Header",
            (
                ex,
                ey,
                pillar_height
            ),
            (
                ew + 2.0,
                1.0,
                0.65
            ),
            DARK_METAL_MAT,
            ENTRANCES_COLL,
            0,
            0.05
        )


        create_box(
            f"Gate_{index}_Accent",
            (
                ex,
                ey - 0.55,
                pillar_height - 0.1
            ),
            (
                min(
                    ew * 0.50,
                    6.0
                ),
                0.15,
                0.25
            ),
            ACCENT_MAT,
            ENTRANCES_COLL
        )


    # North.
    elif ey >= site_height - 2:

        create_box(
            f"Gate_{index}_Left",
            (
                ex - ew / 2,
                ey,
                pillar_height / 2
            ),
            (
                1.2,
                1.5,
                pillar_height
            ),
            DARK_METAL_MAT,
            ENTRANCES_COLL,
            0,
            0.08
        )


        create_box(
            f"Gate_{index}_Right",
            (
                ex + ew / 2,
                ey,
                pillar_height / 2
            ),
            (
                1.2,
                1.5,
                pillar_height
            ),
            DARK_METAL_MAT,
            ENTRANCES_COLL,
            0,
            0.08
        )


        create_box(
            f"Gate_{index}_Header",
            (
                ex,
                ey,
                pillar_height
            ),
            (
                ew + 2,
                1.0,
                0.65
            ),
            DARK_METAL_MAT,
            ENTRANCES_COLL,
            0,
            0.05
        )


    # West / East entrances.
    else:

        side_x = (
            0
            if ex <= 2
            else site_width
        )


        create_box(
            f"Gate_{index}_PillarA",
            (
                side_x,
                ey - ew / 2,
                pillar_height / 2
            ),
            (
                1.5,
                1.2,
                pillar_height
            ),
            DARK_METAL_MAT,
            ENTRANCES_COLL,
            0,
            0.08
        )


        create_box(
            f"Gate_{index}_PillarB",
            (
                side_x,
                ey + ew / 2,
                pillar_height / 2
            ),
            (
                1.5,
                1.2,
                pillar_height
            ),
            DARK_METAL_MAT,
            ENTRANCES_COLL,
            0,
            0.08
        )


for index, entrance in enumerate(
    blueprint.get(
        "entrances",
        []
    ),
    start=1
):

    create_entrance(
        entrance,
        index
    )


# ============================================================
# 24. PERIMETER
# ============================================================

wall_height = 2.0
wall_thickness = 0.30


entrances = blueprint.get(
    "entrances",
    []
)


south_entrances = [
    float(e["x"])
    for e in entrances
    if float(
        e.get(
            "y",
            0
        )
    ) <= 2
]


# North.
create_box(
    "Boundary_North",
    (
        site_width / 2,
        site_height,
        wall_height / 2
    ),
    (
        site_width,
        wall_thickness,
        wall_height
    ),
    CURB_MAT,
    SITE_COLL,
    0,
    0.03
)


# East.
create_box(
    "Boundary_East",
    (
        site_width,
        site_height / 2,
        wall_height / 2
    ),
    (
        wall_thickness,
        site_height,
        wall_height
    ),
    CURB_MAT,
    SITE_COLL,
    0,
    0.03
)


# West.
create_box(
    "Boundary_West",
    (
        0,
        site_height / 2,
        wall_height / 2
    ),
    (
        wall_thickness,
        site_height,
        wall_height
    ),
    CURB_MAT,
    SITE_COLL,
    0,
    0.03
)


# South with entrance gap.
if south_entrances:

    entrance_x = south_entrances[0]

    gap = max(
        12.0,
        float(
            blueprint[
                "entrances"
            ][0].get(
                "width",
                10
            )
        ) + 4
    )


    left_length = (
        entrance_x
        - gap / 2
    )


    right_length = (
        site_width
        - (
            entrance_x
            + gap / 2
        )
    )


    if left_length > 0:

        create_box(
            "Boundary_South_Left",
            (
                left_length / 2,
                0,
                wall_height / 2
            ),
            (
                left_length,
                wall_thickness,
                wall_height
            ),
            CURB_MAT,
            SITE_COLL,
            0,
            0.03
        )


    if right_length > 0:

        create_box(
            "Boundary_South_Right",
            (
                entrance_x
                + gap / 2
                + right_length / 2,
                0,
                wall_height / 2
            ),
            (
                right_length,
                wall_thickness,
                wall_height
            ),
            CURB_MAT,
            SITE_COLL,
            0,
            0.03
        )


else:

    create_box(
        "Boundary_South",
        (
            site_width / 2,
            0,
            wall_height / 2
        ),
        (
            site_width,
            wall_thickness,
            wall_height
        ),
        CURB_MAT,
        SITE_COLL,
        0,
        0.03
    )


# ============================================================
# 25. STREET LIGHTS
# ============================================================

def create_street_light(
    name,
    x,
    y
):

    # Pole.
    create_cylinder(
        f"{name}_Pole",
        (
            x,
            y,
            3.4
        ),
        0.11,
        6.8,
        DARK_METAL_MAT,
        ROADS_COLL,
        12
    )


    # Cantilever arm.
    create_box(
        f"{name}_Arm",
        (
            x + 0.75,
            y,
            6.65
        ),
        (
            1.5,
            0.14,
            0.14
        ),
        DARK_METAL_MAT,
        ROADS_COLL,
        0,
        0.02
    )


    # Lamp head.
    create_box(
        f"{name}_Head",
        (
            x + 1.45,
            y,
            6.52
        ),
        (
            0.65,
            0.30,
            0.12
        ),
        ACCENT_MAT,
        ROADS_COLL,
        0,
        0.025
    )


    # Actual light.
    light_data = bpy.data.lights.new(
        f"{name}_Light",
        "AREA"
    )

    light_data.energy = 45
    light_data.shape = "DISK"
    light_data.size = 0.8


    light_object = bpy.data.objects.new(
        f"{name}_Light",
        light_data
    )


    LIGHTING_COLL.objects.link(
        light_object
    )


    light_object.location = (
        x + 1.45,
        y,
        6.35
    )


# Roadside lamps.
lamp_spacing = clamp(
    site_width * 0.11,
    25,
    38
)


lamp_x = (
    site_width * 0.12
)

lamp_index = 0


while lamp_x < (
    site_width * 0.90
):

    create_street_light(
        f"StreetLight_{lamp_index}",
        lamp_x,
        site_height * 0.50
    )

    lamp_x += lamp_spacing

    lamp_index += 1


# ============================================================
# 26. DAYLIGHT / NISHITA SKY
# ============================================================

scene = bpy.context.scene


if scene.world is None:

    scene.world = bpy.data.worlds.new(
        "Campus_World"
    )


world = scene.world

world.use_nodes = True


nodes = world.node_tree.nodes
links = world.node_tree.links


nodes.clear()


world_output = nodes.new(
    "ShaderNodeOutputWorld"
)

world_output.location = (
    400,
    0
)


background = nodes.new(
    "ShaderNodeBackground"
)

background.location = (
    150,
    0
)


sky = nodes.new(
    "ShaderNodeTexSky"
)

sky.location = (
    -150,
    0
)


sky.sky_type = "MULTIPLE_SCATTERING"

sky.sun_elevation = math.radians(
    38
)

sky.sun_rotation = math.radians(
    225
)

sky.altitude = 10

sky.air_density = 1.0

sky.dust_density = 1.2

sky.ozone_density = 1.0

sky.ground_albedo = 0.3

sky.sun_intensity = 1.0

sky.sun_disc = True


links.new(
    sky.outputs["Color"],
    background.inputs["Color"]
)


background.inputs[
    "Strength"
].default_value = 0.75


links.new(
    background.outputs["Background"],
    world_output.inputs["Surface"]
)


# ============================================================
# 27. SUN
# ============================================================

sun_data = bpy.data.lights.new(
    "Sun_Daylight",
    "SUN"
)

sun_data.energy = 3.0

sun_data.angle = math.radians(
    12
)


sun = bpy.data.objects.new(
    "Sun_Daylight",
    sun_data
)


LIGHTING_COLL.objects.link(
    sun
)


sun.rotation_euler = (
    math.radians(35),
    math.radians(-25),
    math.radians(140)
)


# ============================================================
# 28. LARGE SOFT FILL
# ============================================================

area_data = bpy.data.lights.new(
    "Architectural_Fill",
    "AREA"
)

area_data.energy = 500

area_data.shape = "DISK"

area_data.size = max(
    100,
    max(
        site_width,
        site_height
    ) * 0.55
)


area = bpy.data.objects.new(
    "Architectural_Fill",
    area_data
)


LIGHTING_COLL.objects.link(
    area
)


area.location = (
    site_width * 0.50,
    site_height * 0.25,
    max(
        site_width,
        site_height
    ) * 0.80
)


area_target = Vector(
    (
        site_width / 2,
        site_height / 2,
        0
    )
)


area_direction = (
    area_target
    - area.location
)


area.rotation_euler = (
    area_direction
    .to_track_quat(
        "-Z",
        "Y"
    )
    .to_euler()
)


# ============================================================
# 29. CAMERA
# ============================================================

print("")
print("Creating architectural cameras...")

center = Vector((
    site_width / 2,
    site_height / 2,
    5
))

max_dimension = max(site_width, site_height)

camera_data = bpy.data.cameras.new(
    "Camera_Architectural_Overview"
)

camera = bpy.data.objects.new(
    "Camera_Architectural_Overview",
    camera_data
)

CAMERAS_COLL.objects.link(camera)

# IMPORTANT: make this the active render camera
scene.camera = camera

# ------------------------------------------------------------
# Architectural overview position
# ------------------------------------------------------------

camera.location = (
    center.x - max_dimension * 0.75,
    center.y - max_dimension * 0.75,
    max_dimension * 0.70
)

# Point camera toward campus center
direction = center - camera.location

camera.rotation_euler = (
    direction
    .to_track_quat("-Z", "Y")
    .to_euler()
)

camera_data.type = "PERSP"

# Wider field of view
camera_data.lens = 38

camera_data.clip_start = 0.1
camera_data.clip_end = max_dimension * 10

# ============================================================
# 30. SECONDARY CAMERA
# ============================================================

detail_camera_data = bpy.data.cameras.new(
    "Camera_Campus_Detail"
)


detail_camera = bpy.data.objects.new(
    "Camera_Campus_Detail",
    detail_camera_data
)


CAMERAS_COLL.objects.link(
    detail_camera
)


detail_camera.location = (
    site_width * 0.18,
    site_height * 0.18,
    max_dimension * 0.18
)


detail_target = Vector(
    (
        site_width * 0.50,
        site_height * 0.50,
        5
    )
)


detail_direction = (
    detail_target
    - detail_camera.location
)


detail_camera.rotation_euler = (
    detail_direction
    .to_track_quat(
        "-Z",
        "Y"
    )
    .to_euler()
)


detail_camera_data.type = "PERSP"

detail_camera_data.lens = 35


# ============================================================
# 31. RENDER ENGINE
# ============================================================

print("")
print(
    f"Render engine: {CLI_ENGINE}"
)


if CLI_ENGINE == "CYCLES":

    scene.render.engine = "CYCLES"

    scene.cycles.samples = 64

    scene.cycles.use_denoising = True

else:

    # Blender 5.2.
    scene.render.engine = "BLENDER_EEVEE"


# ============================================================
# 32. RENDER SETTINGS
# ============================================================

scene.render.resolution_x = 1920

scene.render.resolution_y = 1080

scene.render.resolution_percentage = 100


scene.render.image_settings.file_format = (
    "PNG"
)


scene.render.filepath = (
    RENDER_OUTPUT_PATH
)


scene.render.film_transparent = False


# Color management.
try:

    scene.view_settings.view_transform = (
        "AgX"
    )

    scene.view_settings.look = (
        "AgX - Medium High Contrast"
    )

    scene.view_settings.exposure = (
        -0.20
    )

    scene.view_settings.gamma = 1.0

except Exception:

    pass


# ============================================================
# 33. SCENE METADATA
# ============================================================

scene["HoloEarth_Project_ID"] = (
    project_id
)

scene["HoloEarth_Layout_ID"] = (
    layout_id
)

scene["HoloEarth_Site_Width"] = (
    site_width
)

scene["HoloEarth_Site_Height"] = (
    site_height
)

scene["HoloEarth_Building_Count"] = (
    len(buildings)
)

scene["HoloEarth_Generator"] = (
    "Person 6 Contract 9 Ultimate Procedural Generator"
)

scene["HoloEarth_Procedural"] = True

scene["HoloEarth_No_External_Assets"] = True


# ============================================================
# 34. SAVE BLEND
# ============================================================

print("")
print(
    "Saving Blender scene..."
)


bpy.ops.wm.save_as_mainfile(
    filepath=BLEND_OUTPUT_PATH
)


print(
    "BLEND saved:"
)

print(
    BLEND_OUTPUT_PATH
)


# ============================================================
# 35. RENDER
# ============================================================

print("")
print(
    "Rendering final architectural overview..."
)


scene.camera = camera


bpy.ops.render.render(
    write_still=True
)


# Save after rendering as well.
bpy.ops.wm.save_as_mainfile(
    filepath=BLEND_OUTPUT_PATH
)


# ============================================================
# 36. FINAL REPORT
# ============================================================

print("")
print("=" * 78)
print("HOLOEARTH GENERATION COMPLETE")
print("=" * 78)

print(
    f"Project ID        : {project_id}"
)

print(
    f"Layout ID         : {layout_id}"
)

print(
    f"Site              : "
    f"{site_width:.1f}m x "
    f"{site_height:.1f}m"
)

print(
    f"Buildings         : "
    f"{len(buildings)}"
)

print(
    f"Blueprint Roads   : "
    f"{len(blueprint.get('roads', []))}"
)

print(
    f"Blueprint Green   : "
    f"{len(blueprint.get('greenAreas', []))}"
)

print(
    f"Blueprint Parking : "
    f"{len(blueprint.get('parkingAreas', []))}"
)

print(
    f"Entrances         : "
    f"{len(blueprint.get('entrances', []))}"
)

print("")
print(
    "BLEND:"
)

print(
    BLEND_OUTPUT_PATH
)

print("")
print(
    "RENDER:"
)

print(
    RENDER_OUTPUT_PATH
)

print("")
print(
    "Procedural generation: YES"
)

print(
    "External assets: NONE"
)

print(
    "Database access: NONE"
)

print(
    "Contract 9 Blueprint: YES"
)

print("=" * 78)

scene.camera = camera

scene.render.filepath = os.path.join(
    OUTPUT_DIR,
    "campus.png"
)

bpy.ops.render.render(write_still=True)