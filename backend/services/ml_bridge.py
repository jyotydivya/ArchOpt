"""
ML Pipeline Integration Bridge for Person 4 (Backend Orchestrator).
Connects to upstream modules:
- Person 1: ml.dataset.graph_builder (build_graph)
- Person 2: ml.inference.generate (generate_candidates)
- Person 3: optimization.optimizer (optimize_layouts)

Strict Contract Rule:
When REAL mode is active, any missing module, runtime exception, or malformed output
must raise HTTP 422 GENERATION_FAILED (or 500 INTERNAL_SERVER_ERROR).
Never silently fall back to MOCK mode.
"""

from typing import Any, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field


class BaseContract(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class CandidateBuildingContract(BaseContract):
    building_id: int = Field(..., alias="buildingId")
    x: float
    y: float
    rotation: float = 0.0


class CandidateLayoutContract(BaseContract):
    candidate_id: str = Field(..., alias="candidateId")
    site_width: float = Field(..., alias="siteWidth")
    site_height: float = Field(..., alias="siteHeight")
    buildings: list[CandidateBuildingContract]


class RankedLayoutMetricsContract(BaseContract):
    land_utilization: float = Field(..., alias="landUtilization")
    green_ratio: float = Field(..., alias="greenRatio")
    parking_ratio: float = Field(0.0, alias="parkingRatio")
    accessibility_score: float = Field(0.0, alias="accessibilityScore")
    road_efficiency: float = Field(0.0, alias="roadEfficiency")
    constraint_score: float = Field(1.0, alias="constraintScore")


class RankedLayoutContract(BaseContract):
    candidate_id: str = Field(..., alias="candidateId")
    rank: int
    feasible: bool = True
    buildings: list[CandidateBuildingContract]
    metrics: RankedLayoutMetricsContract


def invoke_p1_build_graph(campus_data: dict[str, Any]) -> Any:
    """
    Invokes Person 1 Graph Builder: build_graph(campus_data) -> CampusGraph.
    Raises 422 GENERATION_FAILED if module missing or execution fails.
    """
    try:
        from ml.dataset.graph_builder import build_graph
    except (ImportError, ModuleNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="GENERATION_FAILED",
        ) from exc

    try:
        campus_graph = build_graph(campus_data)
        if campus_graph is None:
            raise ValueError("build_graph returned None")
        return campus_graph
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="GENERATION_FAILED",
        ) from exc


def invoke_p2_generate_candidates(campus_graph: Any, num_candidates: int) -> list[Any]:
    """
    Invokes Person 2 GNN Generator: generate_candidates(campus_graph, num_candidates) -> list[CandidateLayout].
    Raises 422 GENERATION_FAILED if module missing or execution fails.
    """
    try:
        from ml.inference.generate import generate_candidates
    except (ImportError, ModuleNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="GENERATION_FAILED",
        ) from exc

    try:
        candidates = generate_candidates(campus_graph, num_candidates)
        if not isinstance(candidates, list) or len(candidates) == 0:
            raise ValueError("generate_candidates returned invalid or empty candidates")
        return candidates
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="GENERATION_FAILED",
        ) from exc


def invoke_p3_optimize_layouts(
    candidates: list[Any],
    requirements: dict[str, Any],
    constraints: list[dict[str, Any]],
    top_k: int,
) -> list[Any]:
    """
    Invokes Person 3 Optimizer: optimize_layouts(candidates, requirements, constraints, top_k) -> list[RankedLayout].
    Raises 422 GENERATION_FAILED if module missing or execution fails.
    """
    try:
        from optimization.optimizer import optimize_layouts
    except (ImportError, ModuleNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="GENERATION_FAILED",
        ) from exc

    try:
        ranked = optimize_layouts(candidates, requirements, constraints, top_k)
        if not isinstance(ranked, list) or len(ranked) == 0:
            raise ValueError("optimize_layouts returned invalid or empty ranked layouts")
        return ranked
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="GENERATION_FAILED",
        ) from exc


def validate_and_format_ranked_layout(raw_layout: Any) -> dict[str, Any]:
    """
    Validates a ranked layout against Contract 8 (RankedLayout).
    Raises 422 GENERATION_FAILED if layout data is malformed.
    """
    try:
        if hasattr(raw_layout, "model_dump"):
            data = raw_layout.model_dump(by_alias=True)
        elif hasattr(raw_layout, "__dict__") and not isinstance(raw_layout, dict):
            data = vars(raw_layout)
        elif isinstance(raw_layout, dict):
            data = raw_layout
        else:
            raise ValueError(f"Unsupported layout object type: {type(raw_layout)}")

        validated = RankedLayoutContract.model_validate(data)
        dump = validated.model_dump(by_alias=True)

        formatted_buildings = [
            {
                "buildingId": b["buildingId"],
                "x": b["x"],
                "y": b["y"],
                "rotation": b.get("rotation", 0.0),
            }
            for b in dump["buildings"]
        ]

        return {
            "candidateId": dump["candidateId"],
            "rank": dump["rank"],
            "feasible": dump["feasible"],
            "buildings": formatted_buildings,
            "metrics": dump["metrics"],
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="GENERATION_FAILED",
        ) from exc


def run_real_pipeline(
    campus_data: dict[str, Any],
    requirements_dict: dict[str, Any],
    constraints_list: list[dict[str, Any]],
    candidate_count: int = 100,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Executes the real P1 -> P2 -> P3 pipeline in strict sequence.
    Any failure at any stage surfaces 422 GENERATION_FAILED.
    Zero silent fallback to mock pipeline.
    """
    try:
        # 1. P1: Graph Builder
        campus_graph = invoke_p1_build_graph(campus_data)

        # 2. P2: GNN Candidate Generator
        candidates = invoke_p2_generate_candidates(campus_graph, num_candidates=candidate_count)

        # 3. P3: NSGA-II Multi-Objective Optimizer
        ranked_candidates = invoke_p3_optimize_layouts(
            candidates=candidates,
            requirements=requirements_dict,
            constraints=constraints_list,
            top_k=top_k,
        )

        # 4. Strict Contract 8 validation
        validated_layouts: list[dict[str, Any]] = []
        for item in ranked_candidates:
            validated_layout = validate_and_format_ranked_layout(item)
            validated_layouts.append(validated_layout)

        return validated_layouts
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="GENERATION_FAILED",
        ) from exc
