"""
ArchOpt_Final_Report/experiments/generate_architecture_plots.py
==============================================================
Generates architectural and workflow figures:
- Figure 2: Campus Graph Representation (Contract 5)
- Figure 3: GNN Architecture (Encoder-Decoder)
- Figure 4: NSGA-II Multi-Objective Optimization Workflow
- Figure 12: Database Entity-Relationship (ER) Diagram (8 Tables)
"""
from __future__ import annotations

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np

FIGURES_DIR = Path("E:/ArchOpt/ArchOpt_Final_Report/figures").resolve()
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.size": 11,
    "font.family": "serif",
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "figure.titlesize": 14,
    "savefig.dpi": 300,
})


def plot_graph_representation():
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Nodes (Buildings)
    nodes = [
        ("Acad A\n(id=1)", 20, 70, "#90CAF9"),
        ("Acad B\n(id=2)", 50, 75, "#90CAF9"),
        ("Library\n(id=3)", 35, 45, "#80DEEA"),
        ("Admin\n(id=4)", 75, 55, "#C5E1A5"),
        ("Hostel A\n(id=5)", 20, 20, "#FFE082"),
        ("Hostel B\n(id=6)", 50, 20, "#FFE082"),
        ("Sports\n(id=8)", 80, 25, "#FFAB91"),
        ("Parking\n(id=9)", 85, 80, "#CFD8DC"),
    ]

    for label, x, y, col in nodes:
        circle = patches.Circle((x, y), 6.5, facecolor=col, edgecolor="#263238", linewidth=1.5, zorder=4)
        ax.add_patch(circle)
        ax.text(x, y, label, ha="center", va="center", fontsize=8.5, weight="bold", color="#212121", zorder=5)

    # Edges
    def draw_edge(x1, y1, x2, y2, label, col="#546E7A", style="-"):
        ax.plot([x1, x2], [y1, y2], color=col, linestyle=style, linewidth=1.5, zorder=2)
        mx, my = (x1 + x2)/2, (y1 + y2)/2
        ax.text(mx, my, label, fontsize=7.5, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#FFFFFF", edgecolor=col, alpha=0.9), zorder=3)

    # Same zone
    draw_edge(20, 70, 50, 75, "SAME_ZONE", "#1976D2")
    draw_edge(20, 20, 50, 20, "SAME_ZONE", "#F57F17")
    # Functional
    draw_edge(20, 70, 35, 45, "NEAR (w=0.9)", "#00897B")
    draw_edge(50, 75, 35, 45, "NEAR (w=0.9)", "#00897B")
    draw_edge(75, 55, 85, 80, "NEAR (w=0.7)", "#00897B")
    draw_edge(50, 20, 80, 25, "NEAR (w=0.6)", "#00897B")
    # Distance constraints
    draw_edge(35, 45, 80, 25, "MIN_DIST >= 60m", "#E53935", style="--")
    draw_edge(20, 70, 75, 55, "ACCESS_FROM (w=0.5)", "#7B1FA2")

    # Legend / Info Box
    info_box = patches.FancyBboxPatch((2, 85), 45, 12, boxstyle="round,pad=1.0",
                                      facecolor="#F5F5F5", edgecolor="#9E9E9E", linewidth=1.0)
    ax.add_patch(info_box)
    ax.text(24.5, 93, "CampusGraph Topology (Contract 5)", weight="bold", fontsize=9.5, ha="center")
    ax.text(24.5, 88, "Nodes: [N, 20] (Width, Depth, Zone, Type One-Hot)\nEdges: [2, E], Edge Features: [E, 9]", fontsize=8, ha="center", color="#424242")

    plt.title("Figure 4.1: Topological Campus Graph Representation and Spatial Constraint Edges", weight="bold", pad=15)
    plt.tight_layout()
    out_file = FIGURES_DIR / "fig2_graph_representation.png"
    plt.savefig(out_file)
    plt.close()
    print(f"[GENERATED] {out_file}")


def plot_gnn_architecture():
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.set_xlim(0, 110)
    ax.set_ylim(0, 100)
    ax.axis("off")

    def box(x, y, w, h, t1, t2, col):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1.2",
                                      facecolor=col, edgecolor="#37474F", linewidth=1.3)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h*0.62, t1, ha="center", va="center", weight="bold", fontsize=9.5)
        ax.text(x + w/2, y + h*0.28, t2, ha="center", va="center", fontsize=8, color="#455A64")

    # Input features
    box(2, 60, 20, 25, "Graph Inputs", "Node Feats: [N, 20]\nEdge Feats: [E, 9]\nEdge Index: [2, E]", "#E3F2FD")

    # Projection
    box(26, 60, 18, 25, "Input Projection", "Linear(20, 64)\nReLU Activation", "#BBDEFB")

    # GNN Message Passing Layers
    box(48, 48, 24, 45, "GNN Encoder (3 Layers)",
        "Message: [h_v || e_uv] -> 64\nUpdate: [h_u || m_u] -> 64\nSum Aggregation\nEmbeddings: [N, 64]", "#C8E6C9")

    # Latent Sampling
    box(26, 12, 18, 26, "Latent Prior", "z_node ~ N(0, I) [N, 16]\nz_graph ~ N(0, I) [16]", "#FFF9C4")

    # Layout Decoder
    box(76, 25, 28, 55, "Layout Decoder",
        "Concat: [h_i || h_graph || z_i || z_g]\nInput Dim: 128 + 32 = 160\nDense(160, 64) + ReLU\nDense(64, 64) + ReLU\nLinear(64, 3) -> Sigmoid\nOutput: (u, v, vertical)", "#FFE0B2")

    # Bounded Output
    box(80, 2, 22, 16, "Bounded Footprints", "bounded_positions()\nFootprints on-site [N, 3]", "#FFCDD2")

    # Connectors
    def arr(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color="#37474F", lw=1.8, mutation_scale=12))

    arr(22, 72, 26, 72)
    arr(44, 72, 48, 72)
    arr(72, 70, 76, 70)
    arr(44, 25, 76, 40)
    arr(90, 25, 90, 18)

    plt.title("Figure 4.2: Graph Neural Network Architecture (GNN Encoder & Spatial Layout Decoder)", weight="bold", pad=15)
    plt.tight_layout()
    out_file = FIGURES_DIR / "fig3_gnn_architecture.png"
    plt.savefig(out_file)
    plt.close()
    print(f"[GENERATED] {out_file}")


def plot_nsga2_workflow():
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    def box(x, y, w, h, t1, t2, col):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1.2",
                                      facecolor=col, edgecolor="#37474F", linewidth=1.3)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h*0.62, t1, ha="center", va="center", weight="bold", fontsize=9.5)
        ax.text(x + w/2, y + h*0.28, t2, ha="center", va="center", fontsize=8, color="#455A64")

    box(5, 75, 25, 18, "Candidate Population", "100 GNN Layouts\nContract 6 Candidates", "#E1F5FE")
    box(38, 75, 26, 18, "Constraint Engine", "8 Checkers (Hard & Soft)\nFeasibility & Score", "#FFF3E0")
    box(72, 75, 24, 18, "Objective Evaluation", "5 Objectives Computed\n[f1, f2, f3, f4, f5] to minimise", "#E8F5E9")

    box(72, 40, 24, 22, "Non-Dominated Sort", "Fast Pareto Ranking\nFronts F1, F2, ..., Fk\nDominance check (a <= b)", "#E1BEE7")
    box(38, 40, 26, 22, "Crowding Distance", "Density Estimation in Front\nPreserves Diversity\nBoundary points = Inf", "#D1C4E9")
    box(5, 40, 25, 22, "Pareto Ranking", "Sort: (Front ASC,\nCrowding Distance DESC)\nBest trade-off ordering", "#C5CAE9")

    box(30, 8, 40, 20, "RankedLayouts Assembly", "Feasible Preferred\nTop-5 Pareto-Optimal Layouts\nSaved to Contract 8 JSON & SVG", "#C8E6C9")

    def arr(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color="#37474F", lw=1.8, mutation_scale=12))

    arr(30, 84, 38, 84)
    arr(64, 84, 72, 84)
    arr(84, 75, 84, 62)
    arr(72, 51, 64, 51)
    arr(38, 51, 30, 51)
    arr(17, 40, 35, 28)

    plt.title("Figure 4.3: NSGA-II Multi-Objective Optimization and Pareto Ranking Workflow", weight="bold", pad=15)
    plt.tight_layout()
    out_file = FIGURES_DIR / "fig4_nsga2_workflow.png"
    plt.savefig(out_file)
    plt.close()
    print(f"[GENERATED] {out_file}")


def plot_database_er_diagram():
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 110)
    ax.set_ylim(0, 100)
    ax.axis("off")

    def table_box(x, y, w, h, name, fields):
        # Header
        h_rect = patches.Rectangle((x, y + h - 6), w, 6, facecolor="#1976D2", edgecolor="#0D47A1", linewidth=1.2)
        b_rect = patches.Rectangle((x, y), w, h - 6, facecolor="#FFFFFF", edgecolor="#0D47A1", linewidth=1.2)
        ax.add_patch(b_rect)
        ax.add_patch(h_rect)
        ax.text(x + w/2, y + h - 3, name, ha="center", va="center", weight="bold", fontsize=9, color="#FFFFFF")
        
        # Fields
        for i, f in enumerate(fields):
            fy = y + h - 9 - i * 4.2
            ax.text(x + 2, fy, f, fontsize=7.5, color="#212121")

    # 8 Tables
    table_box(5, 70, 22, 26, "users", [
        "PK id : Integer",
        "name : String",
        "email : String (Unique)",
        "password_hash : String",
        "role : String",
        "created_at : DateTime",
    ])

    table_box(33, 70, 24, 26, "projects", [
        "PK id : Integer",
        "FK user_id -> users.id",
        "name : String",
        "description : String",
        "status : String",
        "created_at : DateTime",
    ])

    table_box(63, 70, 26, 26, "campus_requirements", [
        "PK id : Integer",
        "FK project_id -> projects.id",
        "site_width : Float",
        "site_height : Float",
        "min_green_percent : Float",
        "entrance_data : JSONB",
    ])

    table_box(5, 36, 24, 26, "buildings", [
        "PK id : Integer",
        "FK project_id -> projects.id",
        "name : String",
        "type : String",
        "zone : String",
        "width, depth, height : Float",
        "floor_count, req_count : Int",
    ])

    table_box(35, 36, 24, 26, "constraints", [
        "PK id : Integer",
        "FK project_id -> projects.id",
        "constraint_type : String",
        "source_id, target_id : Int",
        "value : Float",
        "priority : String",
    ])

    table_box(65, 36, 24, 26, "layout_runs", [
        "PK id : Integer",
        "FK project_id -> projects.id",
        "algorithm : String",
        "population_size : Int",
        "status : String",
        "completed_at : DateTime",
    ])

    table_box(65, 4, 24, 26, "layouts", [
        "PK id : Integer",
        "FK run_id -> layout_runs.id",
        "rank : Int",
        "feasible : Boolean",
        "layout_json : JSONB",
        "metrics_json : JSONB",
    ])

    table_box(33, 4, 26, 26, "selected_plans", [
        "PK id : Integer",
        "FK project_id -> projects.id",
        "FK layout_id -> layouts.id",
        "selected_by : Int",
        "selected_at : DateTime",
    ])

    # Connectors (Relational lines)
    def rel(x1, y1, x2, y2):
        ax.plot([x1, x2], [y1, y2], color="#37474F", linewidth=1.5, linestyle=":")

    rel(27, 82, 33, 82) # user -> project
    rel(57, 82, 63, 82) # project -> requirements
    rel(45, 70, 17, 62) # project -> buildings
    rel(45, 70, 47, 62) # project -> constraints
    rel(50, 70, 75, 62) # project -> layout_runs
    rel(77, 36, 77, 30) # layout_runs -> layouts
    rel(65, 17, 59, 17) # layouts -> selected_plans
    rel(45, 70, 45, 30) # project -> selected_plans

    plt.title("Figure 4.4: PostgreSQL Relational Database Schema and Contract Tables (Alembic Head)", weight="bold", pad=15)
    plt.tight_layout()
    out_file = FIGURES_DIR / "fig12_database_er_diagram.png"
    plt.savefig(out_file)
    plt.close()
    print(f"[GENERATED] {out_file}")


if __name__ == "__main__":
    print("=" * 60)
    print("  GENERATING ARCHITECTURE & SCHEMATIC FIGURES (300 DPI)")
    print("=" * 60)
    plot_graph_representation()
    plot_gnn_architecture()
    plot_nsga2_workflow()
    plot_database_er_diagram()
    print("\n[ALL SCHEMATICS SUCCESSFULLY GENERATED]")

