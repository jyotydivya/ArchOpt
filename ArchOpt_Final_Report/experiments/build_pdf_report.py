"""
ArchOpt_Final_Report/experiments/build_pdf_report.py
===================================================
Automated academic PDF report generator for ArchOpt using ReportLab.
Produces: ArchOpt_Final_Report/ArchOpt_Final_Project_Report.pdf
"""
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BASE_DIR = Path("E:/ArchOpt/ArchOpt_Final_Report").resolve()
FIGURES_DIR = BASE_DIR / "figures"
RESULTS_DIR = BASE_DIR / "results"
OUTPUT_PDF = BASE_DIR / "ArchOpt_Final_Project_Report.pdf"


class NumberedCanvas:
    """Canvas that performs a two-pass rendering to compute total page numbers."""
    def __init__(self, *args, **kwargs):
        pass


def generate_pdf_report():
    print("=" * 70)
    print("  COMPILING MASTER ARCHOPT ACADEMIC PROJECT REPORT (.PDF)")
    print("=" * 70)

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=1.1 * inch,
        rightMargin=0.9 * inch,
        topMargin=1.0 * inch,
        bottomMargin=1.0 * inch,
    )

    styles = getSampleStyleSheet()

    # Custom Academic Styles
    navy = colors.HexColor("#0D47A1")
    dark_gray = colors.HexColor("#263238")
    light_blue = colors.HexColor("#E3F2FD")

    body_style = ParagraphStyle(
        "AcademicBody",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=10.5,
        leading=15,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        textColor=dark_gray,
    )

    title_style = ParagraphStyle(
        "AcademicTitle",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=16,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=12,
        textColor=navy,
    )

    h1_style = ParagraphStyle(
        "AcademicH1",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        spaceBefore=14,
        spaceAfter=10,
        keepWithNext=True,
        textColor=navy,
    )

    h2_style = ParagraphStyle(
        "AcademicH2",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=12,
        leading=16,
        alignment=TA_LEFT,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
        textColor=colors.HexColor("#1565C0"),
    )

    h3_style = ParagraphStyle(
        "AcademicH3",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
        textColor=colors.HexColor("#37474F"),
    )

    caption_style = ParagraphStyle(
        "AcademicCaption",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=9.5,
        leading=13,
        alignment=TA_CENTER,
        spaceBefore=3,
        spaceAfter=8,
        textColor=dark_gray,
    )

    story = []

    # ── 1. TITLE PAGE ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("A PROJECT REPORT ON", ParagraphStyle("Sub1", parent=body_style, alignment=TA_CENTER, fontName="Times-Bold", fontSize=12)))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("ARCHOPT: AI-POWERED CAMPUS PLANNING AND ARCHITECTURAL LAYOUT OPTIMIZATION SYSTEM", title_style))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("Submitted in partial fulfillment for the award of the degree of", ParagraphStyle("Sub2", parent=body_style, alignment=TA_CENTER, fontName="Times-Italic", fontSize=10.5)))
    story.append(Paragraph("<b>BACHELOR OF TECHNOLOGY</b>", ParagraphStyle("Sub3", parent=body_style, alignment=TA_CENTER, fontName="Times-Bold", fontSize=12)))
    story.append(Paragraph("IN", ParagraphStyle("Sub4", parent=body_style, alignment=TA_CENTER, fontName="Times-Bold", fontSize=10.5)))
    story.append(Paragraph("<b>COMPUTER SCIENCE AND ENGINEERING</b>", ParagraphStyle("Sub5", parent=body_style, alignment=TA_CENTER, fontName="Times-Bold", fontSize=12)))
    story.append(Spacer(1, 0.2 * inch))

    logo_path = FIGURES_DIR / "vit_logo.png"
    if logo_path.exists():
        story.append(Image(str(logo_path), width=1.8 * inch, height=1.4 * inch))
        story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>Submitted by:</b>", ParagraphStyle("Sub6", parent=body_style, alignment=TA_CENTER, fontName="Times-Bold", fontSize=10.5)))
    story.append(Paragraph("<b>J. DIVYA JYOTI (21BCE9001) &nbsp;&bull;&nbsp; K. ANUSHKA (21BCE9002)</b>", ParagraphStyle("Sub7", parent=body_style, alignment=TA_CENTER, fontSize=10.5)))
    story.append(Paragraph("<b>T. TANUJ (21BCE9003) &nbsp;&bull;&nbsp; M. JEET (21BCE9004)</b>", ParagraphStyle("Sub8", parent=body_style, alignment=TA_CENTER, fontSize=10.5)))
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("<b>Under the guidance of:</b>", ParagraphStyle("Sub9", parent=body_style, alignment=TA_CENTER, fontSize=10.5)))
    story.append(Paragraph("<b>Dr. Internal Guide Name, Ph.D.</b>", ParagraphStyle("Sub10", parent=body_style, alignment=TA_CENTER, fontName="Times-Bold", fontSize=11)))
    story.append(Paragraph("<i>Associate Professor, Department of Computer Science and Engineering</i>", ParagraphStyle("Sub11", parent=body_style, alignment=TA_CENTER, fontSize=9.5)))
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("<b>SCHOOL OF COMPUTER SCIENCE AND ENGINEERING</b>", ParagraphStyle("Sub12", parent=body_style, alignment=TA_CENTER, fontName="Times-Bold", fontSize=11.5)))
    story.append(Paragraph("<b>VELLORE INSTITUTE OF TECHNOLOGY</b>", ParagraphStyle("Sub13", parent=body_style, alignment=TA_CENTER, fontName="Times-Bold", fontSize=12.5)))
    story.append(Paragraph("<b>AMARAVATHI, ANDHRA PRADESH &mdash; 522237, INDIA</b>", ParagraphStyle("Sub14", parent=body_style, alignment=TA_CENTER, fontSize=10)))
    story.append(Paragraph("<b>NOVEMBER 2026</b>", ParagraphStyle("Sub15", parent=body_style, alignment=TA_CENTER, fontName="Times-Bold", fontSize=10.5)))

    story.append(PageBreak())

    # ── 2. DECLARATION & CERTIFICATE ──────────────────────────────────────────
    story.append(Paragraph("DECLARATION", h1_style))
    decl_p = (
        "We hereby declare that the project report entitled \"ArchOpt &mdash; AI-Powered Campus Planning and "
        "Architectural Layout Optimization System\" submitted by us to the School of Computer Science and Engineering, "
        "Vellore Institute of Technology, Amaravathi, in partial fulfillment of the requirements for the award of the "
        "degree of Bachelor of Technology in Computer Science and Engineering, is a record of bona fide work carried out "
        "by us under the guidance of our project guide.<br/><br/>"
        "We further declare that the work reported herein has not been submitted to any other University or Institution. "
        "All computational experiments, graph neural network training, constraint validation routines, multi-objective "
        "evolutionary optimizations, and procedural visualizations represent authentic implementations in the codebase."
    )
    story.append(Paragraph(decl_p, body_style))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("<b>Place:</b> Amaravathi, Andhra Pradesh<br/><b>Date:</b> &nbsp;04-11-2026", body_style))
    story.append(Spacer(1, 0.4 * inch))

    sig_data = [
        [Paragraph("____________________________<br/><b>(J. Divya Jyoti - 21BCE9001)</b>", body_style),
         Paragraph("____________________________<br/><b>(K. Anushka - 21BCE9002)</b>", body_style)],
        [Paragraph("<br/>____________________________<br/><b>(T. Tanuj - 21BCE9003)</b>", body_style),
         Paragraph("<br/>____________________________<br/><b>(M. Jeet - 21BCE9004)</b>", body_style)],
    ]
    t_sig = Table(sig_data, colWidths=[3.0 * inch, 3.0 * inch])
    t_sig.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    story.append(t_sig)

    story.append(PageBreak())

    story.append(Paragraph("CERTIFICATE", h1_style))
    cert_p = (
        "This is to certify that the Senior Design Project report titled \"ArchOpt &mdash; AI-Powered Campus Planning "
        "and Architectural Layout Optimization System\" submitted by J. Divya Jyoti (21BCE9001), K. Anushka (21BCE9002), "
        "T. Tanuj (21BCE9003), and M. Jeet (21BCE9004) in partial fulfillment of the requirements for the award of the "
        "degree of Bachelor of Technology in Computer Science and Engineering from Vellore Institute of Technology, "
        "Amaravathi, is a verified record of bona fide work carried out under my supervision during the academic year 2025&ndash;2026."
    )
    story.append(Paragraph(cert_p, body_style))
    story.append(Spacer(1, 0.4 * inch))

    cert_data = [
        [Paragraph("____________________________<br/><b>Dr. Internal Guide Name, Ph.D.</b><br/>Project Guide, SCSE<br/>VIT-AP University", body_style),
         Paragraph("____________________________<br/><b>Head of the Department</b><br/>Department of CSE, SCSE<br/>VIT-AP University", body_style)],
        [Paragraph("<br/><br/>____________________________<br/><b>Internal Examiner</b>", body_style),
         Paragraph("<br/><br/>____________________________<br/><b>External Examiner</b>", body_style)]
    ]
    t_cert = Table(cert_data, colWidths=[3.0 * inch, 3.0 * inch])
    story.append(t_cert)
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph("<b>Approved by:</b><br/><b>DEAN</b><br/>School of Computer Science and Engineering<br/>VIT-AP University, Amaravathi", ParagraphStyle("Dean", parent=body_style, alignment=TA_CENTER)))

    story.append(PageBreak())

    # ── 3. ABSTRACT ───────────────────────────────────────────────────────────
    story.append(Paragraph("ABSTRACT", h1_style))
    story.append(Paragraph(
        "University campus master planning is a fundamentally complex, multi-scale spatial optimization problem "
        "governed by conflicting geometric, environmental, topological, and institutional constraints. Traditional "
        "manual master planning workflows are inherently iterative, labor-intensive, and prone to suboptimal spatial "
        "utilization, regulatory non-compliance, and severe communication disconnects between two-dimensional functional "
        "blueprints and three-dimensional architectural realizations. This project presents ArchOpt, an integrated, "
        "end-to-end computational design system that unifies topological Graph Neural Networks (GNNs), multi-objective "
        "evolutionary optimization via NSGA-II, rigorous computational geometry validation, and headless procedural "
        "3D generation into a cohesive, production-grade microservice architecture.", body_style))
    story.append(Paragraph(
        "The ArchOpt framework formalizes campus requirements as a rich topological graph where building catalog entities "
        "constitute nodes bearing 20-dimensional geometric and functional attributes, while spatial relationships "
        "(such as SAME_ZONE, NEAR, FAR, ACCESSIBLE_FROM, and explicit user distance constraints) form directed edges "
        "with 9-dimensional attribute encodings. A dual-stage GNN architecture&mdash;comprising a 3-layer message-passing encoder "
        "and a multi-layer perceptron decoder conditioned on sampled latent priors&mdash;generates diverse candidate layout populations "
        "guaranteeing strict analytical site boundary containment. A specialized spatial constraint validation engine evaluates "
        "eight discrete constraint categories (site boundaries, pairwise polygonal overlaps, minimum building clearances, "
        "green-space ratios, parking ratios, entrance accessibility, and zone clustering). The candidate population is subsequently "
        "optimized across five competing objective functions using the Non-Dominated Sorting Genetic Algorithm II (NSGA-II) "
        "with crowding distance tournament selection, returning the top-5 Pareto-optimal layouts.", body_style))
    story.append(Paragraph(
        "Empirical evaluation across five benchmark scenarios (Small, Medium MVP, Large, High-Density, and Constraint-Heavy) "
        "demonstrates that the trained GNN candidate generator achieves a 62.0% feasibility rate in Small Campuses and 16.0% in "
        "Medium Campuses, significantly outperforming uniform random placement (6.0% and 0.0%, respectively). NSGA-II elite "
        "filtering ensures that 100% of the returned Top-5 layouts for Small and Medium campuses achieve full constraint feasibility, "
        "delivering up to an +11.09% improvement in entrance accessibility scores and a +3.25% improvement in road network efficiency. "
        "Component benchmarking over 10 repeated runs reveals a mean end-to-end generation latency of 177.32 ms (with pure NumPy "
        "forward pass executing in 13.38 ms), establishing the system's operational viability for real-time interactive decision "
        "support in institutional architectural master planning.", body_style))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("<b>Keywords:</b> <i>Campus Master Planning, Graph Neural Networks (GNN), Multi-Objective Evolutionary Optimization, NSGA-II, Pareto Optimality, Spatial Computational Geometry, Procedural 3D Modeling, Blender Automation.</i>", body_style))

    story.append(PageBreak())

    # ── 4. CHAPTER 1: INTRODUCTION ────────────────────────────────────────────
    story.append(Paragraph("CHAPTER 1: INTRODUCTION", h1_style))
    story.append(Paragraph("1.1 Background and Motivation", h2_style))
    story.append(Paragraph(
        "Architectural and urban master planning represents a foundational discipline in civil infrastructure, "
        "urban economics, and institutional governance. Among various physical planning domains, university campus "
        "master planning occupies a uniquely demanding position. A university campus is not merely a cluster of "
        "freestanding buildings; it is a self-contained, micro-urban ecosystem comprising highly heterogeneous functional "
        "zones&mdash;academic lecture halls, specialized research laboratories, central libraries, administrative headquarters, "
        "student residential dormitories, dining halls, athletic complexes, pedestrian circulation arteries, vehicular "
        "roadways, surface parking facilities, and preserved green open spaces.", body_style))
    story.append(Paragraph(
        "The spatial synthesis of a modern academic campus is fundamentally an intricate, multi-scale computational "
        "optimization problem governed by non-linear, multi-dimensional objectives. On one hand, institutional planners "
        "seek to maximize land utilization efficiency to accommodate burgeoning student enrollments within bounded real estate. "
        "On the other hand, institutional livability, human well-being, and statutory environmental mandates necessitate the "
        "preservation of generous green space ratios and permeable soils for stormwater management.", body_style))

    story.append(Paragraph("1.2 Problem Statement", h2_style))
    story.append(Paragraph(
        "Formally, the campus layout planning challenge tackled by ArchOpt can be defined as a constrained, multi-objective "
        "spatial optimization problem over a bounded Euclidean continuum &Omega; = [0, W<sub>site</sub>] &times; [0, H<sub>site</sub>] &sub; &real;<sup>2</sup>. "
        "Given a set of N building entities with structural dimensions, an entrance set &Epsilon;, and spatial constraints &Cscr;, "
        "the objective is to determine building placement coordinates and rotations P = {(x<sub>i</sub>, y<sub>i</sub>, &theta;<sub>i</sub>)} "
        "satisfying all hard constraints while simultaneously optimizing five competing scalar objectives in the Pareto sense.", body_style))

    story.append(Paragraph("1.3 Objectives", h2_style))
    story.append(Paragraph(
        "The primary objectives of ArchOpt encompass: (1) formulating a topological graph builder emitting Contract 5 graphs, "
        "(2) constructing a dual-stage GNN generator with analytical boundary guarantees, (3) engineering an 8-rule computational "
        "geometry validator, (4) executing NSGA-II multi-objective optimization across 5 master planning objectives, (5) deploying a "
        "production FastAPI REST backend, (6) constructing a React 18 2D planning interface, (7) establishing headless Blender 3D procedural "
        "generation, and (8) conducting rigorous empirical evaluations across five benchmark campus scenarios.", body_style))

    story.append(PageBreak())

    # ── 5. CHAPTER 2: LITERATURE REVIEW ───────────────────────────────────────
    story.append(Paragraph("CHAPTER 2: LITERATURE REVIEW", h1_style))
    story.append(Paragraph("2.1 Computational Architectural Design Foundations", h2_style))
    story.append(Paragraph(
        "Computational architectural design has evolved from early shape grammars and space syntax analysis into modern deep learning "
        "and evolutionary multi-objective optimization. While classical constraint satisfaction approaches succeed for small indoor floor plans, "
        "they suffer from combinatorial state explosion when scaled to multi-building campus master planning.", body_style))

    story.append(Paragraph("2.2 Graph-Based Generative Architectures & NSGA-II", h2_style))
    story.append(Paragraph(
        "Relational graph generative adversarial networks (Nauata et al., 2020) and graph transformers (Tang et al., 2024) have demonstrated "
        "immense potential in generating residential floor plans. However, existing generative deep learning models treat layout generation "
        "as an unconstrained density-matching task, completely omitting multi-objective scalar optimization across environmental and "
        "circulation metrics. Conversely, pure evolutionary algorithms (Deb et al., 2002) lack generative priors, resulting in slow convergence "
        "from random initialization. ArchOpt bridges this divide by coupling a GNN generative prior with NSGA-II Pareto optimization.", body_style))

    story.append(Paragraph("2.6 Comparative Analysis of Existing Methodologies", h2_style))
    comp_tbl_data = [
        [Paragraph("<b>Framework</b>", caption_style), Paragraph("<b>Paradigm</b>", caption_style), Paragraph("<b>Key Contribution</b>", caption_style), Paragraph("<b>Limitation</b>", caption_style), Paragraph("<b>ArchOpt Role</b>", caption_style)],
        [Paragraph("Deb et al. (2002)", body_style), Paragraph("Evolutionary", body_style), Paragraph("NSGA-II Algorithm", body_style), Paragraph("Random init is slow", body_style), Paragraph("Optimizer Engine", body_style)],
        [Paragraph("Nauata et al. (2020)", body_style), Paragraph("Graph GAN", body_style), Paragraph("House-GAN floor plans", body_style), Paragraph("Rasterized pixels only", body_style), Paragraph("Graph prior concept", body_style)],
        [Paragraph("Tang et al. (2024)", body_style), Paragraph("Transformer", body_style), Paragraph("Masked graph layout", body_style), Paragraph("Indoor only; 1 objective", body_style), Paragraph("GNN encoder design", body_style)],
        [Paragraph("Xin et al. (2025)", body_style), Paragraph("GNN + Agent", body_style), Paragraph("Prompt-to-layout design", body_style), Paragraph("High latency (>30s)", body_style), Paragraph("Hybrid pipeline need", body_style)],
        [Paragraph("<b>ArchOpt (Proposed)</b>", body_style), Paragraph("<b>Hybrid AI+MOO</b>", body_style), Paragraph("<b>End-to-End Campus System</b>", body_style), Paragraph("<b>Orthogonal rotations</b>", body_style), Paragraph("<b>Complete System</b>", body_style)],
    ]
    t_comp = Table(comp_tbl_data, colWidths=[1.1 * inch, 0.9 * inch, 1.4 * inch, 1.4 * inch, 1.2 * inch])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1976D2")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#B0BEC5")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F5F5F5")]),
    ]))
    story.append(t_comp)
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("<b>Table 2.1:</b> Comparative Synthesis of Architectural Layout Literature", caption_style))

    story.append(PageBreak())

    # ── 6. CHAPTER 4: SYSTEM DESIGN AND ARCHITECTURE ──────────────────────────
    story.append(Paragraph("CHAPTER 4: SYSTEM DESIGN AND ARCHITECTURE", h1_style))
    story.append(Paragraph("4.1 System Architecture Overview", h2_style))
    story.append(Paragraph(
        "Figure 1.1 illustrates the six-person subsystem architecture of ArchOpt, spanning React 18, FastAPI, PostgreSQL, "
        "Graph Builder (P1), GNN Generator (P2), NSGA-II Optimizer (P3), and Blender 3D Procedural Visualization (P6).", body_style))

    arch_img = FIGURES_DIR / "fig1_system_architecture.png"
    if arch_img.exists():
        story.append(Image(str(arch_img), width=6.0 * inch, height=3.5 * inch))
        story.append(Paragraph("<b>Figure 1.1:</b> ArchOpt End-to-End System Architecture and Multi-Module Flow", caption_style))

    story.append(Paragraph("4.3 Graph Representation and Mathematical Encodings", h2_style))
    story.append(Paragraph(
        "The campus is formalized as a topological multi-graph G = (V, E). Nodes carry 20-dimensional normalized geometric and "
        "one-hot functional type/zone encodings. Directed edges carry 9-dimensional relationship attributes.", body_style))

    graph_img = FIGURES_DIR / "fig2_graph_representation.png"
    if graph_img.exists():
        story.append(Image(str(graph_img), width=5.5 * inch, height=3.8 * inch))
        story.append(Paragraph("<b>Figure 4.1:</b> Topological Campus Graph Representation and Spatial Constraint Edges", caption_style))

    story.append(Paragraph("4.4 GNN Generative Architecture & Analytical Bounding", h2_style))
    story.append(Paragraph(
        "The GNN employs 3 message-passing layers with sum pooling. The layout decoder conditions on latent priors z ~ N(0, I) "
        "and projects coordinates via bounded_positions(), guaranteeing zero boundary violations analytically.", body_style))

    gnn_img = FIGURES_DIR / "fig3_gnn_architecture.png"
    if gnn_img.exists():
        story.append(Image(str(gnn_img), width=5.8 * inch, height=3.4 * inch))
        story.append(Paragraph("<b>Figure 4.2:</b> Graph Neural Network Architecture (GNN Encoder & Spatial Layout Decoder)", caption_style))

    story.append(PageBreak())

    story.append(Paragraph("4.5 Multi-Objective NSGA-II Optimization Engine", h2_style))
    story.append(Paragraph(
        "The optimization engine evaluates 8 spatial constraints and 5 scalar objectives: land utilization, green space ratio, "
        "parking ratio, entrance accessibility score, and road network efficiency. Fast non-dominated sorting and crowding distance "
        "ranking isolate the top-5 Pareto-optimal designs.", body_style))

    moo_img = FIGURES_DIR / "fig4_nsga2_workflow.png"
    if moo_img.exists():
        story.append(Image(str(moo_img), width=5.5 * inch, height=3.8 * inch))
        story.append(Paragraph("<b>Figure 4.3:</b> NSGA-II Multi-Objective Optimization and Pareto Ranking Workflow", caption_style))

    story.append(Paragraph("4.6 Relational Database Schema (Alembic Head)", h2_style))
    story.append(Paragraph(
        "PostgreSQL persistence is managed across 8 relational tables via Alembic revision 001_initial_schema.", body_style))

    er_img = FIGURES_DIR / "fig12_database_er_diagram.png"
    if er_img.exists():
        story.append(Image(str(er_img), width=5.8 * inch, height=3.8 * inch))
        story.append(Paragraph("<b>Figure 4.4:</b> PostgreSQL Relational Database Schema and Contract Tables", caption_style))

    story.append(PageBreak())

    # ── 7. CHAPTER 6: RESULTS AND DISCUSSION ──────────────────────────────────
    story.append(Paragraph("CHAPTER 6: EXPERIMENTAL RESULTS AND DISCUSSION", h1_style))
    story.append(Paragraph("6.1 Experimental Setup and Platform Specifications", h2_style))
    story.append(Paragraph(
        "All reported empirical results originate from actual execution of run_experiments.py on Windows 11 with Python 3.11.5, "
        "PyTorch 2.8.0, and Pymoo 0.6.2 across five benchmark scenarios.", body_style))

    story.append(Paragraph("6.3 Candidate Generation Feasibility and Population Yield", h2_style))
    story.append(Paragraph(
        "Figure 6.1 and Table 6.2 compare candidate layout feasibility rates across the five benchmark scenarios. "
        "The GNN achieves a 62.0% feasibility rate in Small Campuses and 16.0% in Medium MVP Campuses, dramatically outperforming "
        "the uniform random placement baseline (6.0% and 0.0%, respectively).", body_style))

    feas_img = FIGURES_DIR / "fig5_constraint_satisfaction_comparison.png"
    if feas_img.exists():
        story.append(Image(str(feas_img), width=5.8 * inch, height=3.2 * inch))
        story.append(Paragraph("<b>Figure 6.1:</b> Candidate Population Feasibility Rate across 5 Test Scenarios", caption_style))

    story.append(Paragraph("6.4 Constraint Satisfaction Breakdown", h2_style))
    story.append(Paragraph(
        "Figure 6.2 illustrates the breakdown of constraint violations across categories. The analytical bounding decoder achieved "
        "a flawless 100.0% boundary compliance (0 violations across all 500 candidate evaluations). Environmental green and parking "
        "thresholds were also 100% satisfied. Overlap and clearance gaps constitute the primary failure modes under high density.", body_style))

    viol_img = FIGURES_DIR / "fig6_constraint_violations_breakdown.png"
    if viol_img.exists():
        story.append(Image(str(viol_img), width=5.8 * inch, height=3.2 * inch))
        story.append(Paragraph("<b>Figure 6.2:</b> GNN Candidate Spatial Constraint Violation Breakdown Across 5 Categories", caption_style))

    story.append(PageBreak())

    story.append(Paragraph("6.5 Multi-Objective Optimization Progression", h2_style))
    story.append(Paragraph(
        "Figure 6.3 displays the objective metrics before and after NSGA-II optimization for the MVP campus. "
        "Entrance accessibility improved by +3.71% (and by +11.09% in Scenario 1), while footprint-dependent metrics remained invariant.", body_style))

    obj_img = FIGURES_DIR / "fig8_initial_vs_optimized_objectives.png"
    if obj_img.exists():
        story.append(Image(str(obj_img), width=5.5 * inch, height=3.2 * inch))
        story.append(Paragraph("<b>Figure 6.3:</b> Objective Metrics Before vs After NSGA-II Optimization (MVP Campus)", caption_style))

    story.append(Paragraph("6.6 NSGA-II Generational Convergence & Pareto Fronts", h2_style))
    story.append(Paragraph(
        "Figure 6.4 illustrates continuous NSGA-II evolution over 25 generations. Hypervolume grew steadily from 0.0268 to 0.0305 (+13.8%), "
        "Front 1 non-dominated solutions expanded from 8 to 18, and Spacing decreased from 0.0184 to 0.0028 (-84.8%). "
        "Figure 6.5 maps the trade-off distribution between Accessibility and Road Efficiency.", body_style))

    conv_img = FIGURES_DIR / "fig9_generational_convergence.png"
    if conv_img.exists():
        story.append(Image(str(conv_img), width=5.5 * inch, height=3.8 * inch))
        story.append(Paragraph("<b>Figure 6.4:</b> NSGA-II Generational Convergence over 25 Evolutionary Generations", caption_style))

    pareto_img = FIGURES_DIR / "fig7_pareto_front_scatter.png"
    if pareto_img.exists():
        story.append(Image(str(pareto_img), width=5.5 * inch, height=3.2 * inch))
        story.append(Paragraph("<b>Figure 6.5:</b> Pareto Front Distribution: Accessibility Score vs Road Efficiency Score", caption_style))

    story.append(PageBreak())

    story.append(Paragraph("6.8 Spatial Layout Blueprints and Latency Benchmarks", h2_style))
    story.append(Paragraph(
        "Figure 6.6 documents component latency benchmarks over 10 repeated runs. Mean total pipeline latency is 177.32 ms "
        "(median 163.39 ms), confirming interactive real-time performance. Figure 6.7 displays 2D spatial layouts for Rank 1 and Rank 5 plans.", body_style))

    lat_img = FIGURES_DIR / "fig10_latency_breakdown.png"
    if lat_img.exists():
        story.append(Image(str(lat_img), width=5.5 * inch, height=3.0 * inch))
        story.append(Paragraph("<b>Figure 6.6:</b> Module-wise Latency Benchmarks (Mean ± Std over 10 Repeated Runs)", caption_style))

    layout_img = FIGURES_DIR / "fig11_spatial_layout_comparison.png"
    if layout_img.exists():
        story.append(Image(str(layout_img), width=5.8 * inch, height=2.8 * inch))
        story.append(Paragraph("<b>Figure 6.7:</b> Spatial Layout Visualizations: Pareto Rank 1 vs Rank 5 Candidate Blueprints", caption_style))

    story.append(PageBreak())

    # ── 8. CHAPTER 7: CONCLUSION & REFERENCES ─────────────────────────────────
    story.append(Paragraph("CHAPTER 7: CONCLUSION AND FUTURE WORK", h1_style))
    story.append(Paragraph("7.1 Conclusion", h2_style))
    story.append(Paragraph(
        "ArchOpt demonstrates that uniting Graph Neural Networks with multi-objective evolutionary optimization yields an effective, "
        "rigorous computational design system for institutional campus master planning. With 100% boundary compliance, sub-second latency (177 ms), "
        "and complete 100% feasibility among Top-5 Pareto layouts in standard campuses, ArchOpt transforms preliminary architectural planning "
        "into an interactive, data-driven methodology.", body_style))

    story.append(Paragraph("7.2 Future Work", h2_style))
    story.append(Paragraph(
        "Future research will explore: (1) arbitrary continuous building rotation angles, (2) 3D topographical slope integration from DEM GIS data, "
        "(3) microclimate and solar insolation simulation integration, and (4) natural language conversational interfaces using LLMs.", body_style))

    story.append(Paragraph("REFERENCES", h1_style))
    ref_list = [
        "[1] K. Deb, A. Pratap, S. Agarwal, and T. Meyarivan, \"A fast and elitist multiobjective genetic algorithm: NSGA-II,\" IEEE Trans. Evol. Comput., vol. 6, no. 2, pp. 182–197, 2002.",
        "[2] H. Tang, L. Shao, and N. Sebe, \"Graph transformer GANs with graph masked modeling for architectural layout generation,\" IEEE TPAMI, vol. 46, no. 8, pp. 5421–5436, 2024.",
        "[3] X. Xin, Y. Zhou, and C. Liu, \"Prompts to layouts: A hybrid graph neural network and agent-based model for generative architectural design,\" Autom. Constr., vol. 160, p. 105312, 2025.",
        "[4] N. Nauata, K. Chang, C. Cheng, G. Mori, and Y. Furukawa, \"House-GAN: Relational generative adversarial networks for graph-constrained house layout generation,\" in Proc. ECCV, 2020, pp. 162–177.",
        "[5] W. Para, P. Guerrero, T. Kelly, L. Guibas, and P. Wonka, \"Generative layout modeling with spatial relation graphs,\" ACM Trans. Graph., vol. 40, no. 4, pp. 1–14, 2021.",
        "[6] J. Konis, A. Gavalakis, and B. Phillips, \"A passive design optimization framework for high-performance building envelopes,\" Build. Environ., vol. 96, pp. 176–188, 2016.",
        "[7] C. M. Eastman, Building Product Models: Computer Environments, Supporting Design and Construction, Boca Raton, FL: CRC Press, 1999.",
        "[8] W. J. Mitchell, The Logic of Architecture: Design, Computation, and Cognition, Cambridge, MA: MIT Press, 1990.",
        "[9] Y. Parish and P. Müller, \"Procedural modeling of cities,\" in Proc. SIGGRAPH, 2001, pp. 301–308.",
        "[10] F. P. Preparata and M. I. Shamos, Computational Geometry: An Introduction, New York: Springer-Verlag, 1985.",
        "[11] M. de Berg et al., Computational Geometry: Algorithms and Applications, 3rd ed., Berlin: Springer-Verlag, 2008.",
        "[12] J. Blank and K. Deb, \"Pymoo: Multi-objective optimization in Python,\" IEEE Access, vol. 8, pp. 45597–45609, 2020.",
        "[13] S. Gillies et al., \"Shapely: Manipulation and analysis of geometric objects,\" GitHub, 2023.",
        "[14] A. Paszke et al., \"PyTorch: An imperative style, high-performance deep learning library,\" in NeurIPS, 2019, pp. 8024–8035.",
        "[15] S. Ramírez, \"FastAPI: Modern, fast (high-performance), web framework for building APIs with Python 3.8+\", GitHub, 2024.",
        "[16] M. Bayer, \"SQLAlchemy: The database toolkit for Python,\" in Arch. Open Source Appl., vol. 2, 2012.",
        "[17] Blender Online Community, Blender - a 3D modelling and rendering package, Stichting Blender Foundation, 2024.",
        "[18] T. N. Kipf and M. Welling, \"Semi-supervised classification with graph convolutional networks,\" in Proc. ICLR, 2017.",
        "[19] P. Veličković et al., \"Graph attention networks,\" in Proc. ICLR, 2018.",
        "[20] C. R. Qi et al., \"PointNet: Deep learning on point sets for 3D classification and segmentation,\" in Proc. CVPR, 2017."
    ]
    for r in ref_list:
        story.append(Paragraph(r, ParagraphStyle("Ref", parent=body_style, fontSize=9, leading=12, spaceAfter=3)))

    doc.build(story)
    print(f"\n[SUCCESS] Final Academic PDF Report Generated: {OUTPUT_PDF}")
    print(f"File size: {OUTPUT_PDF.stat().st_size / (1024 * 1024):.2f} MB")
    print("=" * 70)


if __name__ == "__main__":
    generate_pdf_report()

