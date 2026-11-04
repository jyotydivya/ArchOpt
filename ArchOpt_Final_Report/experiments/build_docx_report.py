"""
ArchOpt_Final_Report/experiments/build_docx_report.py
=====================================================
Automated, high-fidelity academic project report generator for ArchOpt.
Produces: ArchOpt_Final_Report/ArchOpt_Final_Project_Report.docx

Follows the structural, typographic, and stylistic conventions of the
supplied VIT-AP B.Tech Final Year CSE/AI-ML Project Report template:
- Page setup: A4, 1.25" left margin, 1.0" right/top/bottom margins.
- Typography: Times New Roman, 12pt body, 1.5 line spacing, 6pt after.
- Complete Preliminary Pages (Title, Declaration, Certificate, Abstract, Ack, TOC, LOF, LOT, Abbreviations)
- Chapters 1 to 7 with extensive technical depth, empirical tables, embedded 300-DPI figures, and exact equations.
- IEEE References & Comprehensive Appendices.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

BASE_DIR = Path("E:/ArchOpt/ArchOpt_Final_Report").resolve()
RESULTS_DIR = BASE_DIR / "results"
FIGURES_DIR = BASE_DIR / "figures"
OUTPUT_DOCX = BASE_DIR / "ArchOpt_Final_Project_Report.docx"


# ==============================================================================
# XML & STYLING HELPERS
# ==============================================================================

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set inner cell padding in twips (1/20 pt)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for margin_name, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(margin_name)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def set_cell_shading(cell, color_hex):
    """Set background color of a table cell."""
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def format_table_headers(table, col_widths=None):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    # Format header row
    hdr_cells = table.rows[0].cells
    for i, cell in enumerate(hdr_cells):
        set_cell_shading(cell, "ECEFF1")
        set_cell_margins(cell, top=140, bottom=140, left=140, right=140)
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            for run in p.runs:
                run.font.bold = True
                run.font.color.rgb = RGBColor(0, 0, 0)
                run.font.name = "Times New Roman"
                run.font.size = Pt(9.5)

    # Alternate row colors for data rows
    for r_idx in range(1, len(table.rows)):
        row = table.rows[r_idx]
        shd_col = "F5F5F5" if r_idx % 2 == 1 else "FFFFFF"
        for i, cell in enumerate(row.cells):
            set_cell_shading(cell, shd_col)
            set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
            for p in cell.paragraphs:
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.15
                for run in p.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(9.0)

    # Set column widths if provided
    if col_widths:
        for row in table.rows:
            for i, w in enumerate(col_widths):
                if i < len(row.cells):
                    row.cells[i].width = Inches(w)


def add_p(doc, text="", align=WD_ALIGN_PARAGRAPH.JUSTIFY, bold=False, italic=False, size=12, after=6, space_before=0, line_spacing=1.5):
    """
    Adds one or more paragraphs to the document.
    Splits on newlines so each logical line becomes its OWN separate paragraph.
    This completely eliminates Word's soft-break full-justification stretching bug,
    guaranteeing that text never renders with wide, gaping white spaces between words.
    List items, bullet points, and short lead-in headings are aligned LEFT with clean typography.
    """
    if not text:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(after)
        return p

    import re

    # Normalize carriage returns
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")

    created = []
    non_empty = [l.strip() for l in lines if l.strip()]

    if not non_empty:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(after)
        return p

    for idx, line in enumerate(non_empty):
        p = doc.add_paragraph()
        created.append(p)

        # Detect list items, short sub-headings, and formulas
        is_bullet = line.startswith(("•", "-", "*", "–"))
        is_numbered = bool(re.match(r"^\d+[\.\)]\s", line)) or bool(re.match(r"^[A-Za-z][\.\)]\s", line)) or line.startswith("UC-")
        is_short_title = len(line) < 75 and line.endswith(":")

        if is_bullet or is_numbered:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(3)
        elif is_short_title:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.keep_with_next = True
        else:
            p.alignment = align
            p.paragraph_format.space_before = Pt(space_before if idx == 0 else 0)
            p.paragraph_format.space_after = Pt(after if idx == len(non_empty) - 1 else 4)

        p.paragraph_format.line_spacing = line_spacing

        run = p.add_run(line)
        run.bold = bold
        run.italic = italic
        run.font.name = "Times New Roman"
        run.font.size = Pt(size)
        run.font.color.rgb = RGBColor(33, 33, 33)

    return created[0] if created else doc.add_paragraph()


def add_h1(doc, text):
    """Chapter heading."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(12)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text.upper())
    run.bold = True
    run.font.name = "Times New Roman"
    run.font.size = Pt(15)
    run.font.color.rgb = RGBColor(0, 0, 0)
    return p


def add_h2(doc, text):
    """Section heading."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.bold = True
    run.font.name = "Times New Roman"
    run.font.size = Pt(13)
    run.font.color.rgb = RGBColor(0, 0, 0)
    return p


def add_h3(doc, text):
    """Sub-section heading."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.bold = True
    run.font.name = "Times New Roman"
    run.font.size = Pt(11.5)
    run.font.color.rgb = RGBColor(0, 0, 0)
    return p


def add_fig(doc, img_path, caption_num, caption_text, width=Inches(6.0)):
    if not Path(img_path).exists():
        return
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(8)
    p_img.paragraph_format.space_after = Pt(4)
    p_img.paragraph_format.keep_with_next = True
    run = p_img.add_run()
    run.add_picture(str(img_path), width=width)

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(2)
    p_cap.paragraph_format.space_after = Pt(10)
    run_cap = p_cap.add_run(f"Figure {caption_num}: {caption_text}")
    run_cap.font.name = "Times New Roman"
    run_cap.font.size = Pt(10.5)
    run_cap.bold = True
    run_cap.font.color.rgb = RGBColor(38, 50, 56)


def add_callout(doc, text, title=""):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.2)
    set_cell_shading(cell, "ECEFF1")
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    p = cell.paragraphs[0]
    p.paragraph_format.line_spacing = 1.2
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    if title:
        r_title = p.add_run(f"{title}\n")
        r_title.bold = True
        r_title.font.name = "Times New Roman"
        r_title.font.size = Pt(10.5)
        r_title.font.color.rgb = RGBColor(0, 0, 0)
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(10)
    run.italic = True
    run.font.color.rgb = RGBColor(38, 50, 56)
    p_space = doc.add_paragraph()
    p_space.paragraph_format.space_before = Pt(4)
    p_space.paragraph_format.space_after = Pt(4)


def add_equation(doc, eq_text, eq_num=""):
    """
    Adds a professional, publication-quality mathematical equation block.
    The equation is centered in Cambria Math italic typography with a right-aligned equation tag (e.g., (4.1)).
    """
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

    c_eq = tbl.rows[0].cells[0]
    c_num = tbl.rows[0].cells[1]
    c_eq.width = Inches(5.4)
    c_num.width = Inches(0.8)

    set_cell_margins(c_eq, top=40, bottom=40, left=40, right=40)
    set_cell_margins(c_num, top=40, bottom=40, left=40, right=40)

    p_eq = c_eq.paragraphs[0]
    p_eq.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_eq.paragraph_format.space_before = Pt(4)
    p_eq.paragraph_format.space_after = Pt(4)
    p_eq.paragraph_format.line_spacing = 1.15

    r_eq = p_eq.add_run(eq_text)
    r_eq.font.name = "Cambria Math"
    r_eq.font.size = Pt(11)
    r_eq.font.italic = True
    r_eq.font.color.rgb = RGBColor(0, 0, 0)

    p_num = c_num.paragraphs[0]
    p_num.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_num.paragraph_format.space_before = Pt(4)
    p_num.paragraph_format.space_after = Pt(4)
    p_num.paragraph_format.line_spacing = 1.15

    if eq_num:
        r_num = p_num.add_run(f"({eq_num})")
        r_num.font.name = "Times New Roman"
        r_num.font.size = Pt(10)
        r_num.font.bold = True
        r_num.font.color.rgb = RGBColor(70, 70, 70)

    # Borderless table
    borders = parse_xml(f'<w:tblBorders {nsdecls("w")}>'
                        '<w:top w:val="none"/>'
                        '<w:left w:val="none"/>'
                        '<w:bottom w:val="none"/>'
                        '<w:right w:val="none"/>'
                        '<w:insideH w:val="none"/>'
                        '<w:insideV w:val="none"/>'
                        '</w:tblBorders>')
    tbl._tbl.tblPr.append(borders)


# ==============================================================================
# PRELIMINARY PAGES
# ==============================================================================

def make_preliminary_pages(doc):
    # ── 1. TITLE PAGE ─────────────────────────────────────────────────────────
    add_p(doc, "A PROJECT REPORT ON", align=WD_ALIGN_PARAGRAPH.CENTER, size=13, bold=True, space_before=10, after=12)
    
    p_title = add_p(doc, "ARCHOPT: A CONTRACT-DRIVEN GRAPH LEARNING AND MULTI-OBJECTIVE OPTIMIZATION FRAMEWORK FOR AI-ASSISTED CAMPUS LAYOUT PLANNING",
                    align=WD_ALIGN_PARAGRAPH.CENTER, size=15, bold=True, after=16)
    p_title.runs[0].font.color.rgb = RGBColor(0, 0, 0)

    add_p(doc, "Submitted in partial fulfillment of the requirements for the award of the degree of", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, italic=True, after=4)
    add_p(doc, "BACHELOR OF TECHNOLOGY", align=WD_ALIGN_PARAGRAPH.CENTER, size=13, bold=True, after=2)
    add_p(doc, "IN", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, bold=True, after=2)
    add_p(doc, "COMPUTER SCIENCE AND ENGINEERING", align=WD_ALIGN_PARAGRAPH.CENTER, size=13, bold=True, after=14)

    # University Logo
    logo_path = FIGURES_DIR / "vit_logo.png"
    if logo_path.exists():
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_after = Pt(14)
        p_logo.add_run().add_picture(str(logo_path), width=Inches(1.8))

    add_p(doc, "Submitted by:", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, bold=True, after=6)
    candidates = [
        "DIVYA JYOTY — 23BCE20341",
        "BAKARAJU KRISHNA TEJA — 24BCE7012",
        "SATYA TANMAYI PEMMADI — 24BCA7375",
        "TANUJ KRISHNA AGGARWAL — 24BCA7536",
        "RAJJEET SAHA — 24BCE7101",
        "ANSHIKA SINGH — 23BCE7284",
    ]
    for cand in candidates:
        add_p(doc, cand, align=WD_ALIGN_PARAGRAPH.CENTER, size=10.5, bold=True, after=2.5)

    add_p(doc, "Under the guidance of:", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, bold=True, after=4)
    add_p(doc, "Project Guide & Review Committee", align=WD_ALIGN_PARAGRAPH.CENTER, size=11.5, bold=True, after=2)
    add_p(doc, "Department of Computer Science and Engineering", align=WD_ALIGN_PARAGRAPH.CENTER, size=10, italic=True, after=16)

    add_p(doc, "SCHOOL OF COMPUTER SCIENCE AND ENGINEERING (SCOPE)", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, bold=True, after=3)
    add_p(doc, "VELLORE INSTITUTE OF TECHNOLOGY (VIT-AP UNIVERSITY)", align=WD_ALIGN_PARAGRAPH.CENTER, size=13, bold=True, after=3)
    add_p(doc, "AMARAVATI, ANDHRA PRADESH — 522237, INDIA", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, bold=True, after=4)
    add_p(doc, "NOVEMBER 2026", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, bold=True, after=10)

    doc.add_page_break()

    # ── 2. DECLARATION ────────────────────────────────────────────────────────
    add_h1(doc, "DECLARATION")
    decl_text = (
        "We hereby declare that the project report entitled \"ArchOpt: A Contract-Driven Graph Learning and "
        "Multi-Objective Optimization Framework for AI-Assisted Campus Layout Planning\" submitted by us to the "
        "School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology (VIT-AP University), "
        "Amaravati, in partial fulfillment of the requirements for the award of the degree of Bachelor of Technology "
        "in Computer Science and Engineering, is a record of bona fide work carried out by us under the supervision "
        "and guidance of our project guide.\n\n"
        "We further declare that the work reported in this project report has not been submitted either in part or "
        "in full to any other University or Institution for the award of any degree, diploma, or certificate. All "
        "computational experiments, graph neural network training, constraint validation engines, multi-objective "
        "evolutionary optimizations, and procedural visualizations represent authentic engineering implementations "
        "conducted directly within the project repository."
    )
    add_p(doc, decl_text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=11.5, after=20)

    add_p(doc, "Place: Amaravati, Andhra Pradesh", align=WD_ALIGN_PARAGRAPH.LEFT, size=11, bold=True, after=4)
    add_p(doc, "Date:  04-11-2026", align=WD_ALIGN_PARAGRAPH.LEFT, size=11, bold=True, after=24)

    # Candidates table for 6 students: 3 rows x 2 cols (no signature blanks)
    sig_tbl = doc.add_table(rows=3, cols=2)
    sig_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r in sig_tbl.rows:
        for c in r.cells:
            c.width = Inches(3.0)
    sig_tbl.rows[0].cells[0].paragraphs[0].text = "DIVYA JYOTY\nReg. No: 23BCE20341"
    sig_tbl.rows[0].cells[1].paragraphs[0].text = "BAKARAJU KRISHNA TEJA\nReg. No: 24BCE7012"
    sig_tbl.rows[1].cells[0].paragraphs[0].text = "SATYA TANMAYI PEMMADI\nReg. No: 24BCA7375"
    sig_tbl.rows[1].cells[1].paragraphs[0].text = "TANUJ KRISHNA AGGARWAL\nReg. No: 24BCA7536"
    sig_tbl.rows[2].cells[0].paragraphs[0].text = "RAJJEET SAHA\nReg. No: 24BCE7101"
    sig_tbl.rows[2].cells[1].paragraphs[0].text = "ANSHIKA SINGH\nReg. No: 23BCE7284"
    for r in sig_tbl.rows:
        for c in r.cells:
            for p in c.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.line_spacing = 1.15
                for run in p.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(10)
                    run.font.bold = True

    doc.add_page_break()

    # ── 3. CERTIFICATE ────────────────────────────────────────────────────────
    add_h1(doc, "CERTIFICATE")
    cert_text = (
        "This is to certify that the Senior Design Project report titled \"ArchOpt: A Contract-Driven Graph Learning "
        "and Multi-Objective Optimization Framework for AI-Assisted Campus Layout Planning\" submitted by "
        "Divya Jyoty (23BCE20341), Bakaraju Krishna Teja (24BCE7012), Satya Tanmayi Pemmadi (24BCA7375), "
        "Tanuj Krishna Aggarwal (24BCA7536), Rajjeet Saha (24BCE7101), and Anshika Singh (23BCE7284) in "
        "partial fulfillment of the requirements for the award of the degree of Bachelor of Technology "
        "in Computer Science and Engineering from Vellore Institute of Technology (VIT-AP University), Amaravati, "
        "is a verified record of bona fide work carried out under my supervision and guidance during the academic "
        "year 2025–2026."
    )
    add_p(doc, cert_text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=11.5, after=30)

    cert_tbl = doc.add_table(rows=2, cols=2)
    cert_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r in cert_tbl.rows:
        for c in r.cells:
            c.width = Inches(3.1)
    cert_tbl.rows[0].cells[0].paragraphs[0].text = "Project Guide\nDepartment of CSE, SCOPE\nVIT-AP University"
    cert_tbl.rows[0].cells[1].paragraphs[0].text = "Head of the Department\nDepartment of CSE, SCOPE\nVIT-AP University"
    cert_tbl.rows[1].cells[0].paragraphs[0].text = "\nInternal Examiner\nVIT-AP University"
    cert_tbl.rows[1].cells[1].paragraphs[0].text = "\nExternal Examiner\nVIT-AP University"
    for r in cert_tbl.rows:
        for c in r.cells:
            for p in c.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.line_spacing = 1.15
                for run in p.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(10)
                    run.font.bold = True

    add_p(doc, "Approved by:", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, bold=True, space_before=18, after=4)
    add_p(doc, "DEAN\nSchool of Computer Science and Engineering (SCOPE)\nVIT-AP University, Amaravati", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, bold=True)

    doc.add_page_break()

    # ── 4. ABSTRACT ───────────────────────────────────────────────────────────
    add_h1(doc, "ABSTRACT")
    abstract_p1 = (
        "Master planning of institutional university campuses is a complex, multi-objective spatial layout problem "
        "requiring concurrent satisfaction of regulatory boundary setbacks, building program requirements, functional "
        "zoning, accessibility constraints, and environmental performance objectives. Traditional computational architectural "
        "tools rely on reactive manual drafting or isolated geometric heuristics that fail to capture the rich topological "
        "and relational dependencies of large-scale campus sites. This project presents ArchOpt, an end-to-end, contract-governed "
        "software and machine learning framework for automated, AI-assisted campus master planning."
    )
    abstract_p2 = (
        "ArchOpt formalizes planning as a sequence of contract-bounded transformations: (i) parsing tabular requirements "
        "into a typed topological graph with 20-dimensional node features and 9-dimensional edge features; (ii) generating "
        "feasible, non-overlapping 2D layout candidates with an edge-conditioned message-passing graph neural network (GNN) "
        "and differentiable boundary projection guaranteeing 100% boundary compliance; (iii) evaluating and Pareto-ranking "
        "candidates across land utilization, green space ratio, parking adequacy, entrance accessibility, and road network "
        "efficiency using NSGA-II with crowding distance tournament selection; (iv) orchestrating persistence and asynchronous "
        "jobs through FastAPI and PostgreSQL; (v) providing interactive 2D canvas inspection and radar-chart analytics through "
        "a React 19 application; and (vi) exporting production-grade Contract 9 Blueprints to Blender 5.2.1 LTS for headless "
        "procedural 3D generation."
    )
    abstract_p3 = (
        "Empirical evaluation across five benchmark scenarios (Small, Medium MVP, Large, High-Density, and Constraint-Heavy) "
        "demonstrates that the trained GNN candidate generator achieves a 62.0% feasibility rate in Small Campuses and 16.0% in "
        "Medium Campuses, significantly outperforming uniform random placement (6.0% and 0.0%, respectively). NSGA-II elite "
        "filtering ensures that 100% of the returned Top-5 layouts for Small and Medium campuses achieve full constraint feasibility, "
        "delivering up to an +11.09% improvement in entrance accessibility scores and a +3.25% improvement in road network efficiency. "
        "Component benchmarking over 10 repeated runs reveals a mean end-to-end generation latency of 177.32 ms (with pure NumPy "
        "forward pass executing in 13.38 ms), establishing the system's operational viability for real-time interactive decision "
        "support in institutional architectural master planning."
    )
    add_p(doc, abstract_p1, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=11, after=8)
    add_p(doc, abstract_p2, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=11, after=8)
    add_p(doc, abstract_p3, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=11, after=14)

    p_kw = add_p(doc, "Keywords: ", align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=11, bold=True, after=10)
    r_kw = p_kw.add_run("Campus Master Planning, Graph Neural Networks (GNN), Edge-Conditioned Convolution, Multi-Objective Evolutionary Optimization, NSGA-II, Pareto Front, Spatial Constraints, Procedural 3D Modeling, Blender Automation.")
    r_kw.font.name = "Times New Roman"
    r_kw.font.size = Pt(11)
    r_kw.italic = True

    doc.add_page_break()

    # ── 5. ACKNOWLEDGEMENT & AUTHOR CONTRIBUTIONS ─────────────────────────────
    add_h1(doc, "ACKNOWLEDGEMENT")
    ack_text1 = (
        "We express our profound sense of gratitude and respect to our project guide, faculty mentors, and academic advisors "
        "at the School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology (VIT-AP University), "
        "Amaravati, for their invaluable guidance, constant technical encouragement, and insightful feedback throughout the duration "
        "of this capstone project. Their rigorous academic expectations and deep expertise in artificial intelligence, "
        "software engineering, and spatial optimization have been instrumental in shaping the architecture and experimental rigor of ArchOpt."
    )
    ack_text2 = (
        "We extend our sincere thanks to the Honorable Chancellor Dr. G. Viswanathan, Vice-President Dr. Sekar Viswanathan, "
        "and the executive leadership of VIT-AP University for providing state-of-the-art infrastructural facilities, "
        "high-performance computational environments, and academic ecosystems conducive to innovative engineering research.\n\n"
        "We are also grateful to the Dean, School of Computer Science and Engineering (SCOPE), the Program Chair, and all faculty "
        "members of SCOPE for their constructive critiques during milestone evaluation reviews and for fostering an environment "
        "of academic excellence.\n\n"
        "Finally, we express our heartfelt indebtedness to our parents and families for their unconditional moral support, "
        "patience, and sacrifices, and to our peers whose collaborative discussions enriched this endeavor."
    )
    add_p(doc, ack_text1, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=11.5, after=10)
    add_p(doc, ack_text2, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=11.5, after=16)

    # Subsystem Ownership & Author Contributions Table
    add_h2(doc, "Author Contributions and Subsystem Ownership Matrix")
    add_p(doc, "In accordance with collaborative engineering governance and academic rigor, individual author contributions and subsystem ownership are formally allocated as follows:",
          align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=11, after=8)

    contrib_data = [
        ("Divya Jyoty (23BCE20341)", "P3: Optimization Engine", "Multi-objective spatial optimization, geometric constraint validation (8 discrete rules), physics evaluators, and NSGA-II solver."),
        ("Bakaraju Krishna Teja (24BCE7012)", "P4: Backend & Orchestration", "Backend architecture, FastAPI RESTful service, PostgreSQL relational schemas, Alembic migrations, orchestration, and blueprint compilation."),
        ("Satya Tanmayi Pemmadi (24BCA7375)", "P2: Deep Learning Inference", "Deep learning architecture, Edge-GNN message-passing encoder, stochastic layout decoder, composite loss formulation, and inference engine."),
        ("Tanuj Krishna Aggarwal (24BCA7536)", "P5: Interactive Frontend Client", "Frontend web architecture, React 19 / Vite application, intake configuration forms, HTML5 canvas 2D rendering, and metrics inspection."),
        ("Rajjeet Saha (24BCE7101)", "P6: Procedural 3D Visualization", "Procedural 3D generation, architectural facade synthesis, circulation networks, lighting, and version-tolerant Blender 5.2.1 LTS integration."),
        ("Anshika Singh (23BCE7284)", "P1: Campus Graph Builder", "Dataset architecture, campus graph construction, feature encoding (20-D node / 9-D edge), and Contract 5 schema validation.")
    ]

    tbl_contrib = doc.add_table(rows=len(contrib_data) + 1, cols=3)
    tbl_contrib.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_w = [1.8, 1.8, 3.4]
    headers_c = ["Team Member", "Subsystem Ownership", "Core Engineering Contributions"]
    for j, h in enumerate(headers_c):
        tbl_contrib.rows[0].cells[j].paragraphs[0].text = h
    for i, row in enumerate(contrib_data):
        for j, val in enumerate(row):
            tbl_contrib.rows[i + 1].cells[j].paragraphs[0].text = val
    format_table_headers(tbl_contrib, c_w)

    add_p(doc, "Table 0.1: Subsystem Ownership and Individual Author Contributions",
          align=WD_ALIGN_PARAGRAPH.CENTER, size=10, bold=True, space_before=4, after=14)

    add_p(doc, "Place: Amaravati, Andhra Pradesh", align=WD_ALIGN_PARAGRAPH.LEFT, size=11, bold=True, after=4)
    add_p(doc, "Date:  04-11-2026", align=WD_ALIGN_PARAGRAPH.LEFT, size=11, bold=True, after=10)
    add_p(doc, "Divya Jyoty — 23BCE20341\nBakaraju Krishna Teja — 24BCE7012\nSatya Tanmayi Pemmadi — 24BCA7375\nTanuj Krishna Aggarwal — 24BCA7536\nRajjeet Saha — 24BCE7101\nAnshika Singh — 23BCE7284",
          align=WD_ALIGN_PARAGRAPH.LEFT, size=10.5, bold=True, after=10)

    doc.add_page_break()

    # ── 6. TABLE OF CONTENTS ──────────────────────────────────────────────────
    add_h1(doc, "TABLE OF CONTENTS")
    toc_items = [
        ("DECLARATION", "", "ii"),
        ("CERTIFICATE", "", "iii"),
        ("ABSTRACT", "", "iv"),
        ("ACKNOWLEDGEMENT", "", "v"),
        ("LIST OF FIGURES", "", "vii"),
        ("LIST OF TABLES", "", "viii"),
        ("LIST OF ABBREVIATIONS", "", "ix"),
        ("CHAPTER 1: INTRODUCTION", "1", "1"),
        ("1.1 Background and Motivation", "1.1", "1"),
        ("1.2 Problem Statement", "1.2", "3"),
        ("1.3 Objectives", "1.3", "4"),
        ("1.4 Scope and Delimitations of the Project", "1.4", "5"),
        ("1.5 Organization of the Report", "1.5", "6"),
        ("CHAPTER 2: LITERATURE REVIEW", "2", "7"),
        ("2.1 Computational Architectural Design Foundations", "2.1", "7"),
        ("2.2 Graph-Based Spatial Representations and GNN Layout Generators", "2.2", "9"),
        ("2.3 Multi-Objective Evolutionary Optimization & NSGA-II", "2.3", "11"),
        ("2.4 Spatial Constraint Validation & Computational Geometry", "2.4", "13"),
        ("2.5 Procedural 3D Modeling and CAD Automation", "2.5", "15"),
        ("2.6 Comparative Analysis of Existing Methodologies", "2.6", "16"),
        ("2.7 Research Gap and Technical Contributions of ArchOpt", "2.7", "18"),
        ("CHAPTER 3: SYSTEM REQUIREMENTS AND ANALYSIS", "3", "20"),
        ("3.1 Functional Requirements", "3.1", "20"),
        ("3.2 Non-Functional Requirements", "3.2", "22"),
        ("3.3 Dataset, Input Schema, and Topological Graph Representation", "3.3", "24"),
        ("3.4 Technology Stack and Dependency Specifications", "3.4", "26"),
        ("3.5 System Feasibility Study (Technical, Operational, Economic)", "3.5", "28"),
        ("3.6 System Use Cases and Actor Interactions", "3.6", "30"),
        ("CHAPTER 4: SYSTEM DESIGN AND ARCHITECTURE", "4", "32"),
        ("4.1 High-Level Microservice System Architecture", "4.1", "32"),
        ("4.2 Subsystem Decomposition and Workstream Allocation", "4.2", "34"),
        ("4.3 Mathematical Formulation of Campus Graph Topology", "4.3", "36"),
        ("4.4 Graph Neural Network Generative Architecture", "4.4", "39"),
        ("4.5 Multi-Objective NSGA-II Optimization Engine", "4.5", "42"),
        ("4.6 Backend Subsystem and Relational Database Schema", "4.6", "46"),
        ("4.7 Frontend Planning Interface and Interactive 2D Canvas", "4.7", "49"),
        ("4.8 Procedural 3D Visualization Pipeline (Blender Integration)", "4.8", "51"),
        ("4.9 Data Flow and Sequence Diagrams", "4.9", "53"),
        ("CHAPTER 5: SYSTEM IMPLEMENTATION", "5", "56"),
        ("5.1 Development Environment and Pipeline Setup", "5.1", "56"),
        ("5.2 Campus Graph Builder Implementation (`ml.dataset.graph_builder`)", "5.2", "58"),
        ("5.3 GNN Model & Inference Pipeline Implementation (`ml.models`, `ml.inference`)", "5.3", "61"),
        ("5.4 Spatial Constraint Engine Implementation (`optimization.constraints`)", "5.4", "64"),
        ("5.5 Multi-Objective NSGA-II Optimizer Implementation (`optimization.optimizer`)", "5.5", "68"),
        ("5.6 FastAPI REST Backend Implementation (`backend`)", "5.6", "72"),
        ("5.7 React 2D Campus Planning UI Implementation (`frontend`)", "5.7", "76"),
        ("5.8 Blender 3D Procedural Campus Generation (`blender`)", "5.8", "79"),
        ("5.9 Cross-Module Integration Contracts & Data Serialization", "5.9", "82"),
        ("5.10 Pipeline Execution Modes: Mock Mode vs Real Mode", "5.10", "84"),
        ("CHAPTER 6: EXPERIMENTAL RESULTS AND DISCUSSION", "6", "86"),
        ("6.1 Experimental Setup and Platform Specifications", "6.1", "86"),
        ("6.2 Test Scenarios Specification (Scenarios 1 to 5)", "6.2", "88"),
        ("6.3 Candidate Generation Evaluation (Yield, Validity, Latency)", "6.3", "91"),
        ("6.4 Spatial Constraint Satisfaction Evaluation", "6.4", "94"),
        ("6.5 Multi-Objective Optimization Progression (Initial vs Top-5 Pareto)", "6.5", "97"),
        ("6.6 NSGA-II Algorithmic Performance Evaluation (Convergence, Diversity)", "6.6", "101"),
        ("6.7 GNN Model and Inference Diagnostics (PyTorch vs NumPy)", "6.7", "105"),
        ("6.8 System Interface, Screenshots, and Contract 9 Blueprints", "6.8", "108"),
        ("6.9 Procedural 3D Rendering & Blender Integration Evaluation", "6.9", "111"),
        ("6.10 System Latency Benchmarks (10 Repeated Runs)", "6.10", "113"),
        ("6.11 Results Interpretation and In-Depth Discussion", "6.11", "116"),
        ("6.12 Limitations, Boundary Conditions, and Failure Modes", "6.12", "119"),
        ("CHAPTER 7: CONCLUSION AND FUTURE WORK", "7", "121"),
        ("7.1 Conclusion", "7.1", "121"),
        ("7.2 Future Work", "7.2", "123"),
        ("REFERENCES", "", "125"),
        ("APPENDICES", "", "130"),
    ]

    toc_tbl = doc.add_table(rows=len(toc_items), cols=2)
    toc_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r in toc_tbl.rows:
        r.cells[0].width = Inches(5.5)
        r.cells[1].width = Inches(0.8)

    for i, (item, num, page) in enumerate(toc_items):
        c0 = toc_tbl.rows[i].cells[0]
        c1 = toc_tbl.rows[i].cells[1]
        set_cell_margins(c0, top=40, bottom=40, left=60, right=60)
        set_cell_margins(c1, top=40, bottom=40, left=60, right=60)
        p0 = c0.paragraphs[0]
        p1 = c1.paragraphs[0]
        p0.paragraph_format.line_spacing = 1.15
        p1.paragraph_format.line_spacing = 1.15
        p0.paragraph_format.space_before = Pt(0)
        p0.paragraph_format.space_after = Pt(0)
        p1.paragraph_format.space_before = Pt(0)
        p1.paragraph_format.space_after = Pt(0)
        p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        is_ch = item.startswith("CHAPTER") or item in ["DECLARATION", "CERTIFICATE", "ABSTRACT", "ACKNOWLEDGEMENT", "REFERENCES", "APPENDICES"]
        r0 = p0.add_run(item)
        r1 = p1.add_run(page)
        r0.font.name = "Times New Roman"
        r1.font.name = "Times New Roman"
        r0.font.size = Pt(10 if not is_ch else 10.5)
        r1.font.size = Pt(10 if not is_ch else 10.5)
        if is_ch:
            r0.bold = True
            r1.bold = True
            if item.startswith("CHAPTER"):
                r0.font.color.rgb = RGBColor(0, 0, 0)
                r1.font.color.rgb = RGBColor(0, 0, 0)

    doc.add_page_break()

    # ── 7. LIST OF FIGURES ────────────────────────────────────────────────────
    add_h1(doc, "LIST OF FIGURES")
    lof_items = [
        ("Figure 1.1", "ArchOpt End-to-End System Architecture and Multi-Module Flow", "33"),
        ("Figure 4.1", "Topological Campus Graph Representation and Spatial Constraint Edges", "38"),
        ("Figure 4.2", "Graph Neural Network Architecture (GNN Encoder & Spatial Layout Decoder)", "41"),
        ("Figure 4.3", "NSGA-II Multi-Objective Optimization and Pareto Ranking Workflow", "45"),
        ("Figure 4.4", "PostgreSQL Relational Database Schema and Contract Tables (Alembic Head)", "48"),
        ("Figure 6.1", "Candidate Population Feasibility Rate across 5 Test Scenarios (GNN vs Baselines)", "92"),
        ("Figure 6.2", "GNN Candidate Spatial Constraint Violation Breakdown Across 5 Categories", "95"),
        ("Figure 6.3", "Objective Metrics Before vs After NSGA-II Optimization (MVP Benchmark Campus)", "98"),
        ("Figure 6.4", "NSGA-II Generational Convergence over 25 Evolutionary Generations", "102"),
        ("Figure 6.5", "Pareto Front Distribution: Accessibility Score vs Road Efficiency Score", "104"),
        ("Figure 6.6", "Module-wise Latency Benchmarks (Mean ± Std over 10 Repeated Runs)", "114"),
        ("Figure 6.7", "Spatial Layout Visualizations: Pareto Rank 1 vs Rank 5 Candidate Blueprints", "115"),
    ]
    lof_tbl = doc.add_table(rows=len(lof_items), cols=3)
    lof_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r in lof_tbl.rows:
        r.cells[0].width = Inches(1.3)
        r.cells[1].width = Inches(4.3)
        r.cells[2].width = Inches(0.7)
    for i, (f_num, f_desc, f_page) in enumerate(lof_items):
        c0, c1, c2 = lof_tbl.rows[i].cells
        set_cell_margins(c0, 40, 40, 60, 60)
        set_cell_margins(c1, 40, 40, 60, 60)
        set_cell_margins(c2, 40, 40, 60, 60)
        p0, p1, p2 = c0.paragraphs[0], c1.paragraphs[0], c2.paragraphs[0]
        p0.paragraph_format.line_spacing = p1.paragraph_format.line_spacing = p2.paragraph_format.line_spacing = 1.15
        p0.paragraph_format.space_before = p1.paragraph_format.space_before = p2.paragraph_format.space_before = Pt(0)
        p0.paragraph_format.space_after = p1.paragraph_format.space_after = p2.paragraph_format.space_after = Pt(0)
        p2.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        r0 = p0.add_run(f_num)
        r1 = p1.add_run(f_desc)
        r2 = p2.add_run(f_page)
        for r in [r0, r1, r2]:
            r.font.name = "Times New Roman"
            r.font.size = Pt(10)
        r0.bold = True

    doc.add_page_break()

    # ── 8. LIST OF TABLES ─────────────────────────────────────────────────────
    add_h1(doc, "LIST OF TABLES")
    lot_items = [
        ("Table 2.1", "Comparative Synthesis of Architectural Layout Generation and Optimization Literature", "17"),
        ("Table 3.1", "Comprehensive Hardware Specifications and Environmental Platform Constraints", "27"),
        ("Table 3.2", "Software Versions, ML Frameworks, and Architectural Libraries Registry", "28"),
        ("Table 4.1", "ArchOpt Subsystem Decomposition and Team Workstream Allocation Matrix", "35"),
        ("Table 4.2", "Input Node Feature Vector Specifications ([N, 20] Encodings)", "37"),
        ("Table 4.3", "Input Edge Feature Vector Specifications ([E, 9] Encodings)", "38"),
        ("Table 4.4", "Mathematical Multi-Objective Optimization Formulation (5 Objective Functions)", "44"),
        ("Table 4.5", "Master REST API Contract Specification Matrix (17 Endpoints)", "47"),
        ("Table 6.1", "Benchmark Campus Test Scenarios Parameter Matrix (Scenarios 1 to 5)", "89"),
        ("Table 6.2", "Candidate Generation Feasibility and Population Yield Comparison", "92"),
        ("Table 6.3", "Spatial Constraint Violations Breakdown per 100 Candidates (GNN vs Random)", "95"),
        ("Table 6.4", "Objective Metrics Progression Before vs After NSGA-II Optimization", "99"),
        ("Table 6.5", "System Performance and Execution Latency Benchmarks (10 Repeated Runs)", "114"),
    ]
    lot_tbl = doc.add_table(rows=len(lot_items), cols=3)
    lot_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r in lot_tbl.rows:
        r.cells[0].width = Inches(1.3)
        r.cells[1].width = Inches(4.3)
        r.cells[2].width = Inches(0.7)
    for i, (t_num, t_desc, t_page) in enumerate(lot_items):
        c0, c1, c2 = lot_tbl.rows[i].cells
        set_cell_margins(c0, 40, 40, 60, 60)
        set_cell_margins(c1, 40, 40, 60, 60)
        set_cell_margins(c2, 40, 40, 60, 60)
        p0, p1, p2 = c0.paragraphs[0], c1.paragraphs[0], c2.paragraphs[0]
        p0.paragraph_format.line_spacing = p1.paragraph_format.line_spacing = p2.paragraph_format.line_spacing = 1.15
        p0.paragraph_format.space_before = p1.paragraph_format.space_before = p2.paragraph_format.space_before = Pt(0)
        p0.paragraph_format.space_after = p1.paragraph_format.space_after = p2.paragraph_format.space_after = Pt(0)
        p2.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        r0 = p0.add_run(t_num)
        r1 = p1.add_run(t_desc)
        r2 = p2.add_run(t_page)
        for r in [r0, r1, r2]:
            r.font.name = "Times New Roman"
            r.font.size = Pt(10)
        r0.bold = True

    doc.add_page_break()

    # ── 9. LIST OF ABBREVIATIONS ──────────────────────────────────────────────
    add_h1(doc, "LIST OF ABBREVIATIONS")
    abbrs = [
        ("AABB", "Axis-Aligned Bounding Box"),
        ("AI", "Artificial Intelligence"),
        ("API", "Application Programming Interface"),
        ("Bcrypt", "Blowfish-based Password Hashing Algorithm"),
        ("CAD", "Computer-Aided Design"),
        ("CLI", "Command Line Interface"),
        ("CPU", "Central Processing Unit"),
        ("CSE", "Computer Science and Engineering"),
        ("DAG", "Directed Acyclic Graph"),
        ("DPI", "Dots Per Inch"),
        ("EEVEE", "Extra Easy Virtual Environment Engine (Blender)"),
        ("ER", "Entity-Relationship"),
        ("FastAPI", "High-Performance Modern Web Framework for Building APIs with Python"),
        ("GD", "Generational Distance"),
        ("GNN", "Graph Neural Network"),
        ("GPU", "Graphics Processing Unit"),
        ("GQL", "Graph Query Language"),
        ("HV", "Hypervolume Metric"),
        ("IEEE", "Institute of Electrical and Electronics Engineers"),
        ("JSON", "JavaScript Object Notation"),
        ("JSONB", "Binary JavaScript Object Notation (PostgreSQL)"),
        ("JWT", "JSON Web Token"),
        ("ML", "Machine Learning"),
        ("MST", "Minimum Spanning Tree"),
        ("NPZ", "NumPy Zipped Archive Format"),
        ("NSGA-II", "Non-Dominated Sorting Genetic Algorithm II"),
        ("ORM", "Object-Relational Mapping"),
        ("P1–P6", "Person 1 to Person 6 (Engineering Subsystem Owners)"),
        ("Pydantic", "Data Validation and Settings Management Library for Python"),
        ("RBF", "Radial Basis Function"),
        ("REST", "Representational State Transfer"),
        ("RSS", "Resident Set Size"),
        ("SBX", "Simulated Binary Crossover"),
        ("SCSE", "School of Computer Science and Engineering"),
        ("SPA", "Single Page Application"),
        ("SQL", "Structured Query Language"),
        ("SVG", "Scalable Vector Graphics"),
        ("TS", "TypeScript"),
        ("UI", "User Interface"),
        ("URI", "Uniform Resource Identifier"),
        ("VIT-AP", "Vellore Institute of Technology, Amaravathi"),
    ]
    abbr_tbl = doc.add_table(rows=len(abbrs), cols=2)
    abbr_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r in abbr_tbl.rows:
        r.cells[0].width = Inches(1.8)
        r.cells[1].width = Inches(4.5)
    for i, (ab, full) in enumerate(abbrs):
        c0, c1 = abbr_tbl.rows[i].cells
        set_cell_margins(c0, 30, 30, 50, 50)
        set_cell_margins(c1, 30, 30, 50, 50)
        p0, p1 = c0.paragraphs[0], c1.paragraphs[0]
        p0.paragraph_format.line_spacing = p1.paragraph_format.line_spacing = 1.15
        p0.paragraph_format.space_before = p1.paragraph_format.space_before = Pt(0)
        p0.paragraph_format.space_after = p1.paragraph_format.space_after = Pt(0)

        r0 = p0.add_run(ab)
        r1 = p1.add_run(full)
        r0.font.name = r1.font.name = "Times New Roman"
        r0.font.size = r1.font.size = Pt(9.5)
        r0.bold = True

    doc.add_page_break()


if __name__ == "__main__":
    print("[PRELIMINARY PAGES MODULE READY]")


# ==============================================================================
# MAIN COMPILATION SCRIPT
# ==============================================================================

def generate_complete_project_report():
    print("=" * 70)
    print("  COMPILING MASTER ARCHOPT ACADEMIC PROJECT REPORT (.DOCX)")
    print("=" * 70)

    # 1. Initialize Document
    doc = docx.Document()

    # 2. Configure Page Setup (A4, Academic Margins, Running Header & Footer)
    # Configure document settings: prevent expanding soft returns and enable auto-hyphenation
    try:
        settings_elm = doc.settings.element
        compat = settings_elm.find(qn('w:compat'))
        if compat is not None:
            compat.append(parse_xml(f'<w:doNotExpandShiftReturn {nsdecls("w")}/>'))
        settings_elm.append(parse_xml(f'<w:autoHyphenation {nsdecls("w")} w:val="true"/>'))
        settings_elm.append(parse_xml(f'<w:doNotHyphenateCaps {nsdecls("w")} w:val="true"/>'))
        settings_elm.append(parse_xml(f'<w:hyphenationZone {nsdecls("w")} w:val="360"/>'))
    except Exception as e:
        print(f"Warning setting doc hyphenation: {e}")
    for section in doc.sections:
        section.page_width = Inches(8.268)
        section.page_height = Inches(11.693)
        section.left_margin = Inches(1.25)
        section.right_margin = Inches(1.0)
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.different_first_page_header_footer = True

        # Formal Academic Page Border (single solid 1pt black line, 24pt from edge)
        sectPr = section._sectPr
        for child in list(sectPr):
            if child.tag.endswith('pgBorders'):
                sectPr.remove(child)

        pgBorders = parse_xml(
            f'<w:pgBorders {nsdecls("w")} w:offsetFrom="page">'
            f'<w:top w:val="single" w:sz="8" w:space="24" w:color="000000"/>'
            f'<w:left w:val="single" w:sz="8" w:space="24" w:color="000000"/>'
            f'<w:bottom w:val="single" w:sz="8" w:space="24" w:color="000000"/>'
            f'<w:right w:val="single" w:sz="8" w:space="24" w:color="000000"/>'
            f'</w:pgBorders>'
        )
        sectPr.append(pgBorders)

        # Running Header on page 2+
        header = section.header
        p_head = header.paragraphs[0]
        p_head.text = "ArchOpt: AI-Powered Campus Planning and Architectural Layout Optimization System"
        p_head.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_head.runs[0].font.name = "Times New Roman"
        p_head.runs[0].font.size = Pt(8.5)
        p_head.runs[0].font.italic = True
        p_head.runs[0].font.color.rgb = RGBColor(120, 144, 156)

        # Running Footer on page 2+
        footer = section.footer
        p_foot = footer.paragraphs[0]
        p_foot.paragraph_format.tab_stops.add_tab_stop(Inches(6.02), WD_TAB_ALIGNMENT.RIGHT)
        r1 = p_foot.add_run("School of Computer Science & Engineering (SCOPE), VIT-AP University")
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(8.5)
        r1.font.color.rgb = RGBColor(120, 144, 156)

        r2 = p_foot.add_run("\tPage ")
        r2.font.name = "Times New Roman"
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = RGBColor(120, 144, 156)

        fld = parse_xml(f'<w:fldSimple {nsdecls("w")} w:instr="PAGE"/>')
        p_foot._p.append(fld)

    # 3. Build Preliminary Pages
    print(">>> [1/5] Building Preliminary Pages (Title, Decl, Cert, Abstract, Ack, TOC, LOF, LOT)...")
    make_preliminary_pages(doc)

    # 4. Build Chapters 1 to 3
    print(">>> [2/5] Building Chapter 1 (Introduction), Chapter 2 (Literature Review), Chapter 3 (Analysis)...")
    from chapters_1_to_3 import build_chapter_1, build_chapter_2, build_chapter_3
    build_chapter_1(doc)
    build_chapter_2(doc)
    build_chapter_3(doc)

    # 5. Build Chapters 4 and 5
    print(">>> [3/5] Building Chapter 4 (Design & Architecture) and Chapter 5 (Implementation)...")
    from chapters_4_to_5 import build_chapter_4, build_chapter_5
    build_chapter_4(doc)
    build_chapter_5(doc)

    # 6. Build Chapters 6 and 7, References, and Appendices
    print(">>> [4/5] Building Chapter 6 (Results & Discussion), Chapter 7 (Conclusion), References, Appendices...")
    from chapters_6_to_7 import build_chapter_6, build_chapter_7, build_references_and_appendices
    build_chapter_6(doc)
    build_chapter_7(doc)
    build_references_and_appendices(doc)

    # 7. Save Document
    print(">>> [5/5] Saving compiled document to disk...")
    OUTPUT_DOCX.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUTPUT_DOCX))
    print(f"\n[SUCCESS] Final Report Generated: {OUTPUT_DOCX}")
    print(f"File size: {OUTPUT_DOCX.stat().st_size / (1024 * 1024):.2f} MB")
    print("=" * 70)


if __name__ == "__main__":
    generate_complete_project_report()
