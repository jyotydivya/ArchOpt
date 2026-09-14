# ml/ — Person 2: GNN candidate layout generator

Turns a `CampusGraph` (Contract 5) into a population of `CandidateLayout`s
(Contract 6) for Person 3's NSGA-II optimizer.

```python
from ml.inference.generate import generate_candidates

candidates = generate_candidates(campus_graph, 100)   # -> list[CandidateLayout], len 100
```

This module only generates layouts. It does not filter, validate, or rank them.

## Layout

| Path | What |
|---|---|
| `inference/generate.py` | `generate_candidates()`: the function the backend calls |
| `models/features.py` | Column layout of `node_features` / `edge_features`, plus `encode_node()` / `encode_edge()` |
| `models/gnn_encoder.py` | Edge-conditioned message-passing encoder (plain PyTorch, plus a NumPy forward pass) |
| `models/layout_decoder.py` | Embedding + latent noise → `(x, y, rotation)` kept inside the site |
| `models/campus_model.py` | Encoder → decoder, checkpoint load/save |
| `models/weights/campus_model.npz` | Trained weights (~200 KB) |
| `training/mock_graph.py` | Mock and synthetic graphs used until Person 1's `build_graph()` exists |
| `training/loss.py` | Self-supervised losses: overlap, relations, zoning, diversity |
| `training/train.py` | Training loop |
| `training/evaluate.py` | Population diagnostics |
| `tests/` | Contract, unit and Person 3 integration tests |

## Run it

Run all commands from the repo root.

```bash
pip install -r ml/requirements.txt        # numpy is required; torch is optional

python -m ml.inference.generate           # 100 candidates on the mock campus, prints one
python -m ml.training.evaluate --with-optimizer   # overlap / bounds / diversity + P3 validator stats
python -m ml.training.train               # retrain (about 3 min on CPU), overwrites the checkpoint
python -m pytest ml/tests                 # the root pyproject only collects optimization/tests
```

Extra keyword-only options: `seed=` (reproducible output; `None` gives fresh
randomness on each call), `temperature=` (spread of the latent noise),
`weights_path=`, and `backend="auto" | "torch" | "numpy"`.

## How it works

1. `prepare_graph()` validates the graph. It accepts the dataclass, a dict,
   or a camelCase object. It reads site size, ids, footprints, type, and zone
   from the node rows, normalises the features, and adds reverse edges.
2. The GNN encoder runs 3 rounds of message passing and produces one
   64-d embedding per building.
3. For each candidate, the decoder takes `[embedding ‖ graph mean ‖ z_building ‖ z_layout]`.
   Both `z` vectors are fresh Gaussian noise. The decoder outputs `u, v` (the
   centre position inside the allowed range) and `p(rotated 90°)`.
4. `bounded_positions()` converts these to metres. It keeps `x, y ≥ 0` and
   keeps the rotated footprint inside `[0, site_width] × [0, site_height]`.
5. Every `CandidateBuilding` gets `width, depth, height, floor_count, zone, type`
   from the graph. `name` is `"<Type> <id>"`, because the graph carries no
   names. The backend adds catalogue names back for the blueprint.

Coordinates follow the contract: origin at bottom-left, metres, and `(x, y)`
is the bottom-left corner of the unrotated footprint. Rotation is 0° or 90°,
counter-clockwise about the footprint centre.

Training is self-supervised because there are no ground-truth layouts. It
penalises footprint overlap (including the minimum gap), relation distances
(NEAR / FAR / SAME_ZONE / MIN_DISTANCE / MAX_DISTANCE), and same-zone spread.
A diversity term pushes different latent samples apart. Training uses random
synthetic campuses plus the MVP mock campus.

## Graph feature layout (for Person 1)

Contract 5 fixes only the shapes. The generator also needs the site size,
building ids (the backend checks that they match the DB ids), and
footprint/type/zone for each building. Build rows with the helpers so both
sides stay in sync:

```python
from contracts.layout import CampusGraph
from ml.models.features import encode_node, encode_edge

row = encode_node(building_id=b["id"], width=b["width"], depth=b["depth"],
                  height=b["height"], floor_count=b["floorCount"],
                  building_type=b["type"], zone=b["zone"],
                  site_width=campus_data["siteWidth"], site_height=campus_data["siteHeight"])
edge = encode_edge("SAME_ZONE", weight=1.0)                    # or "MIN_DISTANCE", weight, distance=100.0
```

**Node row (20 columns):** `building_id, width, depth, height, floor_count, site_width, site_height`,
then a type one-hot (`academic, library, hostel, admin, sports, parking, other`),
then a zone one-hot (`academic, residential, sports, admin, parking, other`).
Types and zones outside these lists map to `other`. Extra trailing columns are ignored.

**Edge row (9 columns):** a relation one-hot (`NEAR, FAR, SAME_ZONE, ACCESSIBLE_FROM, ROAD_ACCESS, MIN_DISTANCE, MAX_DISTANCE`),
then `weight` (0–1) and `distance` (metres, only for MIN/MAX_DISTANCE).
Shorter or longer rows are zero-padded or truncated. Give each edge once; the
encoder adds the reverse direction.

## The mock graph and swapping in the real builder

`training/mock_graph.py` has `graph_from_campus_data(campus_data)`. It takes
the same dict that `backend/services/orchestrator.py` passes to
`build_graph()` and returns a `CampusGraph` in the layout above:

- one node per building copy (`requiredCount` expands),
- `SAME_ZONE` edges between buildings in the same zone,
- functional type edges (academic–library NEAR, hostel–sports NEAR, admin–parking NEAR, …),
- `MIN_DISTANCE` / `MAX_DISTANCE` edges from user constraints (weight 1.0 if hard, 0.5 if soft).

`build_mock_campus_graph()` is the 9-building, 300 × 300 m MVP campus from
`optimization/mock_data.py`.

When `ml/dataset/graph_builder.py` exists, the backend calls
`build_graph(campus_data)` and passes the result straight to
`generate_candidates()`. Nothing in `ml/models` or `ml/inference` changes, as
long as the rows follow the layout above. Person 1 can copy
`graph_from_campus_data` as a starting point or call `encode_node` / `encode_edge`
directly.

## Integration checks

`tests/test_integration_optimizer.py` runs against the real repo code:

- `generate_candidates(mock_graph, 100)` → `optimize_layouts(..., top_k=5)` returns 5 `RankedLayout`s.
- `backend.services.ml_bridge.run_real_pipeline()` runs end to end. A test
  stub stands in for `ml.dataset.graph_builder`. The 5 layouts contain exactly
  the project's building ids.
