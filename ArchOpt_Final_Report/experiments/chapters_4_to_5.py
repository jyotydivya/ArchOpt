"""
ArchOpt_Final_Report/experiments/chapters_4_to_5.py
===================================================
Contains text, tables, formulas, and formatting for Chapters 4 and 5.
Uses publication-quality Unicode math typography and add_equation() blocks.
"""
from __future__ import annotations

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

from build_docx_report import (
    add_callout,
    add_equation,
    add_fig,
    add_h1,
    add_h2,
    add_h3,
    add_p,
    format_table_headers,
    set_cell_margins,
    set_cell_shading,
    FIGURES_DIR,
)


# ==============================================================================
# CHAPTER 4: SYSTEM DESIGN AND ARCHITECTURE
# ==============================================================================

def build_chapter_4(doc):
    add_h1(doc, "CHAPTER 4: SYSTEM DESIGN AND ARCHITECTURE")

    # 4.1 System Architecture Overview
    add_h2(doc, "4.1 High-Level Microservice System Architecture")
    p1 = (
        "The architecture of ArchOpt is structured as a decoupled, multi-tiered microservice pipeline organized around "
        "strict data contracts and explicit separation of engineering concerns. The system bridges five foundational technical domains: "
        "relational data persistence, RESTful API orchestration, geometric graph neural networks, multi-objective evolutionary computation, "
        "and procedural computer graphics rendering."
    )
    p2 = (
        "Figure 1.1 illustrates the comprehensive end-to-end architecture and inter-subsystem data flows governing ArchOpt. "
        "The frontend client—implemented as a responsive Single Page Application (SPA) in React 18 and Vite—communicates with the "
        "backend through standardized JSON payloads over HTTP/1.1 REST interfaces. The backend, constructed with FastAPI and Python 3.11, "
        "orchestrates business logic, manages JWT security, persists relational state in PostgreSQL via SQLAlchemy ORM and Alembic migrations, "
        "and delegates computational generation to the integrated Python AI Engine."
    )
    add_p(doc, p1)
    add_p(doc, p2)

    add_fig(doc, FIGURES_DIR / "fig1_system_architecture.png", "1.1",
            "ArchOpt End-to-End System Architecture and Multi-Module Flow")

    p3 = (
        "The core principle guiding this architectural hierarchy is captured by the project's foundational operational maxim:\n"
        "1. AI decides WHERE: The Graph Neural Network (P2) ingests the topological graph and proposes spatial coordinates (x, y, θ) "
        "guided by learned spatial relational priors.\n"
        "2. Optimization decides WHICH: The NSGA-II Optimizer (P3) evaluates candidate layouts against 8 strict spatial constraints and ranks them "
        "across 5 competing objective functions to isolate the Pareto-optimal designs.\n"
        "3. The Frontend lets the planner CHOOSE: The React 2D planning interface (P5) surfaces the top-5 Pareto layouts, enabling the campus planner "
        "to evaluate visual trade-offs and select the preferred master plan.\n"
        "4. Blender decides HOW: The procedural graphics engine (P6) consumes the validated Contract 9 Blueprint JSON and procedurally instantiates "
        "photorealistic 3D architectural geometry, materials, lighting, and camera perspectives."
    )
    add_p(doc, p3)

    # 4.2 Subsystem Decomposition and Workstream Allocation
    add_h2(doc, "4.2 Subsystem Decomposition and Workstream Allocation")
    add_p(doc, "To achieve clean engineering modularity, the codebase is decomposed into six specialized workstreams mapped directly to verified repository directories, as summarized in Table 4.1.")

    workstream_data = [
        ("Divya Jyoty – 23BCE20341 (P3)", "Spatial Constraint Validation Engine & NSGA-II Optimizer", "optimization/", "Validates 8 spatial constraints, evaluates 5 competing objectives, executes NSGA-II Pareto ranking, outputs top-5 plans (Contract 8)."),
        ("Bakaraju Krishna Teja – 24BCE7012 (P4)", "FastAPI REST Backend, Relational Database & System Orchestrator", "backend/, alembic/, contracts/", "Hosts 17 Master REST APIs, manages 8 PostgreSQL tables, enforces JWT security, coordinates ML Bridge orchestration."),
        ("Satya Tanmayi Pemmadi – 24BCA7375 (P2)", "Deep Graph Neural Network Model & Spatial Layout Decoder", "ml/models/, ml/training/, ml/inference/", "Constructs GNN message-passing encoder and latent-conditioned layout decoder; generates candidate populations (Contract 6)."),
        ("Tanuj Krishna Aggarwal – 24BCA7536 (P5)", "React 2D Campus Planning User Interface & Interactive Canvas", "frontend/", "Constructs interactive React 19 canvas, enables requirements configuration, displays real-time layout comparisons and metrics."),
        ("Rajjeet Saha – 24BCE7101 (P6)", "Blender Headless Procedural 3D Modeling & Rendering Pipeline", "blender/", "Consumes Contract 9 Blueprint JSON, procedurally generates 3D buildings, roads, foliage, lighting, and renders final imagery."),
        ("Anshika Singh – 23BCE7284 (P1)", "Campus Schema, Synthetic Dataset & Topological Graph Builder", "ml/data/, ml/dataset/", "Transforms raw backend campus specifications into Contract 5 CampusGraph with [N, 20] node features and [E, 9] edge features.")
    ]
    tbl_ws = doc.add_table(rows=len(workstream_data) + 1, cols=4)
    tbl_ws.alignment = WD_TABLE_ALIGNMENT.CENTER
    ws_headers = ["Engineering Role", "Functional Domain", "Repository Modules", "Core Technical Responsibilities"]
    for j, h in enumerate(ws_headers):
        tbl_ws.rows[0].cells[j].paragraphs[0].text = h
    for i, row in enumerate(workstream_data):
        for j, val in enumerate(row):
            tbl_ws.rows[i + 1].cells[j].paragraphs[0].text = val
    format_table_headers(tbl_ws, [1.2, 1.8, 1.5, 2.0])
    add_p(doc, "Table 4.1: ArchOpt Subsystem Decomposition and Team Workstream Allocation Matrix",
          align=WD_ALIGN_PARAGRAPH.CENTER, size=10, bold=True, space_before=4, after=12)

    # 4.3 Mathematical Formulation of Campus Graph Topology
    add_h2(doc, "4.3 Mathematical Formulation of Campus Graph Topology")
    p_graph1 = (
        "ArchOpt formalizes the campus master planning domain as a directed, attributed multi-graph G = (V, E, X_v, X_e), "
        "where V = {v_1, v_2, ..., v_N} denotes the set of N building nodes (expanded from catalog entries based on `requiredCount`), "
        "E ⊆ V × V represents directed relational edges, X_v ∈ ℝ^(N × 20) is the node feature matrix, "
        "and X_e ∈ ℝ^(E × 9) is the edge feature matrix."
    )
    add_p(doc, p_graph1)

    add_fig(doc, FIGURES_DIR / "fig2_graph_representation.png", "4.1",
            "Topological Campus Graph Representation and Spatial Constraint Edges")

    add_p(doc, "The exact feature vector encodings for nodes and edges are documented in Tables 4.2 and 4.3, adhering strictly to `ml/models/features.py`.")

    # Table 4.2: Node Features
    node_feat_data = [
        ("Indices 0–5 (6 dims)", "Normalized Geometry", "Width (w / W_site), Depth (d / H_site), Area ((w · d) / (W_site · H_site)), Aspect Ratio (w / d), Normalized Height (h / 30), Floor Count (f / 10)"),
        ("Indices 6–12 (7 dims)", "Building Type One-Hot", "academic, library, hostel, admin, sports, parking, other"),
        ("Indices 13–18 (6 dims)", "Campus Zone One-Hot", "academic, residential, admin, sports, parking, other"),
        ("Index 19 (1 dim)", "Site Footprint Ratio", "Footprint area relative to maximum building area ((w · d) / max_j(w_j · d_j))")
    ]
    tbl_nf = doc.add_table(rows=len(node_feat_data) + 1, cols=3)
    tbl_nf.alignment = WD_TABLE_ALIGNMENT.CENTER
    nf_headers = ["Tensor Slice", "Feature Semantic", "Mathematical Encoding & Normalization"]
    for j, h in enumerate(nf_headers):
        tbl_nf.rows[0].cells[j].paragraphs[0].text = h
    for i, row in enumerate(node_feat_data):
        for j, val in enumerate(row):
            tbl_nf.rows[i + 1].cells[j].paragraphs[0].text = val
    format_table_headers(tbl_nf, [1.5, 1.8, 3.2])
    add_p(doc, "Table 4.2: Input Node Feature Vector Specifications ([N, 20] Encodings)",
          align=WD_ALIGN_PARAGRAPH.CENTER, size=10, bold=True, space_before=4, after=12)

    # Table 4.3: Edge Features
    edge_feat_data = [
        ("Indices 0–6 (7 dims)", "Relationship One-Hot", "SAME_ZONE, NEAR, FAR, ACCESSIBLE_FROM, ROAD_ACCESS, MIN_DISTANCE, MAX_DISTANCE"),
        ("Index 7 (1 dim)", "Normalized Distance", "Target distance D / √(W_site² + H_site²) (0.0 for qualitative edges)"),
        ("Index 8 (1 dim)", "Constraint Weight", "Weight scalar: 1.0 for hard constraints and functional rules; 0.5 for soft user rules")
    ]
    tbl_ef = doc.add_table(rows=len(edge_feat_data) + 1, cols=3)
    tbl_ef.alignment = WD_TABLE_ALIGNMENT.CENTER
    ef_headers = ["Tensor Slice", "Feature Semantic", "Mathematical Encoding & Normalization"]
    for j, h in enumerate(ef_headers):
        tbl_ef.rows[0].cells[j].paragraphs[0].text = h
    for i, row in enumerate(edge_feat_data):
        for j, val in enumerate(row):
            tbl_ef.rows[i + 1].cells[j].paragraphs[0].text = val
    format_table_headers(tbl_ef, [1.5, 1.8, 3.2])
    add_p(doc, "Table 4.3: Input Edge Feature Vector Specifications ([E, 9] Encodings)",
          align=WD_ALIGN_PARAGRAPH.CENTER, size=10, bold=True, space_before=4, after=12)

    # 4.4 GNN Architecture
    add_h2(doc, "4.4 Graph Neural Network Generative Architecture")
    p_gnn1 = (
        "The neural generative engine of ArchOpt is structured as an encoder-decoder architecture specifically engineered "
        "for continuous spatial placement. Figure 4.2 illustrates the complete tensor transformations from input graph to layout."
    )
    add_p(doc, p_gnn1)

    add_fig(doc, FIGURES_DIR / "fig3_gnn_architecture.png", "4.2",
            "Graph Neural Network Architecture (GNN Encoder & Spatial Layout Decoder)")

    # 1. GNN Encoder Formulation
    add_p(doc, "1. GNN Encoder Formulation: The input node feature vectors x_i ∈ ℝ²⁰ are first projected into a d_h = 64 "
               "hidden dimensional embedding space via a linear projection:")
    add_equation(doc, "h_i⁽⁰⁾ = ReLU(W_in · x_i + b_in)", "4.1")

    add_p(doc, "The model executes L = 3 message-passing iterations. In each layer l ∈ {1, 2, 3}, a directed message m_ij⁽ˡ⁾ "
               "is computed across edge (i, j) by concatenating the sender node representation and edge feature vector e_ij ∈ ℝ⁹:")
    add_equation(doc, "m_ij⁽ˡ⁾ = ReLU(W_m⁽ˡ⁾ · [h_j⁽ˡ⁻¹⁾ ∥ e_ij] + b_m⁽ˡ⁾)", "4.2")

    add_p(doc, "Incoming messages for node i are aggregated via sum pooling over its local neighborhood N(i), and the node hidden state is updated through a residual update function:")
    add_equation(doc, "h_i⁽ˡ⁾ = ReLU(W_u⁽ˡ⁾ · [h_i⁽ˡ⁻¹⁾ ∥ ∑_{j ∈ N(i)} m_ij⁽ˡ⁾] + b_u⁽ˡ⁾)", "4.3")

    add_p(doc, "A global graph-level representation h_graph ∈ ℝ⁶⁴ is computed via global mean pooling across all N building node embeddings:")
    add_equation(doc, "h_graph = (1 / N) · ∑_{i=1}^{N} h_i⁽ᴸ⁾", "4.4")

    # 2. Spatial Layout Decoder Formulation
    add_p(doc, "2. Spatial Layout Decoder Formulation: To generate diverse candidate layouts, the decoder conditions on stochastic latent priors. "
               "For candidate k, node-specific latent vectors z_i⁽ᵏ⁾ ~ N(0, I₁₆) and a graph-level latent vector z_graph⁽ᵏ⁾ ~ N(0, I₁₆) "
               "are concatenated with the deterministic node and graph embeddings:")
    add_equation(doc, "y_i⁽ᵏ⁾ = [h_i⁽ᴸ⁾ ∥ h_graph ∥ z_i⁽ᵏ⁾ ∥ z_graph⁽ᵏ⁾] ∈ ℝ¹⁶⁰", "4.5")

    add_p(doc, "The decoder multi-layer perceptron (MLP) processes y_i⁽ᵏ⁾ through two hidden layers with ReLU activations to emit 3 raw unconstrained logits per building node:")
    add_equation(doc, "s_i⁽ᵏ⁾ = [s_{u, i}⁽ᵏ⁾, s_{v, i}⁽ᵏ⁾, s_{θ, i}⁽ᵏ⁾] = W_out · ReLU(W_d2 · ReLU(W_d1 · y_i⁽ᵏ⁾ + b_d1) + b_d2) + b_out", "4.6")

    add_p(doc, "Applying the element-wise sigmoid activation function yields normalized placement probabilities [u_i, v_i, p_{vert, i}] = σ(s_i⁽ᵏ⁾) ∈ [0, 1]³.")

    # 3. Guaranteed Analytical Boundary Projection
    add_p(doc, "3. Guaranteed Analytical Boundary Projection: Rather than penalizing out-of-bounds placements with soft loss terms, ArchOpt guarantees "
               "100% boundary compliance through an analytical bounding function (`bounded_positions()`). If building i is assigned cardinal rotation "
               "θ_i = 90° (when p_{vert, i} > 0.5), its effective planar width and depth are transposed (w_eff = d_i, d_eff = w_i). "
               "The spatial bottom-left vertex coordinates (x_i, y_i) are deterministically projected onto the site domain using:")
    add_equation(doc, "x_i = margin + u_i · (W_site − w_eff − 2 · margin)", "4.7")
    add_equation(doc, "y_i = margin + v_i · (H_site − d_eff − 2 · margin)", "4.8")

    add_p(doc, "where margin = 0.05 m. Because u_i, v_i ∈ [0, 1], this formulation mathematically guarantees that:")
    add_equation(doc, "0 < x_i < x_i + w_eff < W_site,     0 < y_i < y_i + d_eff < H_site", "4.9")
    add_p(doc, "completely eliminating boundary violations by construction.")

    # 4.5 NSGA-II Optimization
    add_h2(doc, "4.5 Multi-Objective NSGA-II Optimization Engine")
    p_opt1 = (
        "The candidate layouts synthesized by the GNN are transferred to the Person 3 Optimization Engine. Figure 4.3 depicts "
        "the multi-stage optimization workflow executing constraint checking, objective evaluation, and Pareto ranking."
    )
    add_p(doc, p_opt1)

    add_fig(doc, FIGURES_DIR / "fig4_nsga2_workflow.png", "4.3",
            "NSGA-II Multi-Objective Optimization and Pareto Ranking Workflow")

    p_opt2 = (
        "1. Mathematical Objective Functions: ArchOpt formalizes five distinct master planning objectives, as defined in Table 4.4. "
        "All metrics are normalized to [0, 1], where higher values represent superior architectural utility. For algorithmic consistency "
        "with minimization-based evolutionary solvers, the NSGA-II module inverts each objective (f_m^min = 1.0 − f_m)."
    )
    add_p(doc, p_opt2)

    # Table 4.4: Objectives
    obj_data = [
        ("1. Land Utilization (f_land)", "(1 / (W_site · H_site)) · ∑_{i=1}^N (w_i · d_i)", "Maximizes structural footprint utilization relative to gross site parcel area."),
        ("2. Green Space Ratio (f_green)", "1.0 − (1 / (W_site · H_site)) · (A_built + A_road + A_park)", "Maximizes permeable, vegetated environmental land coverage."),
        ("3. Parking Ratio (f_park)", "(∑_{b ∈ parking} w_b · d_b) / (W_site · H_site)", "Maximizes vehicular parking capacity relative to campus site area."),
        ("4. Accessibility Score (f_access)", "1.0 − (1 / (N · D_diag)) · ∑_{i=1}^N min_{e ∈ E} dist(c_i, e)", "Minimizes pedestrian transit distances from building centers to entrances."),
        ("5. Road Efficiency (f_road)", "1.0 − Length(MST({c_i} ∪ E)) / ((N + M) · D_diag)", "Minimizes vehicular infrastructure length via Prim's Minimum Spanning Tree.")
    ]
    tbl_obj = doc.add_table(rows=len(obj_data) + 1, cols=3)
    tbl_obj.alignment = WD_TABLE_ALIGNMENT.CENTER
    obj_headers = ["Objective Metric", "Mathematical Formulation", "Architectural Intent & Normalization"]
    for j, h in enumerate(obj_headers):
        tbl_obj.rows[0].cells[j].paragraphs[0].text = h
    for i, row in enumerate(obj_data):
        for j, val in enumerate(row):
            tbl_obj.rows[i + 1].cells[j].paragraphs[0].text = val
    format_table_headers(tbl_obj, [1.8, 2.4, 2.3])
    add_p(doc, "Table 4.4: Mathematical Multi-Objective Optimization Formulation (5 Objective Functions)",
          align=WD_ALIGN_PARAGRAPH.CENTER, size=10, bold=True, space_before=4, after=12)

    p_opt3 = (
        "2. Spatial Constraint Validation Mechanics: The constraint validator evaluates eight discrete rule sets for each candidate:\n"
        "• Hard Site Boundary: Verifies that rotated polygon vertices reside strictly within [0, W_site] × [0, H_site].\n"
        "• Hard Footprint Overlap: Uses Shapely polygon intersection to detect spatial collisions (Area(P_i ∩ P_j) > 0).\n"
        "• Hard Minimum Building Gap: Evaluates minimum Euclidean separation against clearance threshold g_min (dist(P_i, P_j) ≥ g_min).\n"
        "• Hard/Soft Named Distances: Enforces user-prescribed pairwise Euclidean distances (dist(b_i, b_j) ≥ D or dist(b_i, b_j) ≤ D).\n"
        "• Hard Minimum Green Coverage: Validates that computed green ratio meets or exceeds threshold γ_min.\n"
        "• Hard Minimum Parking Coverage: Validates that computed parking ratio meets or exceeds threshold ρ_min.\n"
        "• Hard Entrance Road Reachability: Confirms every building is connected to at least one entrance via the circulation tree.\n"
        "• Soft Zone Clustering: Penalizes layouts where same-zone buildings exceed the spatial clustering threshold (0.45 · min(W_site, H_site))."
    )
    add_p(doc, p_opt3)

    add_p(doc, "A composite constraint score S_const ∈ [0, 1] is computed across all evaluated rules:")
    add_equation(doc, "S_const = 1.0 − (N_hard + 0.5 · N_soft) / N_rules", "4.10")
    add_p(doc, "Layouts with N_hard = 0 are designated as strictly feasible (feasible = True).")

    p_opt4 = (
        "3. Pareto Ranking & Crowding Distance Selection: In accordance with Deb et al. (2002), NSGA-II executes fast non-dominated sorting. "
        "A layout a dominates b (denoted a ≺ b) if and only if ∀ m: f_m(a) ≤ f_m(b) and ∃ m: f_m(a) < f_m(b). The population is partitioned into sequential Pareto fronts F_1, F_2, .... "
        "Within each front, population diversity is preserved via the crowding distance metric I_d(i):"
    )
    add_p(doc, p_opt4)
    add_equation(doc, "I_d(i) = ∑_{m=1}^{M} [f_m(i+1) − f_m(i−1)] / [f_m^max − f_m^min]", "4.11")
    add_p(doc, "Layouts are lexicographically sorted by (front_number ASC, I_d DESC), prioritizing feasible plans to construct the final top-5 RankedLayout list.")

    # 4.6 Backend & DB Design
    add_h2(doc, "4.6 Backend Subsystem and Relational Database Schema")
    p_be1 = (
        "The backend is constructed with FastAPI and PostgreSQL, providing a resilient persistence layer and strict schema validation. "
        "Figure 4.4 illustrates the relational Entity-Relationship (ER) model across all 8 contract tables."
    )
    add_p(doc, p_be1)

    add_fig(doc, FIGURES_DIR / "fig12_database_er_diagram.png", "4.4",
            "PostgreSQL Relational Database Schema and Contract Tables (Alembic Head)")

    add_p(doc, "Table 4.5 registers the 17 verified Master REST APIs hosted by the FastAPI application.")

    # Table 4.5: 17 Master APIs
    api_data = [
        ("POST /api/auth/register", "Public", "Registers new user with Bcrypt password hash", "201 Created (UserRegisterResponse)"),
        ("POST /api/auth/login", "Public", "Authenticates credentials and returns JWT Bearer token", "200 OK (UserLoginResponse)"),
        ("POST /api/projects", "Bearer", "Creates a new campus master planning project", "201 Created (ProjectResponse)"),
        ("GET /api/projects/{id}", "Bearer", "Retrieves project metadata and current lifecycle status", "200 OK (ProjectResponse)"),
        ("PUT /api/projects/{id}", "Bearer", "Updates project name, description, or status", "200 OK (ProjectResponse)"),
        ("DELETE /api/projects/{id}", "Bearer", "Deletes project and cascades dependent requirements", "204 No Content"),
        ("POST /api/projects/{id}/requirements", "Bearer", "Saves campus boundary, green %, parking %, entrances", "201 Created (RequirementsResponse)"),
        ("GET /api/projects/{id}/requirements", "Bearer", "Fetches validated campus requirements payload", "200 OK (RequirementsResponse)"),
        ("POST /api/projects/{id}/buildings", "Bearer", "Appends a building entity to project catalog", "201 Created (BuildingResponse)"),
        ("GET /api/projects/{id}/buildings", "Bearer", "Lists all building entities in project catalog", "200 OK (BuildingListResponse)"),
        ("POST /api/projects/{id}/constraints", "Bearer", "Appends a spatial constraint rule to project", "201 Created (ConstraintResponse)"),
        ("GET /api/projects/{id}/constraints", "Bearer", "Lists all spatial constraints defined for project", "200 OK (ConstraintListResponse)"),
        ("POST /api/projects/{id}/layout-runs", "Bearer", "Triggers asynchronous generative optimization run", "200 OK (LayoutRunCreateResponse)"),
        ("GET /api/projects/{id}/layouts", "Bearer", "Lists generated layout candidates with ranks and metrics", "200 OK (LayoutListResponse)"),
        ("GET /api/layouts/{id}", "Bearer", "Retrieves complete single layout details with coordinates", "200 OK (LayoutDetailResponse)"),
        ("POST /api/layouts/{id}/select", "Bearer", "Marks layout as the officially selected master plan", "200 OK (LayoutSelectResponse)"),
        ("GET /api/layouts/{id}/blueprint", "Bearer", "Exports Contract 9 Blueprint JSON for Blender 3D render", "200 OK (BlueprintResponse)")
    ]
    tbl_api = doc.add_table(rows=len(api_data) + 1, cols=4)
    tbl_api.alignment = WD_TABLE_ALIGNMENT.CENTER
    api_headers = ["HTTP Endpoint", "Auth", "Functional Operation", "Contract Response"]
    for j, h in enumerate(api_headers):
        tbl_api.rows[0].cells[j].paragraphs[0].text = h
    for i, row in enumerate(api_data):
        for j, val in enumerate(row):
            tbl_api.rows[i + 1].cells[j].paragraphs[0].text = val
    format_table_headers(tbl_api, [2.2, 0.8, 2.2, 1.8])
    add_p(doc, "Table 4.5: Master REST API Contract Specification Matrix (17 Endpoints)",
          align=WD_ALIGN_PARAGRAPH.CENTER, size=10, bold=True, space_before=4, after=12)

    # 4.7 Frontend Planning Interface
    add_h2(doc, "4.7 Frontend Planning Interface and Interactive 2D Canvas")
    p_fe = (
        "The frontend is implemented in TypeScript, React 18, and Vite. The core interface (`CampusCanvas2D.tsx`) renders "
        "an interactive, hardware-accelerated 2D viewport. It performs world-to-screen coordinate transformations:"
    )
    add_p(doc, p_fe)
    add_equation(doc, "x_screen = x_world · S_scale + O_x,     y_screen = (H_site − y_world) · S_scale + O_y", "4.12")
    p_fe2 = (
        "ensuring the origin (0, 0) remains at the bottom-left corner of the campus parcel to match the Blender 3D coordinate system. "
        "The interface incorporates zone-based color coding (Academic = Blue, Residential = Yellow, Admin = Green, Sports = Coral, "
        "Parking = Slate Gray), entrance orientation indicators, and interactive metric comparison radar charts."
    )
    add_p(doc, p_fe2)

    # 4.8 Blender Integration
    add_h2(doc, "4.8 Procedural 3D Visualization Pipeline (Blender Integration)")
    p_bl = (
        "The Blender automation subsystem (`blender/generator.py`) consumes the Contract 9 Blueprint JSON exported by the backend "
        "(`GET /api/layouts/{id}/blueprint`). Operating headlessly via Blender's Python interface (`bpy`), the generator procedurally creates:\n"
        "1. Architectural Building Massing: Extrudes rectangular building footprints to specified heights (h_i = f_i · 3.5 m + 1.0 m), "
        "generates procedural horizontal floor plate divisions, applies procedural window array textures, and adds roof parapets.\n"
        "2. Circulation Network: Generates extruded asphalt roadways connecting entrances to building access portals.\n"
        "3. Environmental Elements: Instantiates marked surface parking stalls, procedurally scatters 3D low-poly tree canopies across green plots, "
        "and places perimeter entrance security portals.\n"
        "4. Lighting and Camera: Configures a physically-based Sun lamp, ambient sky environment, and an architectural camera framing the campus "
        "at an isometric overview perspective, rendering photorealistic `.png` images and saving `.blend` source project files."
    )
    add_p(doc, p_bl)

    # 4.9 Data Flow and Sequence
    add_h2(doc, "4.9 Data Flow and Sequence Diagrams")
    p_seq = (
        "The lifecycle of a generative layout execution run follows a deterministic sequence:\n"
        "1. Client triggers layout generation via `POST /api/projects/{projectId}/layout-runs` specifying candidate count (100) and algorithm (`GNN_NSGA2`).\n"
        "2. Backend fetches project requirements, building catalog, and constraints from PostgreSQL.\n"
        "3. ML Bridge checks `PIPELINE_MODE`. If `real`, dispatches data to Person 1's `ml.dataset.graph_builder.build_graph()`.\n"
        "4. Graph Builder emits Contract 5 `CampusGraph`.\n"
        "5. Person 2's `ml.inference.generate.generate_candidates()` ingests `CampusGraph`, draws latent noise, runs GNN forward pass, "
        "and emits 100 Contract 6 `CandidateLayout` objects.\n"
        "6. Person 3's `optimization.optimizer.optimize_layouts()` validates all 100 candidates across 8 constraints, computes 5 objectives, "
        "executes NSGA-II non-dominated sorting, and returns top-5 Contract 8 `RankedLayout` objects.\n"
        "7. Backend stores layout run and ranked layouts in PostgreSQL (`layout_runs`, `layouts` tables) and returns run status to client.\n"
        "8. Planner selects preferred layout via `POST /api/layouts/{layoutId}/select` and exports blueprint via `GET /api/layouts/{layoutId}/blueprint`.\n"
        "9. Blender headless generator consumes Blueprint JSON and outputs 3D `.blend` file and `.png` visualization render."
    )
    add_p(doc, p_seq)
    doc.add_page_break()


# ==============================================================================
# CHAPTER 5: SYSTEM IMPLEMENTATION
# ==============================================================================

def build_chapter_5(doc):
    add_h1(doc, "CHAPTER 5: SYSTEM IMPLEMENTATION")

    # 5.1 Development Environment
    add_h2(doc, "5.1 Development Environment and Pipeline Setup")
    p1 = (
        "ArchOpt was implemented using modern software engineering practices, type-safe programming paradigms, and strict data contracts. "
        "The project repository is structured into distinct, self-contained packages with zero circular dependencies:\n"
        "• `ml/`: Contains Graph Builder (`ml/dataset/`), GNN model definitions (`ml/models/`), model weights (`ml/models/weights/`), "
        "training scripts (`ml/training/`), and inference runners (`ml/inference/`).\n"
        "• `optimization/`: Contains the spatial constraint validation engine (`optimization/constraints/`), NSGA-II solver (`nsga2.py`), "
        "objective calculators (`objectives.py`), and visualization helpers (`visualize.py`).\n"
        "• `backend/`: Hosts the FastAPI application (`main.py`), REST routers (`api/`), SQLAlchemy database models (`models/`), "
        "Pydantic schemas (`schemas/`), and orchestration services (`services/ml_bridge.py`).\n"
        "• `frontend/`: Contains the React 18 TypeScript application, canvas components, and state management hooks.\n"
        "• `blender/`: Contains headless procedural generation scripts (`generator.py`) and validated sample blueprints.\n"
        "• `contracts/`: Houses shared Pydantic and TypeScript data contracts (Contracts 1 to 9)."
    )
    add_p(doc, p1)

    # 5.2 Graph Builder Implementation
    add_h2(doc, "5.2 Campus Graph Builder Implementation (`ml.dataset.graph_builder`)")
    p2 = (
        "The Graph Builder module (`ml/dataset/graph_builder.py`) implements `build_graph(campus_data: dict) -> CampusGraph`. "
        "It executes four deterministic operations:\n"
        "1. Strict Input Validation: Calls `validate_campus_data(campus_data)` to ensure positive site dimensions, valid building entities, "
        "positive floor counts, and non-empty building lists.\n"
        "2. Deterministic Node Expansion: Expands catalog entries according to `requiredCount` after sorting entities by ascending ID, "
        "guaranteeing identical node index assignments across runs.\n"
        "3. Node Feature Normalization: Maps building dimensions, height, floor count, type one-hot encodings, and zone one-hot encodings "
        "into a dense [N, 20] float array.\n"
        "4. Edge Construction: Establishes directed edges between node pairs: SAME_ZONE edges between buildings sharing a functional zone, "
        "functional type edges (e.g. Academic to Library NEAR with weight 0.9, Hostel to Sports NEAR with weight 0.6), and explicit user-defined "
        "MIN_DISTANCE and MAX_DISTANCE constraints. Edge indices and [E, 9] edge features are assembled and validated."
    )
    add_p(doc, p2)

    # 5.3 GNN Model Implementation
    add_h2(doc, "5.3 GNN Model & Inference Pipeline Implementation (`ml.models`, `ml.inference`)")
    p3 = (
        "The GNN module (`ml/models/campus_model.py`) unifies `GNNEncoder` and `LayoutDecoder` into a single deployable architecture (`CampusModel`). "
        "A critical engineering feature is the checkpoint storage mechanism: weights are stored in a plain NumPy zipped archive (`campus_model.npz`) "
        "keyed by PyTorch `state_dict` names. This dual-compatibility design allows the identical trained checkpoint to execute in PyTorch during "
        "model training and in pure NumPy during lightweight production inference without PyTorch installed."
    )
    add_p(doc, p3)

    gnn_code = (
        "# Source Excerpt: ml/models/campus_model.py (Dual Execution Forward Pass)\n"
        "def forward(params, graph, z_node, z_graph, config, backend='auto'):\n"
        "    if backend == 'numpy' or not TORCH_AVAILABLE:\n"
        "        return forward_numpy(params, graph, z_node, z_graph, config)\n"
        "    model = CampusModel.from_params(params, config).eval()\n"
        "    with torch.no_grad():\n"
        "        raw = model(torch.as_tensor(graph.node_inputs, dtype=torch.float32),\n"
        "                    torch.as_tensor(graph.edge_index, dtype=torch.long),\n"
        "                    torch.as_tensor(graph.edge_inputs, dtype=torch.float32),\n"
        "                    torch.as_tensor(z_node, dtype=torch.float32),\n"
        "                    torch.as_tensor(z_graph, dtype=torch.float32))\n"
        "    return raw.numpy().astype(np.float64)"
    )
    add_callout(doc, gnn_code, title="Listing 5.1: Dual-Backend GNN Forward Pass Execution")

    p4 = (
        "In `ml/inference/generate.py`, `generate_candidates()` draws random normal latent vectors z_node ∈ ℝ^(K × N × 16) "
        "and z_graph ∈ ℝ^(K × 16) scaled by temperature τ = 1.0. The forward pass computes raw logits, "
        "which are mapped through `sigmoid_numpy()`. Stochastic rotation selection determines cardinal rotation (0° or 90°), and `bounded_positions()` "
        "computes final metric (x, y) coordinates."
    )
    add_p(doc, p4)

    # 5.4 Constraint Engine Implementation
    add_h2(doc, "5.4 Spatial Constraint Engine Implementation (`optimization.constraints`)")
    p5 = (
        "The constraint validation subsystem (`optimization/validator.py`) delegates verification to 7 modular checker packages:\n"
        "1. `boundary.py`: Calculates building corner vertices (x, y), (x+w, y), (x+w, y+d), (x, y+d) rotated about the bottom-left vertex. "
        "Verifies that all 4 vertices satisfy 0 ≤ x ≤ W_site and 0 ≤ y ≤ H_site.\n"
        "2. `overlap.py`: Constructs 2D Shapely `Polygon` instances for each building. Evaluates pairwise polygon intersection (P_i ∩ P_j). "
        "Inflates footprints by g_min / 2 to evaluate minimum gap compliance simultaneously.\n"
        "3. `distance.py`: Evaluates center-to-center Euclidean distances between designated building pairs against MIN_DISTANCE and MAX_DISTANCE rules.\n"
        "4. `green.py`: Computes net unbuilt permeable area (A_green = A_site − ∑ A_built − A_road − A_park). "
        "Verifies that (A_green / A_site) · 100 ≥ γ_min.\n"
        "5. `parking.py`: Computes parking area ratio and verifies (A_parking / A_site) · 100 ≥ ρ_min.\n"
        "6. `roads.py`: Evaluates a circulation graph connecting building centers and entrances. Confirms every building has a valid path to an entrance.\n"
        "7. `zoning.py`: Calculates intra-zone building separation distances, verifying same-zone entities remain clustered within 0.45 · min(W_site, H_site)."
    )
    add_p(doc, p5)

    # 5.5 Multi-Objective Optimizer Implementation
    add_h2(doc, "5.5 Multi-Objective NSGA-II Optimizer Implementation (`optimization.optimizer`)")
    p6 = (
        "The optimization orchestrator (`optimization/optimizer.py`) implements `optimize_layouts()`. It validates all candidates, "
        "evaluates objective vectors via `objectives_to_minimise()`, executes Pymoo-accelerated non-dominated sorting (`rank_population()`), "
        "and assembles `RankedLayout` objects. The ranking logic (`ranking.py`) partitions the sorted population into feasible and infeasible "
        "pools. Feasible layouts populate top ranks; if fewer than K = 5 feasible layouts exist, the highest-scoring infeasible layouts fill "
        "the remaining positions."
    )
    add_p(doc, p6)

    # 5.6 FastAPI Backend Implementation
    add_h2(doc, "5.6 FastAPI REST Backend Implementation (`backend`)")
    p7 = (
        "The backend application is initialized in `backend/main.py` with CORS middleware and 6 modular routers:\n"
        "• `auth.py`: Implements user registration and JWT authentication using `passlib.context.CryptContext(schemes=['bcrypt'])` and `pyjwt`.\n"
        "• `projects.py`: CRUD operations for project lifecycle management.\n"
        "• `requirements.py`: Site boundary and environmental parameter validation.\n"
        "• `buildings.py`: Catalog management with strict Pydantic v2 schemas.\n"
        "• `constraints.py`: Spatial rule definition with operator verification.\n"
        "• `layouts.py`: Dispatches layout generation runs, retrieves ranked candidates, and exports Contract 9 blueprints."
    )
    add_p(doc, p7)

    # 5.7 React 2D Frontend Implementation
    add_h2(doc, "5.7 React 2D Campus Planning UI Implementation (`frontend`)")
    p8 = (
        "The frontend application is constructed with React 18, TypeScript, and Vite. The core interface comprises:\n"
        "• `RequirementsPage.tsx`: Interactive site dimensions, environmental ratios, and entrance coordinates configuration.\n"
        "• `BuildingsPage.tsx`: Building catalog configuration with real-time footprint dimension validation.\n"
        "• `CampusViewerPage.tsx`: Full-screen 2D canvas viewer rendering layout plans with zoom, pan, and layer toggle controls.\n"
        "• `PlanComparisonPage.tsx`: Side-by-side Pareto candidate comparison surfacing metrics tables and radar comparison charts."
    )
    add_p(doc, p8)

    # 5.8 Blender 3D Implementation
    add_h2(doc, "5.8 Blender 3D Procedural Campus Generation (`blender`)")
    p9 = (
        "The Blender script (`blender/generator.py`) runs in background headless mode (`blender -b -P blender/generator.py -- --input blueprint.json`). "
        "The procedural generator creates all geometry programmatically:\n"
        "• Site Parcel: Creates planar mesh with ground material.\n"
        "• Procedural Buildings: Instantiates mesh boxes extruded to storey heights, subdivides horizontal loops for floor plates, "
        "and assigns distinct Principled BSDF shader materials based on campus zone.\n"
        "• Roadways: Connects building entrance points to campus gates via extruded ribbon curves.\n"
        "• Trees & Environment: Randomly distributes procedural icosphere canopies with wood trunks across designated green zones.\n"
        "• Render Engine: Supports both EEVEE and Cycles rendering with automated camera framing."
    )
    add_p(doc, p9)

    # 5.9 Integration Contracts
    add_h2(doc, "5.9 Cross-Module Integration Contracts & Data Serialization")
    p10 = (
        "Inter-module communication is strictly governed by nine formal contracts defined in `contracts/layout.py` and `backend/schemas/`. "
        "Pydantic models utilize camelCase field aliasing (`by_alias=True`) to maintain seamless binary compatibility between Python backend "
        "services, TypeScript frontend interfaces, and Blender ingestion scripts."
    )
    add_p(doc, p10)

    # 5.10 Execution Modes
    add_h2(doc, "5.10 Pipeline Execution Modes: Mock Mode vs Real Mode")
    p11 = (
        "The backend `MLBridge` service (`backend/services/ml_bridge.py`) enforces strict pipeline gating via the `PIPELINE_MODE` environment variable:\n"
        "1. `PIPELINE_MODE=mock`: Employs deterministic contract-compliant candidate generation (`optimization.mock_data.generate_mock_candidates`). "
        "This mode enables isolated frontend and Blender feature development without requiring deep learning dependencies.\n"
        "2. `PIPELINE_MODE=real`: Dispatches execution dynamically to Person 1 (`ml.dataset.graph_builder`), Person 2 (`ml.inference.generate`), "
        "and Person 3 (`optimization.optimizer`).\n\n"
        "Under the Zero-Silent-Fallback Rule, if any upstream ML module is missing, raises an unhandled exception, or returns malformed data "
        "violating Contract 8, the backend raises an immediate `HTTP 422 Unprocessable Entity` error (`422 GENERATION_FAILED`). Silent fallback "
        "to mock data is strictly prohibited in real mode."
    )
    add_p(doc, p11)
    doc.add_page_break()


if __name__ == "__main__":
    print("[CHAPTERS 4-5 MODULE READY]")
