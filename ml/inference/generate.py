"""
ml/inference/generate.py
========================
Person 2 public API — called by backend/services/ml_bridge.py:

    from ml.inference.generate import generate_candidates
    candidates = generate_candidates(campus_graph, num_candidates=100)

Per call:
    CampusGraph ──prepare_graph──▶ validated, normalised arrays
        ──GNN encoder──▶ one embedding per building
        ──decoder, fresh latent noise per candidate──▶ (u, v, vertical)
        ──bounded_positions──▶ list[CandidateLayout]

Generation only: no filtering, validation or ranking (Person 3 owns that).
Runs on PyTorch when installed, otherwise on the NumPy forward pass.
"""
from __future__ import annotations

import functools
import warnings
from pathlib import Path
from typing import Optional, Union

import numpy as np

from contracts.layout import CampusGraph, CandidateBuilding, CandidateLayout
from ml.models.campus_model import DEFAULT_WEIGHTS_PATH, ModelConfig, forward, init_params, load_params
from ml.models.features import prepare_graph
from ml.models.gnn_encoder import Params
from ml.models.layout_decoder import bounded_positions, sigmoid_numpy

# Keeps footprints a few centimetres inside the site so float round-off in
# downstream corner maths never reads as a boundary violation.
BOUNDARY_MARGIN_M = 0.05


@functools.lru_cache(maxsize=4)
def _cached_params(path: str) -> Params:
    return load_params(path)


def load_model_params(weights_path: Union[str, Path, None] = None) -> Params:
    """Trained weights if the checkpoint exists, else seeded untrained weights."""
    path = Path(weights_path) if weights_path is not None else DEFAULT_WEIGHTS_PATH
    if path.exists():
        return _cached_params(str(path))
    warnings.warn(
        f"GNN checkpoint not found at {path}; using untrained weights. "
        "Run `python -m ml.training.train` to create it.",
        RuntimeWarning,
        stacklevel=2,
    )
    return init_params(ModelConfig(), seed=0)


def generate_candidates(
    campus_graph: CampusGraph,
    num_candidates: int = 100,
    *,
    seed: Optional[int] = None,
    temperature: float = 1.0,
    weights_path: Union[str, Path, None] = None,
    backend: str = "auto",
) -> list[CandidateLayout]:
    """
    Generate a diverse population of candidate campus layouts.

    Parameters
    ----------
    campus_graph   : Contract 5 graph from Person 1 (dataclass, camelCase object
                     or dict), columns as in ml/models/features.py.
    num_candidates : number of layouts to return (default 100).
    seed           : latent-noise seed; None draws fresh randomness each call.
    temperature    : latent noise scale; higher = more varied layouts.
    weights_path   : checkpoint override (default ml/models/weights/campus_model.npz).
    backend        : "auto" | "torch" | "numpy".

    Returns
    -------
    list[CandidateLayout] of length num_candidates. Every CandidateBuilding
    carries building_id, x, y, rotation (0 or 90) and the width, depth,
    height, floor_count, zone and type from the graph.
    """
    if isinstance(num_candidates, bool) or int(num_candidates) != num_candidates or num_candidates < 1:
        raise ValueError(f"num_candidates must be a positive integer, got {num_candidates!r}")
    if temperature < 0:
        raise ValueError(f"temperature must be >= 0, got {temperature}")
    num_candidates = int(num_candidates)

    graph = prepare_graph(campus_graph)
    params = load_model_params(weights_path)
    config = ModelConfig()
    rng = np.random.default_rng(seed)
    n = graph.num_nodes

    z_node = rng.standard_normal((num_candidates, n, config.latent_dim)) * temperature
    z_graph = rng.standard_normal((num_candidates, config.latent_dim)) * temperature
    probs = sigmoid_numpy(forward(params, graph, z_node, z_graph, config, backend))

    vertical = (rng.random((num_candidates, n)) < probs[..., 2]).astype(np.float64)
    x, y, *_ = bounded_positions(
        probs[..., 0], probs[..., 1], vertical,
        graph.widths, graph.depths, graph.site_width, graph.site_height,
        margin=BOUNDARY_MARGIN_M,
    )

    id_digits = max(3, len(str(num_candidates)))
    return [
        CandidateLayout(
            candidate_id=f"candidate-{k + 1:0{id_digits}d}",
            site_width=graph.site_width,
            site_height=graph.site_height,
            buildings=[
                CandidateBuilding(
                    building_id=node.building_id,
                    x=float(x[k, i]),
                    y=float(y[k, i]),
                    rotation=90.0 if vertical[k, i] else 0.0,
                    width=node.width,
                    depth=node.depth,
                    zone=node.zone,
                    name=node.name,
                    type=node.type,
                    height=node.height,
                    floor_count=node.floor_count,
                )
                for i, node in enumerate(graph.nodes)
            ],
        )
        for k in range(num_candidates)
    ]


if __name__ == "__main__":
    from ml.training.mock_graph import build_mock_campus_graph

    layouts = generate_candidates(build_mock_campus_graph(), 100, seed=0)
    print(f"generated {len(layouts)} candidates")
    for b in layouts[0].buildings:
        print(f"  {b.building_id:>2} {b.type:<9} {b.zone:<12} x={b.x:6.1f} y={b.y:6.1f} rot={b.rotation:4.0f} {b.width:.0f}x{b.depth:.0f}")
