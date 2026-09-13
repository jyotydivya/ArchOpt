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
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        extra="forbid",
    )


class CampusGraphContract(BaseContract):
    node_features: list[list[float]] = Field(..., alias="nodeFeatures")
    edge_index: list[list[int]] = Field(..., alias="edgeIndex")
    edge_features: list[list[float]] = Field(..., alias="edgeFeatures")


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


class P3CandidateBuildingContract(BaseContract):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        extra="ignore",
    )
    building_id: int = Field(..., alias="buildingId")
    x: float
    y: float
    rotation: float = 0.0


class P3RankedLayoutContract(BaseContract):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        extra="ignore",
    )
    candidate_id: str = Field(..., alias="candidateId")
    rank: int
    feasible: bool = True
    buildings: list[P3CandidateBuildingContract]
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

        # Validate P1 output against Contract 5 (CampusGraphContract)
        if hasattr(campus_graph, "model_dump"):
            graph_data = campus_graph.model_dump(by_alias=True)
        elif hasattr(campus_graph, "__dict__") and not isinstance(campus_graph, dict):
            graph_data = vars(campus_graph)
        elif isinstance(campus_graph, dict):
            graph_data = campus_graph
        else:
            raise ValueError(f"Unsupported graph object type: {type(campus_graph)}")

        CampusGraphContract.model_validate(graph_data)
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


def _adapt_requirements_to_p3(requirements: Any) -> Any:
    """
    Converts requirements dictionary (Contract 2) to CampusRequirements dataclass
    if it's not already a CampusRequirements instance.
    """
    if hasattr(requirements, "site_width") and hasattr(requirements, "site_height"):
        return requirements

    if not isinstance(requirements, dict):
        raise ValueError(f"Invalid requirements type: {type(requirements)}")

    project_id = int(requirements.get("projectId") or requirements.get("project_id", 0))
    site_width = float(requirements.get("siteWidth") or requirements.get("site_width", 300.0))
    site_height = float(requirements.get("siteHeight") or requirements.get("site_height", 300.0))
    min_green_percent = float(requirements.get("minGreenPercent") or requirements.get("min_green_percent", 0.0))
    min_parking_percent = float(requirements.get("minParkingPercent") or requirements.get("min_parking_percent", 0.0))
    min_road_width = float(requirements.get("minRoadWidth") or requirements.get("min_road_width", 0.0))
    min_building_gap = float(requirements.get("minBuildingGap") or requirements.get("min_building_gap", 0.0))

    raw_entrances = requirements.get("entrances") or []
    from contracts.layout import CampusRequirements, Entrance

    entrances = []
    for e in raw_entrances:
        if isinstance(e, Entrance):
            entrances.append(e)
        elif isinstance(e, dict):
            entrances.append(
                Entrance(
                    x=float(e.get("x", 0.0)),
                    y=float(e.get("y", 0.0)),
                    width=float(e.get("width", 0.0)),
                )
            )

    return CampusRequirements(
        project_id=project_id,
        site_width=site_width,
        site_height=site_height,
        min_green_percent=min_green_percent,
        min_parking_percent=min_parking_percent,
        min_road_width=min_road_width,
        min_building_gap=min_building_gap,
        entrances=entrances,
    )


def _adapt_constraints_to_p3(constraints: Any) -> list[Any]:
    """
    Converts constraints list (dicts) to list of Constraint dataclasses.
    """
    if constraints is None:
        return []
    if not isinstance(constraints, list):
        raise ValueError(f"Invalid constraints type: {type(constraints)}")

    from contracts.layout import Constraint

    adapted_constraints = []
    for c in constraints:
        if isinstance(c, Constraint):
            adapted_constraints.append(c)
        elif isinstance(c, dict):
            adapted_constraints.append(
                Constraint(
                    id=int(c.get("id", 0)),
                    type=str(c.get("type", "")),
                    source_id=int(c.get("sourceId") or c.get("source_id", 0)),
                    target_id=int(c.get("targetId") or c.get("target_id", 0)),
                    value=float(c.get("value", 0.0)),
                    operator=str(c.get("operator", "==")),
                    priority=str(c.get("priority", "hard")),
                )
            )
        else:
            raise ValueError(f"Unsupported constraint item type: {type(c)}")

    return adapted_constraints


def invoke_p3_optimize_layouts(
    candidates: list[Any],
    requirements: dict[str, Any],
    constraints: list[dict[str, Any]],
    top_k: int,
) -> list[Any]:
    """
    Invokes Person 3 Optimizer: optimize_layouts(candidates, requirements, constraints, top_k) -> list[RankedLayout].
    Adapts dictionary inputs to P3 dataclasses (CampusRequirements, Constraint) if needed.
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
        p3_requirements = _adapt_requirements_to_p3(requirements)
        p3_constraints = _adapt_constraints_to_p3(constraints)

        ranked = optimize_layouts(candidates, p3_requirements, p3_constraints, top_k)
        if not isinstance(ranked, list) or len(ranked) != top_k:
            raise ValueError(
                f"optimize_layouts must return exactly {top_k} ranked layouts, got {len(ranked) if isinstance(ranked, list) else type(ranked)}"
            )
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
    Accepts P3 richer layout objects and normalizes into clean backend persistence format.
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

        validated = P3RankedLayoutContract.model_validate(data)
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
