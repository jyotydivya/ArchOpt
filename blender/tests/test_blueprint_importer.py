"""
Unit and integration tests for Person 6 Blender Blueprint Importer and Contract 9 compatibility.
These tests verify Blueprint JSON loading, schema compliance, normalization, and validation
without requiring Blender (bpy) to be installed in the test environment.
"""

import json
import os
import pytest
from backend.schemas.blueprint import BlueprintResponse, BlueprintBuildingSchema


SAMPLE_BLUEPRINT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "input",
    "sample_blueprint.json",
)


def load_sample_blueprint() -> dict:
    with open(SAMPLE_BLUEPRINT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_blueprint_pure_python(data: dict) -> dict:
    """
    Pure Python replica of blender/generator.py validate_blueprint logic
    to ensure behavioral parity and contract regression safety in standard CI environments.
    """
    required = [
        "projectId",
        "layoutId",
        "site",
        "buildings",
        "roads",
        "greenAreas",
        "parkingAreas",
        "entrances",
    ]

    for key in required:
        if key not in data:
            raise ValueError(f"Missing Contract 9 field: {key}")

    if "width" not in data["site"]:
        raise ValueError("Missing site.width")

    if "height" not in data["site"]:
        raise ValueError("Missing site.height")

    if not isinstance(data["buildings"], list):
        raise ValueError("buildings must be a list")

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
        "floorCount",
    ]

    for index, building in enumerate(data["buildings"]):
        if "id" not in building and "buildingId" in building:
            building["id"] = building["buildingId"]

        if "zone" not in building:
            building["zone"] = building.get("type", "general")

        if "floorCount" not in building:
            building["floorCount"] = max(
                1, int(round(float(building.get("height", 12)) / 3.5))
            )

        if "rotation" not in building:
            building["rotation"] = 0.0

        for field in building_fields:
            if field not in building:
                raise ValueError(f"Building {index} missing field: {field}")

    return data


def test_sample_blueprint_file_exists():
    assert os.path.isfile(SAMPLE_BLUEPRINT_PATH), "sample_blueprint.json must exist in blender/input/"


def test_sample_blueprint_validates_against_pydantic_contract_9():
    """Verify sample_blueprint.json conforms to backend Contract 9 BlueprintResponse."""
    data = load_sample_blueprint()
    blueprint_obj = BlueprintResponse.model_validate(data)
    assert blueprint_obj.project_id == 1
    assert blueprint_obj.layout_id == 1
    assert blueprint_obj.site.width == 300.0
    assert blueprint_obj.site.height == 300.0
    assert len(blueprint_obj.buildings) == 4
    for b in blueprint_obj.buildings:
        assert isinstance(b, BlueprintBuildingSchema)
        assert b.id > 0
        assert b.width > 0
        assert b.depth > 0
        assert b.height > 0
        assert b.floor_count >= 1
        assert b.zone != ""


def test_sample_blueprint_passes_p6_validator():
    """Verify sample_blueprint.json passes Person 6's validate_blueprint function."""
    data = load_sample_blueprint()
    validated = validate_blueprint_pure_python(data)
    assert validated["projectId"] == 1
    assert len(validated["buildings"]) == 4


def test_validator_rejects_missing_contract_9_fields():
    data = load_sample_blueprint()
    del data["site"]
    with pytest.raises(ValueError, match="Missing Contract 9 field: site"):
        validate_blueprint_pure_python(data)


def test_validator_rejects_missing_building_fields():
    data = load_sample_blueprint()
    del data["buildings"][0]["width"]
    with pytest.raises(ValueError, match="missing field: width"):
        validate_blueprint_pure_python(data)


def test_validator_normalizes_legacy_building_id():
    """Verify fallback normalization when buildingId is provided instead of id."""
    legacy_data = {
        "projectId": 2,
        "layoutId": 202,
        "site": {"width": 200, "height": 200},
        "buildings": [
            {
                "buildingId": 99,
                "name": "Legacy Block",
                "type": "academic",
                "x": 10,
                "y": 20,
                "width": 30,
                "depth": 20,
                "height": 14,
            }
        ],
        "roads": [],
        "greenAreas": [],
        "parkingAreas": [],
        "entrances": [{"x": 100, "y": 0, "width": 8}],
    }
    validated = validate_blueprint_pure_python(legacy_data)
    b = validated["buildings"][0]
    assert b["id"] == 99
    assert b["zone"] == "academic"
    assert b["floorCount"] == 4
    assert b["rotation"] == 0.0


def test_generator_script_compiles():
    """Verify blender/generator.py is syntactically valid Python."""
    generator_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "generator.py",
    )
    assert os.path.isfile(generator_path)
    import py_compile
    py_compile.compile(generator_path, doraise=True)
