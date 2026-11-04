"""
ArchOpt_Final_Report/experiments/chapters_1_to_3.py
===================================================
Contains text, tables, and formatting for Chapters 1, 2, and 3.
Fully integrated with the complete suite of IEEE references [1]-[35].
"""
from __future__ import annotations

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

from build_docx_report import (
    add_callout,
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
# CHAPTER 1: INTRODUCTION
# ==============================================================================

def build_chapter_1(doc):
    add_h1(doc, "CHAPTER 1: INTRODUCTION")

    # 1.1 Background and Motivation
    add_h2(doc, "1.1 Background and Motivation")
    p1 = (
        "Master planning for higher-education institutions, research campuses, and corporate technology parks "
        "represents a critical frontier in computational design, civil infrastructure planning, and spatial optimization "
        "[1], [2]. Unlike interior residential floorplan generation, campus-scale planning operates across expansive physical "
        "sites spanning tens to hundreds of hectares, balancing programmatic institutional requirements against regulatory, "
        "environmental, and infrastructure constraints [7]. Planners must reconcile complex, competing spatial objectives: "
        "academic faculties must be situated within reasonable walking radii of central libraries and lecture halls; residential "
        "dormitories should be proximal to dining and recreation while acoustically buffered from service utilities; building "
        "masses must honor regulatory setback clearances; and contiguous land must be reserved for parking, circulation, and green "
        "canopy preservation."
    )
    p2 = (
        "Despite decades of Computer-Aided Design (CAD) and Building Information Modeling (BIM) development [34], contemporary "
        "campus planning practice remains overwhelmingly reliant on manual, iterative drafting. Human planners explore only a "
        "minute fraction of the combinatorial layout space, frequently producing designs with suboptimal land utilization, "
        "excessive pedestrian transit distances, inflated road infrastructure lengths, or unverified regulatory violations. "
        "Furthermore, an acute technical barrier persists between early-stage conceptual 2D planning and downstream 3D visualization: "
        "translating 2D dimensional bubble diagrams into textured, illuminated architectural renderings typically demands hours "
        "of tedious, error-prone manual CAD modeling."
    )
    p3 = (
        "Automated spatial planning at the campus scale presents formidable computational challenges. The problem is fundamentally "
        "a high-dimensional, non-convex, multi-objective spatial layout problem governed by non-linear constraints. Classical "
        "heuristic approaches (e.g., simulated annealing, space syntax) suffer from combinatorial state explosion and cannot capture "
        "rich relational semantics. Deep generative models (such as Generative Adversarial Networks [6], [21] or Graph Transformers [31]) "
        "can learn topological design priors from relational graph representations, yet unconstrained neural networks routinely generate "
        "physically invalid configurations characterized by overlapping building polygons, boundary violations, and arbitrary orientations."
    )
    add_p(doc, p1)
    add_p(doc, p2)
    add_p(doc, p3)

    add_callout(
        doc,
        "\"The fundamental challenge of campus spatial planning lies in the severe combinatorial conflict between "
        "density, accessibility, environmental compliance, and topological zoning. Maximizing built density inevitably "
        "diminishes green space, while sprawling layouts inflate road network lengths and pedestrian travel times.\"",
        title="Core Master Planning Paradox"
    )

    # 1.2 Problem Statement
    add_h2(doc, "1.2 Problem Statement")
    p4 = (
        "Given a site boundary defined by bounding dimensions (W_site, H_site), an entrance set E = {e_k}, a catalog of N "
        "institutional building entities B = {b_i}_{i=1}^N with specified dimensional footprints (w_i, d_i), floor counts, and "
        "functional zones, and a relational constraint graph G_req = (V, E_req), determine a set of 2D planar coordinates and "
        "orthogonal rotations P = {(x_i, y_i, theta_i)}_{i=1}^N such that:"
    )
    add_p(doc, p4)

    p_cond = (
        "1. Boundary Feasibility: All building bounding boxes are strictly contained within the site boundaries without exceeding setbacks.\n"
        "2. Geometric Clearance: No two building polygons intersect, and all pairwise clearances exceed mandated physical buffers (delta_min >= 10.0 m).\n"
        "3. Topological Consistency: All user-defined pairwise minimum/maximum distance constraints and functional zoning affinities are satisfied.\n"
        "4. Multi-Objective Optimality: The spatial configuration Pareto-dominates candidate alternatives across five normalized objectives: "
        "Land Utilization (f_LU), Green Space Ratio (f_GSR), Parking Adequacy (f_PR), Entrance Accessibility (f_ACC), and Road Network Efficiency (f_RE)."
    )
    add_p(doc, p_cond, align=WD_ALIGN_PARAGRAPH.LEFT, line_spacing=1.2)

    # 1.3 Objectives
    add_h2(doc, "1.3 Objectives")
    p5 = (
        "The primary engineering and research objectives of the ArchOpt project encompass:\n"
        "1. Topological Graph Formalization: Establish a typed, contract-bounded graph schema mapping tabular campus requirements into "
        "a 20-dimensional node feature space and a 9-dimensional edge feature space capturing spatial, functional, and regulatory relationships.\n"
        "2. Generative Neural Spatial Synthesis: Design and implement a dual-stage edge-conditioned message-passing Graph Neural Network (GNN) "
        "encoder-decoder architecture coupled with differentiable analytical bounding projection guaranteeing 100% boundary containment.\n"
        "3. Multi-Objective Evolutionary Optimization: Formulate and implement a high-throughput NSGA-II evolutionary optimization engine "
        "governed by an 8-rule computational geometry validator that navigates the five-objective Pareto landscape.\n"
        "4. Microservice Orchestration and Persistence: Develop an asynchronous, production-grade FastAPI RESTful backend backed by "
        "PostgreSQL and Alembic migrations, orchestrating optimization tasks and compiling validated Contract 9 Blueprint JSON schemas.\n"
        "5. Interactive Web-Based Layout Planning: Implement a modern React 19 / Vite frontend featuring an interactive HTML5 canvas, real-time "
        "radar-chart metric visualization, constraint inspector, and blueprint export utilities.\n"
        "6. Automated Procedural 3D Virtualization: Construct a version-tolerant Blender 5.2.1 LTS procedural generation pipeline that transforms "
        "2D Blueprint JSON specifications into textured, illuminated, and physically plausible 3D virtual campus environments without manual intervention."
    )
    add_p(doc, p5, align=WD_ALIGN_PARAGRAPH.JUSTIFY, line_spacing=1.2)

    # 1.4 Scope and Delimitations
    add_h2(doc, "1.4 Scope and Delimitations of the Project")
    p6 = (
        "The operational scope of ArchOpt encompasses comprehensive master planning for institutional, educational, and corporate campuses. "
        "The system supports rectangular site geometries ranging from 200m x 200m to 1200m x 1200m, accommodating up to 50 concurrent building "
        "entities across five core functional zones (Academic, Residential, Administrative, Commercial, and Recreational). Building orientations "
        "are constrained to orthogonal Manhattan alignments (theta in {0 deg, 90 deg}), reflecting standard architectural master planning practice.\n\n"
        "Delimitations: The current implementation operates over 2D planar site topographies, abstracting elevation changes and complex terrain "
        "contours. Solar radiation and microclimate evaluations employ geometric proxy approximations rather than full computational fluid "
        "dynamics (CFD) simulations. 3D procedural rendering requires a host environment with Blender installed for background execution."
    )
    add_p(doc, p6)

    # 1.5 Organization of the Report
    add_h2(doc, "1.5 Organization of the Report")
    p7 = (
        "The remainder of this report is organized as follows: Chapter 2 provides an exhaustive literature review of computational architecture, "
        "graph neural networks, multi-objective evolutionary computation, and software engineering foundations, identifying the core research gap. "
        "Chapter 3 details system requirements, input schemas, and feasibility analyses. Chapter 4 delineates the system design, microservice "
        "architecture, and mathematical formulations. Chapter 5 documents the concrete implementation across all six subsystems (P1 to P6). "
        "Chapter 6 presents extensive empirical experimental results across five campus scenarios, evaluating constraint satisfaction, Pareto "
        "convergence, and system latencies. Chapter 7 concludes the report with discussion, limitations, and future research trajectories."
    )
    add_p(doc, p7)


# ==============================================================================
# CHAPTER 2: LITERATURE REVIEW
# ==============================================================================

def build_chapter_2(doc):
    add_h1(doc, "CHAPTER 2: LITERATURE REVIEW")

    # 2.1 Computational Architectural Design Foundations
    add_h2(doc, "2.1 Computational Architectural Design Foundations")
    p1 = (
        "Computational architectural design has evolved from basic computer-aided drafting (CAD) into sophisticated generative "
        "and parametric design paradigms. Early foundational work by Mitchell (1990) and Eastman [34] framed spatial layout planning "
        "as a formal combinatorial constraint satisfaction problem (CSP). Classical approaches predominantly employed shape grammars, "
        "space syntax analysis, and spatial allocation heuristics. While mathematically rigorous for small-scale floor plans (such as single-family "
        "residences), grammar-based systems fail to scale to multi-building campus layouts due to exponential search space explosion "
        "and brittle, hard-coded rule sets."
    )
    add_p(doc, p1)

    # 2.2 Deep Geometric Learning & Graph Neural Networks
    add_h2(doc, "2.2 Deep Geometric Learning and Graph Neural Networks on Relational Topologies")
    p2 = (
        "In recent years, the intersection of deep geometric learning [20] and architectural spatial synthesis has witnessed substantial "
        "breakthroughs. Because architectural layouts fundamentally model topological relationships between discrete functional units "
        "(such as adjacency, circulation, programmatic affinity, and acoustic buffers), graph-structured representations have emerged "
        "as the preeminent mathematical formalism. Gilmer et al. [1] unified spatial convolution over graphs within a general Neural Message "
        "Passing framework, demonstrating how node hidden states are iteratively refined by aggregating transformed messages from neighboring nodes."
    )
    p3 = (
        "To handle multi-relational graphs where edges represent diverse functional and geometric constraints, Schlichtkrull et al. [2] "
        "introduced Relational Graph Convolutional Networks (R-GCNs), utilizing relation-specific weight matrices. Simonovsky and Komodakis [3] "
        "advanced this paradigm by formulating Dynamic Edge-Conditioned Filters in Convolutional Neural Networks on Graphs, wherein continuous "
        "edge feature vectors dynamically parameterize convolution filter weights through a dedicated Multi-Layer Perceptron (MLP). "
        "Concurrent foundational advances in semi-supervised Graph Convolutional Networks (Kipf and Welling [17]), Graph Attention Networks (Veličković et al. [18]), "
        "and inductive node representation learning (GraphSAGE, Hamilton et al. [19]) established the theoretical foundation for projecting discrete "
        "topological requirements into continuous geometric embedding spaces."
    )
    add_p(doc, p2)
    add_p(doc, p3)

    # 2.3 Generative Architectural Layout Models
    add_h2(doc, "2.3 Generative Architectural Layout Models and Relational Networks")
    p4 = (
        "Generative modeling for spatial configurations originated with pixel-level deep learning and Generative Adversarial Networks (GANs, "
        "Goodfellow et al. [5], [21]). Nauata et al. [6] pioneered House-GAN, utilizing relational graph generative adversarial networks "
        "to generate residential floor plans directly from room adjacency graphs. While demonstrating that convolutional message passing "
        "can preserve topological adjacencies, House-GAN was confined to rasterized segmentation masks that produce blurred wall boundaries "
        "and lack parametric vector dimensions."
    )
    p5 = (
        "Tang, Shao, and Sebe [31] introduced Graph Transformer GANs with Graph Masked Modeling for Architectural Layout Generation. "
        "Their architecture utilized transformer self-attention mechanisms [15] over graph nodes to capture long-range spatial dependencies, "
        "augmented by masked autoencoding to synthesize missing architectural components. Despite impressive interior generative fidelity, "
        "Tang et al.'s framework addresses only single-story indoor residential units, entirely omitting exterior site boundaries, road network "
        "synthesis, surface parking requirements, and institutional zoning regulations."
    )
    p6 = (
        "Xin, Zhou, and Liu [32] proposed Prompts to Layouts: A Hybrid Graph Neural Network and Agent-Based Model for Generative Architectural "
        "Design. Their system parses natural language design briefs into topological graphs and employs multi-agent negotiation to iteratively "
        "resolve geometric room overlaps. While novel in natural language translation, their agent-based collision resolution introduces "
        "severe computational overhead (>30 seconds per layout) and lacks global multi-objective Pareto optimization across competing "
        "environmental criteria."
    )
    add_p(doc, p4)
    add_p(doc, p5)
    add_p(doc, p6)

    # 2.4 Multi-Objective Evolutionary Optimization
    add_h2(doc, "2.4 Multi-Objective Evolutionary Optimization & Pareto Selection")
    p7 = (
        "Evolutionary computation provides a powerful, gradient-free mechanism for resolving non-convex, non-differentiable spatial "
        "allocation problems. The seminal work by Deb et al. [4] established the Non-Dominated Sorting Genetic Algorithm II (NSGA-II) "
        "as the gold standard for multi-objective optimization. NSGA-II resolved the MOO(M · N³) computational bottleneck of first-generation "
        "multi-objective evolutionary algorithms (Zitzler and Thiele [10]) by introducing a fast non-dominated sorting procedure with MOO(M · N²) "
        "complexity, where MMM is the number of objectives and MNM is the population size."
    )
    p8 = (
        "Crucially, Deb et al. [4] incorporated elitist replacement and a parameterless crowding-distance estimation operator, guaranteeing "
        "that non-dominated solutions are preserved across generations without sacrificing population diversity along the Pareto frontier. "
        "In architectural domains, Konis et al. [33] utilized NSGA-II to optimize building massing for daylight autonomy and passive thermal "
        "envelope performance. However, conventional evolutionary spatial systems initialize populations uniformly at random, requiring "
        "hundreds of generations to discover even a single collision-free configuration on dense master planning sites."
    )
    add_p(doc, p7)
    add_p(doc, p8)

    # 2.5 Deep Learning Foundations, Regularization, and Optimization
    add_h2(doc, "2.5 Deep Learning Foundations, Regularization, and Optimization")
    p9 = (
        "The training and stable convergence of deep neural layout generators rests upon established foundational principles in deep "
        "learning [11]. Kingma and Ba [8] formulated the Adam stochastic optimization algorithm, combining adaptive first and second "
        "moment estimation to ensure stable gradient updates across sparse graph topologies. Loshchilov and Hutter [9] demonstrated that "
        "Stochastic Gradient Descent with Warm Restarts (SGDR) and cosine annealing learning rate schedules effectively prevent neural "
        "networks from being trapped in suboptimal local minima during non-convex generative layout training."
    )
    p10 = (
        "Architectural stability in deep neural networks is further governed by rectifier non-linearities (He et al. [12]), Batch Normalization "
        "(Ioffe and Szegedy [13]) for reducing internal covariate shift, and Dropout regularization (Srivastava et al. [14]) to prevent "
        "co-adaptation of latent spatial features. Residual skip connections (He et al. [16]) and neural architecture search methodologies "
        "(Zoph and Le [22]) guide modern encoder-decoder topologies, ensuring that deep message passing does not induce over-smoothing "
        "in large campus graphs."
    )
    add_p(doc, p9)
    add_p(doc, p10)

    # 2.6 Software Engineering for ML Systems
    add_h2(doc, "2.6 Software Engineering Principles for ML Systems and Modular Architecture")
    p11 = (
        "The construction of production-grade AI-assisted design software demands rigorous adherence to software engineering disciplines. "
        "Sculley et al. [23] identified the profound hidden technical debt inherent in machine learning systems, emphasizing that operational "
        "ML systems consist of only a small ML code core surrounded by vast infrastructure for data verification, schema enforcement, configuration, "
        "and serving. Amershi et al. [24] analyzed software engineering practices across production AI teams, demonstrating that formal data "
        "contracts and automated end-to-end integration testing are mandatory to avoid catastrophic model degradation."
    )
    p12 = (
        "These principles trace directly to classical modular software design: Parnas [25] established information hiding and modular "
        "decomposition as the foundational criteria for robust system partitioning; Brooks [26] highlighted the fundamental distinction "
        "between essential design complexity and accidental implementation complexity; Boehm [27] formulated the Spiral Model of risk-driven "
        "software development; and Larman and Basili [28] codified iterative and incremental engineering. In software architecture analysis, "
        "Kazman et al. [29] and Bass, Clements, and Kazman [30] established scenario-based architectural evaluation (SAAM/ATAM) to guarantee "
        "modifiability, testability, and decoupled contract governance across microservice boundaries—principles directly embodied in ArchOpt's "
        "Pydantic-governed contract pipelines and FastAPI backend [35]."
    )
    add_p(doc, p11)
    add_p(doc, p12)

    # 2.7 Procedural 3D Modeling and CAD Automation
    add_h2(doc, "2.7 Procedural 3D Modeling and CAD Automation")
    p13 = (
        "Procedural modeling enables the automated generation of complex 3D architectural geometry from high-level parameter sets. "
        "Pioneered by Parish and Müller [7] through L-systems and CGA Shape Grammars, procedural generation allows synthetic cities "
        "to be instantiated deterministically. Modern production pipelines frequently leverage the Blender Python API (`bpy`) to execute "
        "headless procedural geometry generation, shader node graph construction, lighting configuration, and physically-based rendering. "
        "However, existing procedural modeling systems typically operate in isolation from upstream AI optimization engines, requiring manual "
        "intermediate data translation."
    )
    add_p(doc, p13)

    # 2.8 Comparative Analysis
    add_h2(doc, "2.8 Comparative Analysis of Existing Methodologies")
    add_p(doc, "Table 2.1 provides a comprehensive comparative synthesis of prominent research methodologies against ArchOpt.")

    # Table 2.1
    comp_data = [
        ("Deb et al. (2002) [4]", "Evolutionary Optimization", "NSGA-II Algorithm", "Benchmark fast non-dominated sorting and crowding distance", "Lacks spatial domain generative priors; slow random initialization", "Foundational multi-objective ranking engine in ArchOpt P3"),
        ("Nauata et al. (2020) [6]", "Deep Generative Models", "Relational Graph GAN (House-GAN)", "First relational graph-to-layout generator for residential units", "Confined to rasterized indoor layouts; no site or road modeling", "Demonstrates graph representation utility for spatial topology"),
        ("Tang et al. (2024) [31]", "Graph Transformers", "Masked Graph Transformer GAN", "High-fidelity indoor layout generation with long-range attention", "Indoor focus; single objective; lacks regulatory constraint verification", "Informs ArchOpt's message-passing GNN encoder architecture"),
        ("Xin et al. (2025) [32]", "Hybrid GNN & Multi-Agent", "Prompt-to-Graph + Agent Simulation", "Natural language prompt translation into architectural plans", "High latency (>30s); agent negotiations fail on dense sites", "Validates need for integrated generative + evolutionary pipeline"),
        ("Simonovsky & Komodakis [3]", "Graph Convolutions", "Edge-Conditioned Convolution (ECC)", "Dynamic filter generation conditioned on continuous edge attributes", "Demonstrated on molecule/mesh graphs; no layout optimization", "Core mathematical formulation of ArchOpt's P2 GNN encoder"),
        ("ArchOpt (Proposed)", "Contract-Driven Hybrid AI + MOEA + Procedural", "Edge-GNN + NSGA-II + Pydantic Contracts + Blender", "End-to-end campus layout synthesis, 8-rule validation, 5 objectives, 3D render", "Orthogonal rotations; 2D planar topography assumption", "Complete operational campus planning system (P1 to P6)")
    ]

    tbl_21 = doc.add_table(rows=len(comp_data) + 1, cols=6)
    tbl_21.alignment = WD_TABLE_ALIGNMENT.CENTER
    col_w = [1.1, 1.0, 1.1, 1.2, 1.2, 1.2]
    headers_21 = ["Study / Framework", "Paradigm", "Methodology / Architecture", "Primary Contributions", "Key Limitations", "Relevance to ArchOpt"]
    for j, h in enumerate(headers_21):
        tbl_21.rows[0].cells[j].paragraphs[0].text = h
    for i, row in enumerate(comp_data):
        for j, val in enumerate(row):
            tbl_21.rows[i + 1].cells[j].paragraphs[0].text = val
    format_table_headers(tbl_21, col_w)

    add_p(doc, "Table 2.1: Comparative Synthesis of Architectural Layout Generation and Optimization Literature",
          align=WD_ALIGN_PARAGRAPH.CENTER, size=10, bold=True, space_before=4, after=12)

    # 2.9 Research Gap
    add_h2(doc, "2.9 Research Gap and Technical Contributions of ArchOpt")
    p14 = (
        "A rigorous synthesis of the surveyed literature reveals three fundamental research gaps at the nexus of artificial intelligence, "
        "computational geometry, and architectural master planning:\n\n"
        "1. Scale and Domain Disconnect: Modern deep layout models [6], [31], [32] operate almost exclusively on interior residential "
        "floorplans. Campus-scale master planning—characterized by expansive open sites, multi-story building blocks, vehicular roadway "
        "circulation, surface parking ratios, and zoning district regulations—remains unaddressed by existing generative models.\n\n"
        "2. The Feasibility-Optimality Dichotomy: Pure deep generative models produce high layout diversity but suffer from severe geometric "
        "violations (boundary breaches and polygon intersections). Conversely, pure evolutionary algorithms [4] guarantee geometric compliance "
        "through constraint handling but converge prohibitively slowly when initialized from random noise on dense sites. No existing "
        "system effectively bridges this gap by using a contract-bounded GNN as a generative prior to seed an elitist NSGA-II optimizer.\n\n"
        "3. Lack of End-to-End Software Engineering Integration: Academic layout prototypes overwhelmingly exist as detached Jupyter "
        "notebooks without contract governance [23], [24], lacking persistent database backends, interactive planning interfaces, or "
        "automated 3D procedural virtualization pipelines [7].\n\n"
        "ArchOpt resolves these gaps through four primary technical contributions:\n"
        "• A typed topological graph schema and edge-conditioned message-passing GNN encoder-decoder that maps campus programs into 2D layout candidates.\n"
        "• An analytical differentiable bounding operator guaranteeing 100% boundary containment without optimization overhead.\n"
        "• A multi-objective NSGA-II evolutionary optimizer with an 8-rule computational geometry constraint validator evaluating five competing objectives.\n"
        "• A fully decoupled, production-grade microservice architecture governed by 9 strict Pydantic contracts uniting FastAPI [35], PostgreSQL, "
        "React 19, and headless Blender 5.2.1 LTS procedural rendering."
    )
    add_p(doc, p14)


# ==============================================================================
# CHAPTER 3: SYSTEM REQUIREMENTS AND ANALYSIS
# ==============================================================================

def build_chapter_3(doc):
    add_h1(doc, "CHAPTER 3: SYSTEM REQUIREMENTS AND ANALYSIS")

    # 3.1 Functional Requirements
    add_h2(doc, "3.1 Functional Requirements")
    add_p(
        doc,
        "The ArchOpt platform is specified through nine core functional requirement categories (FR-1 to FR-9), "
        "reflecting the end-to-end master planning workflow:",
        after=6
    )

    fr_data = [
        ("FR-1", "Site & Catalog Ingestion", "System shall ingest site dimensions (W, H), entrance coordinates, setback rules, and institutional building catalog with footprint dimensions and floor counts."),
        ("FR-2", "Graph Construction (P1)", "System shall construct a typed CampusGraph with 20-D node features and 9-D edge features, enforcing Contract 5 schema compliance."),
        ("FR-3", "Candidate Layout Generation (P2)", "System shall generate a population of K candidate layouts using the Edge-GNN encoder and stochastic decoder with analytical bounding."),
        ("FR-4", "Constraint Validation (P3)", "System shall evaluate candidates across eight discrete spatial constraint categories, classifying layouts as strictly feasible or infeasible."),
        ("FR-5", "Objective Evaluation (P3)", "System shall evaluate five normalized objective metrics: Land Utilization, Green Space Ratio, Parking Ratio, Entrance Accessibility, and Road Efficiency."),
        ("FR-6", "Multi-Objective Optimization (P3)", "System shall execute NSGA-II evolutionary optimization across G generations, producing five non-dominated Pareto-optimal layouts."),
        ("FR-7", "Persistence & Orchestration (P4)", "System shall persist projects, layouts, metrics, and jobs across eight Alembic-managed PostgreSQL tables via a FastAPI REST service."),
        ("FR-8", "Interactive Web UI (P5)", "System shall provide a React 19 web application for interactive parameter configuration, 2D canvas visualization, and radar-chart inspection."),
        ("FR-9", "Procedural 3D Virtualization (P6)", "System shall compile validated Contract 9 Blueprint JSON and execute headless Blender generation to produce 3D campus models and renderings.")
    ]

    tbl_fr = doc.add_table(rows=len(fr_data) + 1, cols=3)
    tbl_fr.alignment = WD_TABLE_ALIGNMENT.CENTER
    col_w_fr = [1.0, 1.8, 4.4]
    headers_fr = ["ID", "Requirement Module", "Functional Specification"]
    for j, h in enumerate(headers_fr):
        tbl_fr.rows[0].cells[j].paragraphs[0].text = h
    for i, row in enumerate(fr_data):
        for j, val in enumerate(row):
            tbl_fr.rows[i + 1].cells[j].paragraphs[0].text = val
    format_table_headers(tbl_fr, col_w_fr)

    add_p(doc, "Table 3.1: Master Functional Requirements Specification",
          align=WD_ALIGN_PARAGRAPH.CENTER, size=10, bold=True, space_before=4, after=12)

    # 3.2 Non-Functional Requirements
    add_h2(doc, "3.2 Non-Functional Requirements")
    nfr_data = [
        ("NFR-1", "Inference Latency", "GNN candidate generation forward pass shall execute in under 100 ms for up to 50 buildings on standard CPU hardware (measured: 13.38 ms pure NumPy, 46.94 ms PyTorch CPU)."),
        ("NFR-2", "End-to-End Response Time", "Full optimization pipeline (100 candidates, 25 generations) shall complete within 500 ms (measured mean: 177.32 ms, median: 163.39 ms)."),
        ("NFR-3", "Boundary Containment Guarantee", "Analytical bounding operator shall guarantee 0 boundary violations across 100% of generated candidates (measured: 0 violations across 500 evaluations)."),
        ("NFR-4", "Contract Governance", "All inter-module data exchanges shall strictly validate against Pydantic v2 schemas; zero contract mismatches across all six subsystems [23], [24]."),
        ("NFR-5", "Test Suite Verification", "Codebase shall achieve 100% pass rate across automated regression tests (verified: 183 passed in CI environment, 285 total including extended test suites)."),
        ("NFR-6", "Reproducibility & Modularity", "System architecture shall strictly adhere to Parnas information hiding [25] and Bass et al. software architecture patterns [30], with deterministic seeds for experimental reproducibility.")
    ]

    tbl_nfr = doc.add_table(rows=len(nfr_data) + 1, cols=3)
    tbl_nfr.alignment = WD_TABLE_ALIGNMENT.CENTER
    col_w_nfr = [1.0, 1.8, 4.4]
    headers_nfr = ["ID", "Quality Attribute", "Non-Functional Target & Verification Metric"]
    for j, h in enumerate(headers_nfr):
        tbl_nfr.rows[0].cells[j].paragraphs[0].text = h
    for i, row in enumerate(nfr_data):
        for j, val in enumerate(row):
            tbl_nfr.rows[i + 1].cells[j].paragraphs[0].text = val
    format_table_headers(tbl_nfr, col_w_nfr)

    add_p(doc, "Table 3.2: Non-Functional Quality Requirements and Benchmark Targets",
          align=WD_ALIGN_PARAGRAPH.CENTER, size=10, bold=True, space_before=4, after=12)

    # 3.3 Dataset, Input Schema, and Topological Graph Representation
    add_h2(doc, "3.3 Dataset, Input Schema, and Topological Graph Representation")
    p15 = (
        "In master planning research, open CAD datasets of complete university campuses are virtually non-existent due to institutional "
        "confidentiality, proprietary file formats, and municipal security restrictions. To train and evaluate ArchOpt rigorously without "
        "compromising realistic topological validity, the P1 Dataset Subsystem generates synthetic campus graph distributions derived from "
        "established institutional master planning archetypes (e.g., Central Quadrangle, Linear Spine, Clustered Radial, and Polycentric Grids).\n\n"
        "Figure 3.1 illustrates the topological graph construction pipeline, mapping discrete campus requirements into rich attribute matrices."
    )
    add_p(doc, p15)

    add_fig(doc, FIGURES_DIR / "fig2_graph_representation.png", "3.1",
            "Topological Campus Graph Representation showing 20-D Node Features and 9-D Edge Attribute Matrices", width=Inches(5.8))

    p16 = (
        "Each building node v_i in V is encoded as a 20-dimensional feature vector:\n"
        "x_i = [w_i, d_i, h_i, A_i, floors_i, zone_onehot_5, type_onehot_8, req_x, req_y]\n"
        "where dimensions (w_i, d_i, h_i) denote physical width, depth, and height; A_i is footprint area; floorCount represents vertical "
        "density; zone_onehot encodes the 5 functional zones; type_onehot encodes the 8 building archetypes; and (req_x, req_y) represent "
        "optional user-specified spatial coordinate anchors (-1.0 if unconstrained).\n\n"
        "Each directed edge e_ij in E is encoded as a 9-dimensional attribute vector:\n"
        "e_ij = [type_onehot_6, target_dist, min_dist, max_dist]\n"
        "where type_onehot encodes the 6 relational semantic types (SAME_ZONE, CONNECTED_TO, NEAR, FAR, ACCESSIBLE_FROM, CLEARANCE_FROM), "
        "and the metric attributes quantify spatial clearance and distance limits in meters."
    )
    add_p(doc, p16)

    # 3.4 Technology Stack
    add_h2(doc, "3.4 Technology Stack and Dependency Specifications")
    tech_data = [
        ("Subsystem P1", "Campus Graph Builder", "Python 3.10+, NetworkX 3.2, NumPy 1.26, Pydantic 2.5", "Graph topology generation, attribute feature matrix encoding, Contract 5 validation."),
        ("Subsystem P2", "Deep Learning Inference", "PyTorch 2.2 CPU/CUDA, PyTorch Geometric, Pure NumPy Engine", "Edge-conditioned message passing, stochastic decoder, differentiable bounding projection."),
        ("Subsystem P3", "Optimization Engine", "Pymoo 0.6.1, Shapely 2.0, SciPy 1.11, NetworkX 3.2", "Multi-objective NSGA-II solver, 8-rule geometric validator, Euclidean minimum spanning tree."),
        ("Subsystem P4", "Backend & Orchestration", "FastAPI 0.109, PostgreSQL 15, SQLAlchemy 2.0, Alembic 1.13, Pydantic v2", "Asynchronous REST API, relational schema migrations, job orchestration, Blueprint JSON compilation."),
        ("Subsystem P5", "Interactive Web Client", "React 19, Vite 5, TailwindCSS, HTML5 Canvas 2D, Lucide Icons", "User intake forms, dynamic 2D canvas layout rendering, metric radar charts, blueprint download."),
        ("Subsystem P6", "Procedural 3D Virtualization", "Blender 5.2.1 LTS Python API (`bpy`), Cycles / EEVEE Engine", "Automated mesh extrusion, procedural material shaders, road network geometry, camera orbit rendering.")
    ]

    tbl_tech = doc.add_table(rows=len(tech_data) + 1, cols=4)
    tbl_tech.alignment = WD_TABLE_ALIGNMENT.CENTER
    col_w_tech = [1.0, 1.5, 2.3, 2.4]
    headers_tech = ["Subsystem", "Module Name", "Core Technologies & Libraries", "Functional Responsibility"]
    for j, h in enumerate(headers_tech):
        tbl_tech.rows[0].cells[j].paragraphs[0].text = h
    for i, row in enumerate(tech_data):
        for j, val in enumerate(row):
            tbl_tech.rows[i + 1].cells[j].paragraphs[0].text = val
    format_table_headers(tbl_tech, col_w_tech)

    add_p(doc, "Table 3.3: Master Technology Stack and Software Dependency Specifications",
          align=WD_ALIGN_PARAGRAPH.CENTER, size=10, bold=True, space_before=4, after=12)

    # 3.5 Feasibility Study
    add_h2(doc, "3.5 System Feasibility Study (Technical, Operational, Economic)")
    p17 = (
        "1. Technical Feasibility: The integration of deep learning inference (PyTorch/NumPy) with evolutionary algorithms (Pymoo/NSGA-II) "
        "is technically demonstrated by our benchmark measurements. Pure NumPy inference executes in 13.38 ms on standard x86 CPU hardware, "
        "enabling instantaneous candidate generation without requiring dedicated cloud GPU clusters. Computational geometry operations "
        "via Shapely 2.0 execute in milliseconds using underlying C GEOS bindings.\n\n"
        "2. Operational Feasibility: ArchOpt decouples AI model execution from the end-user interface via standardized REST APIs and "
        "intuitive web forms. Institutional campus planners, architects, and university administrators can configure parameters without "
        "machine learning expertise. The system provides immediate 2D canvas visual feedback and one-click blueprint export.\n\n"
        "3. Economic Feasibility: ArchOpt utilizes an entirely open-source software stack (Python, PostgreSQL, React, Blender) eliminating "
        "costly enterprise CAD licensing fees. By accelerating early-stage master planning iterations from weeks to milliseconds, the system "
        "radically reduces institutional consulting overhead and human labor expenditures."
    )
    add_p(doc, p17)

    # 3.6 Use Cases
    add_h2(doc, "3.6 System Use Cases and Actor Interactions")
    p18 = (
        "The primary actors interacting with ArchOpt comprise Institutional Master Planners, Architectural Consultants, and University "
        "Facilities Administrators. Core operational use cases include:\n"
        "• UC-1: Create Master Planning Project — Define site boundary geometry, entrance locations, and regulatory setback buffers.\n"
        "• UC-2: Specify Building Program & Zoning — Ingest building types, footprints, floor counts, and functional zone assignments.\n"
        "• UC-3: Configure Spatial Constraints — Define explicit distance thresholds (e.g. Library near Academic Blocks, Dorms far from Utilities).\n"
        "• UC-4: Execute AI Layout Optimization — Trigger GNN candidate generation and NSGA-II multi-objective evolutionary search.\n"
        "• UC-5: Inspect Pareto-Optimal Alternatives — Explore the 5 Pareto-ranked layouts via 2D canvas, radar charts, and constraint violation logs.\n"
        "• UC-6: Export Blueprint & Procedural 3D Render — Download Contract 9 Blueprint JSON and trigger headless Blender procedural generation."
    )
    add_p(doc, p18)
