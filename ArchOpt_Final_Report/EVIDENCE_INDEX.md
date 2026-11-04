# ArchOpt — Technical Evidence and Traceability Index

**Project**: ArchOpt — AI-Powered Campus Planning and Architectural Layout Optimization System  
**Document Purpose**: Traceability matrix linking every architectural claim, algorithmic module, API contract, and empirical result to concrete source code and verified test artifacts.

---

## 1. Architectural & Subsystem Traceability

| Subsystem / Claim | Source Code Location | Responsible Class / Function | Verification Test | Evidence File |
|---|---|---|---|---|
| **Top-Level Orchestration & API** | `backend/main.py`, `backend/services/orchestrator.py` | `FastAPI app`, `run_orchestration_cycle()` | `backend/tests/test_phase10.py` | `docs/person_4_audit_report.md` |
| **P1: Campus Graph Builder** | `ml/dataset/graph_builder.py` | `build_graph(campus_data)` | `ml/dataset/tests/test_graph_builder.py` | 20 unit tests passing |
| **P1: Topological Validation** | `ml/dataset/validation.py` | `validate_campus_data(campus_data)` | `test_validation_rejects_*` | 8 validation checks |
| **Feature Encodings (20 Node, 9 Edge)** | `ml/models/features.py` | `encode_node()`, `encode_edge()`, `prepare_graph()` | `ml/inference/tests/test_models.py` | Fixed one-hot encodings |
| **P2: GNN Message Passing** | `ml/models/gnn_encoder.py` | `GNNEncoder`, `encode_numpy()` | `test_models.py::test_param_shapes_match_torch_module` | Checkpoint `campus_model.npz` |
| **P2: Layout Decoder** | `ml/models/layout_decoder.py` | `LayoutDecoder`, `decode_numpy()`, `bounded_positions()` | `test_bounded_positions_keep_footprint_on_site` | Mathematical proofs of bounds |
| **P2: Candidate Generator** | `ml/inference/generate.py` | `generate_candidates()` | `ml/inference/tests/test_generate.py` | 15 unit tests passing |
| **P3: Spatial Constraint Engine** | `optimization/validator.py` | `validate_layout()` | `optimization/tests/test_validator.py` | 12 unit tests passing |
| **Boundary Checker** | `optimization/constraints/boundary.py` | `check_boundary()` | `optimization/tests/test_boundary.py` | 10 unit tests passing |
| **Overlap & Gap Checker** | `optimization/constraints/overlap.py` | `check_overlaps()` | `optimization/tests/test_overlap.py` | 12 unit tests passing |
| **Distance Checker** | `optimization/constraints/distance.py` | `check_distance()` | `optimization/tests/test_distance.py` | 8 unit tests passing |
| **Green Space Checker** | `optimization/constraints/green.py` | `check_green()` | `optimization/tests/test_green.py` | 6 unit tests passing |
| **Parking Coverage Checker** | `optimization/constraints/parking.py` | `check_parking()` | `optimization/tests/test_parking.py` | 8 unit tests passing |
| **Road Accessibility Checker** | `optimization/constraints/roads.py` | `check_roads()` | `optimization/tests/test_roads.py` | 10 unit tests passing |
| **Zoning Clustering Checker** | `optimization/constraints/zoning.py` | `check_zoning()` | `optimization/tests/test_zoning.py` | 8 unit tests passing |
| **5 Objective Functions** | `optimization/objectives.py` | `compute_objectives()`, `objectives_to_minimise()` | `optimization/tests/test_objectives.py` | 22 unit tests passing |
| **NSGA-II Multi-Objective Engine** | `optimization/nsga2.py` | `rank_population()`, `non_dominated_sort()`, `crowding_distance()` | `optimization/tests/test_nsga2.py` | 16 unit tests passing |
| **Pareto Elite Assembly** | `optimization/ranking.py` | `build_ranked_layouts()` | `optimization/tests/test_optimizer.py` | 14 unit tests passing |
| **P3 Optimizer Entrypoint** | `optimization/optimizer.py` | `optimize_layouts()` | `test_integration_optimizer.py` | Top-5 ranked layouts |
| **P4: Relational Persistence** | `backend/database.py`, `backend/models/*.py` | 8 SQLAlchemy ORM Models | `backend/tests/test_phase5.py` to `test_phase9.py` | Alembic `001_initial_schema.py` |
| **P4: 17 Master REST APIs** | `backend/api/*.py` | 17 registered APIRouters | `backend/tests/test_schemas.py` | `docs/openapi.json` |
| **P5: React Planning UI** | `frontend/src/App.tsx`, `CampusCanvas2D.tsx` | Canvas renderers, coordinate transform | Frontend test suite / Vite app | `frontend/package.json` |
| **P6: Blender Procedural Generation** | `blender/generator.py` | CLI procedural script (`bpy`) | `blender/tests/test_blueprint_importer.py` | 7 tests passing |
| **Shared Contracts (1–9)** | `contracts/layout.py`, `backend/schemas/*.py` | Pydantic / TypeScript data shapes | `backend/tests/test_schemas.py` | Contracts 1 to 9 compliant |

---

## 2. Experimental Data & Results Traceability

| Empirical Claim / Metric | Value | Primary Source Script | Raw Artifact | Figure / Graph |
|---|:---:|---|---|---|
| **Small Campus GNN Feasibility** | 62.0% | `experiments/run_experiments.py` | `results/scenario_summary.csv` (Row 2) | `figures/fig5_constraint_satisfaction_comparison.png` |
| **Small Campus Random Feasibility** | 6.0% | `experiments/run_experiments.py` | `results/scenario_summary.csv` (Row 2) | `figures/fig5_constraint_satisfaction_comparison.png` |
| **Medium Campus GNN Feasibility** | 16.0% | `experiments/run_experiments.py` | `results/scenario_summary.csv` (Row 3) | `figures/fig5_constraint_satisfaction_comparison.png` |
| **Medium Campus Random Feasibility** | 0.0% | `experiments/run_experiments.py` | `results/scenario_summary.csv` (Row 3) | `figures/fig5_constraint_satisfaction_comparison.png` |
| **Top-5 Feasible Yield (S1 & S2)** | 100% (5/5) | `experiments/run_experiments.py` | `results/scenario_results.json` | `figures/fig5_constraint_satisfaction_comparison.png` |
| **GNN Boundary Violations** | 0 / 500 (0.0%) | `experiments/run_experiments.py` | `results/constraint_violations.csv` | `figures/fig6_constraint_violations_breakdown.png` |
| **Random Boundary Violations** | 120 / 500 (24.0%) | `experiments/run_experiments.py` | `results/constraint_violations.csv` | `figures/fig6_constraint_violations_breakdown.png` |
| **Accessibility Score Gain (S1)** | +11.09% | `experiments/run_experiments.py` | `results/objective_progression.csv` (Row 5) | `figures/fig8_initial_vs_optimized_objectives.png` |
| **Accessibility Score Gain (S2)** | +3.71% | `experiments/run_experiments.py` | `results/objective_progression.csv` (Row 10) | `figures/fig8_initial_vs_optimized_objectives.png` |
| **Hypervolume Growth (25 Gens)** | 0.0268 $\to$ 0.0305 | `experiments/run_experiments.py` | `results/generational_convergence.json` | `figures/fig9_generational_convergence.png` |
| **Front 1 Size Growth (25 Gens)** | 8 $\to$ 18 | `experiments/run_experiments.py` | `results/generational_convergence.json` | `figures/fig9_generational_convergence.png` |
| **Spacing Metric Reduction ($\Delta$)** | 0.0184 $\to$ 0.0028 | `experiments/run_experiments.py` | `results/generational_convergence.json` | `figures/fig9_generational_convergence.png` |
| **Graph Construction Latency** | 0.58 $\pm$ 0.63 ms | `experiments/run_experiments.py` | `results/system_benchmarks.json` | `figures/fig10_latency_breakdown.png` |
| **GNN NumPy Inference Latency** | 13.38 $\pm$ 5.98 ms | `experiments/run_experiments.py` | `results/system_benchmarks.json` | `figures/fig10_latency_breakdown.png` |
| **GNN PyTorch Inference Latency** | 46.94 $\pm$ 75.48 ms | `experiments/run_experiments.py` | `results/system_benchmarks.json` | `figures/fig10_latency_breakdown.png` |
| **Validation Latency (100 Layouts)** | 128.15 $\pm$ 15.16 ms | `experiments/run_experiments.py` | `results/system_benchmarks.json` | `figures/fig10_latency_breakdown.png` |
| **NSGA-II Optimization Latency** | 138.76 $\pm$ 17.27 ms | `experiments/run_experiments.py` | `results/system_benchmarks.json` | `figures/fig10_latency_breakdown.png` |
| **Total Real Pipeline Latency** | 177.32 $\pm$ 45.66 ms | `experiments/run_experiments.py` | `results/system_benchmarks.json` | `figures/fig10_latency_breakdown.png` |
| **Peak Resident RAM (RSS)** | 200.65 $\pm$ 0.03 MB | `experiments/run_experiments.py` | `results/system_benchmarks.json` | `results/system_benchmarks.json` |
| **Verified Test Suite Pass Count** | 183 passed, 0 failed | `pytest` CLI runner | Pytest console output | `README.md`, `person_4_audit_report.md` |

