"""
optimization/visualize.py
==========================
SVG and HTML renderer for ranked campus layouts.

Public API
----------
render_layout_svg(layout, requirements) -> str
    Returns an SVG string for a single RankedLayout.

render_comparison_html(layouts, requirements) -> str
    Returns a full HTML page with tabbed comparison of multiple layouts.

Design
------
  • Buildings colored by zone:
      academic    → #3B82F6 (blue)
      residential → #F97316 (orange)
      admin       → #8B5CF6 (purple)
      sports      → #10B981 (green)
      library     → #06B6D4 (teal)
      parking     → #94A3B8 (slate gray, hatched)
      default     → #64748B (gray)

  • Green area shaded #22C55E / 0.15 opacity over unbuilt space
  • Entrances shown as red arrows at site edge
  • Constraint violations outlined red with dotted border
  • Metrics legend panel on the right
  • Rank badge in top-left corner

Coordinate mapping
------------------
  Campus coords (x=east, y=north, origin=bottom-left)
  → SVG coords (x=right, y=DOWN, origin=top-left)

  svg_x = margin + campus_x * scale
  svg_y = margin + (site_height - campus_y - building_depth) * scale
"""
from __future__ import annotations

import math
from typing import List, Optional

from optimization.contracts import (
    CandidateBuilding,
    CampusRequirements,
    RankedLayout,
)


# ── Design tokens ─────────────────────────────────────────────────────────────

ZONE_COLORS = {
    "academic":    "#3B82F6",
    "residential": "#F97316",
    "admin":       "#8B5CF6",
    "sports":      "#10B981",
    "library":     "#06B6D4",
    "parking":     "#94A3B8",
    "default":     "#64748B",
}

ZONE_STROKE = {
    "academic":    "#1D4ED8",
    "residential": "#C2410C",
    "admin":       "#6D28D9",
    "sports":      "#047857",
    "library":     "#0E7490",
    "parking":     "#475569",
    "default":     "#334155",
}

ZONE_LABELS = {
    "academic":    "Academic",
    "residential": "Residential",
    "admin":       "Admin",
    "sports":      "Sports",
    "library":     "Library",
    "parking":     "Parking",
}

CANVAS_W = 560
CANVAS_H = 560
MARGIN = 30
LEGEND_W = 200
TOTAL_W = CANVAS_W + LEGEND_W
TOTAL_H = CANVAS_H + 60  # extra bottom for title


# ── Coordinate helpers ────────────────────────────────────────────────────────

def _scale(site_w: float, site_h: float) -> float:
    """Pixels per metre."""
    return min(
        (CANVAS_W - 2 * MARGIN) / site_w,
        (CANVAS_H - 2 * MARGIN) / site_h,
    )


def _to_svg_xy(
    campus_x: float,
    campus_y: float,
    site_h: float,
    scale: float,
) -> tuple:
    """Convert campus (x, y) to SVG pixel coords (y-axis flipped)."""
    svg_x = MARGIN + campus_x * scale
    svg_y = MARGIN + (site_h - campus_y) * scale
    return svg_x, svg_y


def _building_svg_rect(
    b: CandidateBuilding,
    site_h: float,
    scale: float,
    fill: str,
    stroke: str,
    stroke_dash: str = "",
    opacity: float = 0.85,
) -> str:
    """Return SVG for one building as a rotated rectangle + label."""
    w_px = b.width * scale
    d_px = b.depth * scale

    # Centre in campus coords
    cx = b.x + b.width / 2.0
    cy = b.y + b.depth / 2.0

    # Centre in SVG coords
    svg_cx, svg_cy = _to_svg_xy(cx, cy, site_h, scale)

    # SVG rotation: campus CCW → SVG CW (y-flip)
    svg_rot = -b.rotation

    dash_attr = f'stroke-dasharray="{stroke_dash}"' if stroke_dash else ""

    # Building rectangle (centred at origin, then rotated)
    rect = (
        f'<g transform="translate({svg_cx:.1f},{svg_cy:.1f}) rotate({svg_rot:.1f})">'
        f'<rect x="{-w_px/2:.1f}" y="{-d_px/2:.1f}" '
        f'width="{w_px:.1f}" height="{d_px:.1f}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="1.5" '
        f'opacity="{opacity}" {dash_attr} rx="2"/>'
    )

    # Label (short name, clamped)
    label = b.name[:12] if b.name else f"B{b.building_id}"
    font_size = max(7, min(11, int(w_px / max(len(label), 1) * 1.4)))
    rect += (
        f'<text x="0" y="0" text-anchor="middle" dominant-baseline="middle" '
        f'font-size="{font_size}" font-family="Inter,sans-serif" '
        f'fill="white" font-weight="600" '
        f'style="pointer-events:none;">{label}</text>'
    )

    rect += "</g>"
    return rect


# ── Defs: hatch pattern for parking ──────────────────────────────────────────

def _defs() -> str:
    return """<defs>
  <pattern id="hatch-parking" patternUnits="userSpaceOnUse" width="8" height="8" patternTransform="rotate(45)">
    <line x1="0" y1="0" x2="0" y2="8" stroke="#475569" stroke-width="2" opacity="0.5"/>
  </pattern>
  <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
    <feDropShadow dx="0" dy="1" stdDeviation="2" flood-opacity="0.18"/>
  </filter>
</defs>"""


# ── Main SVG renderer ─────────────────────────────────────────────────────────

def render_layout_svg(
    layout: RankedLayout,
    requirements: CampusRequirements,
    width: int = TOTAL_W,
    height: int = TOTAL_H,
) -> str:
    """
    Render a single RankedLayout as an annotated SVG string.
    """
    sw = layout.site_width
    sh = layout.site_height
    scale = _scale(sw, sh)

    site_px_w = sw * scale
    site_px_h = sh * scale

    # Violation set for quick lookup
    violated_ids: set = set()
    if layout.validation:
        for v in layout.validation.violations:
            if v.severity == "hard":
                for bid in v.building_ids:
                    violated_ids.add(bid)

    svg_parts: List[str] = []

    # ── SVG header ────────────────────────────────────────────────────────────
    svg_parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" '
        f'font-family="Inter,system-ui,sans-serif">'
    )
    svg_parts.append(_defs())

    # Background
    svg_parts.append(f'<rect width="{width}" height="{height}" fill="#0F172A"/>')

    # ── Site ground ───────────────────────────────────────────────────────────
    # Green base (unbuilt area as greenery)
    svg_parts.append(
        f'<rect x="{MARGIN}" y="{MARGIN}" '
        f'width="{site_px_w:.1f}" height="{site_px_h:.1f}" '
        f'fill="#16A34A" opacity="0.22" rx="4"/>'
    )
    # Site border
    svg_parts.append(
        f'<rect x="{MARGIN}" y="{MARGIN}" '
        f'width="{site_px_w:.1f}" height="{site_px_h:.1f}" '
        f'fill="none" stroke="#94A3B8" stroke-width="1.5" '
        f'stroke-dasharray="6,3" rx="4"/>'
    )

    # Grid lines (every 50m)
    grid_step = 50 * scale
    x = MARGIN
    while x <= MARGIN + site_px_w + 0.5:
        svg_parts.append(
            f'<line x1="{x:.1f}" y1="{MARGIN}" x2="{x:.1f}" '
            f'y2="{MARGIN + site_px_h:.1f}" stroke="#1E293B" stroke-width="0.5"/>'
        )
        # Scale label
        m_val = round((x - MARGIN) / scale)
        if m_val > 0:
            svg_parts.append(
                f'<text x="{x:.1f}" y="{MARGIN - 4}" text-anchor="middle" '
                f'font-size="8" fill="#475569">{m_val}m</text>'
            )
        x += grid_step

    y = MARGIN
    while y <= MARGIN + site_px_h + 0.5:
        svg_parts.append(
            f'<line x1="{MARGIN}" y1="{y:.1f}" '
            f'x2="{MARGIN + site_px_w:.1f}" y2="{y:.1f}" '
            f'stroke="#1E293B" stroke-width="0.5"/>'
        )
        m_val = round((MARGIN + site_px_h - y) / scale)
        if m_val > 0:
            svg_parts.append(
                f'<text x="{MARGIN - 4}" y="{y + 3:.1f}" text-anchor="end" '
                f'font-size="8" fill="#475569">{m_val}m</text>'
            )
        y += grid_step

    # ── Buildings ─────────────────────────────────────────────────────────────
    for b in layout.buildings:
        zone = b.zone or "default"
        is_parking = b.type in ("parking", "car_park") or zone == "parking"
        fill = "url(#hatch-parking)" if is_parking else ZONE_COLORS.get(zone, ZONE_COLORS["default"])
        stroke = ZONE_STROKE.get(zone, ZONE_STROKE["default"])
        stroke_dash = "4,3" if b.building_id in violated_ids else ""

        svg_parts.append(
            _building_svg_rect(b, sh, scale, fill, stroke, stroke_dash)
        )

        # Violation red glow
        if b.building_id in violated_ids:
            w_px = b.width * scale
            d_px = b.depth * scale
            cx = b.x + b.width / 2.0
            cy = b.y + b.depth / 2.0
            svg_cx, svg_cy = _to_svg_xy(cx, cy, sh, scale)
            svg_rot = -b.rotation
            svg_parts.append(
                f'<g transform="translate({svg_cx:.1f},{svg_cy:.1f}) rotate({svg_rot:.1f})">'
                f'<rect x="{-w_px/2 - 2:.1f}" y="{-d_px/2 - 2:.1f}" '
                f'width="{w_px + 4:.1f}" height="{d_px + 4:.1f}" '
                f'fill="none" stroke="#EF4444" stroke-width="2" '
                f'stroke-dasharray="4,2" opacity="0.9" rx="3"/>'
                f'</g>'
            )

    # ── Entrances ─────────────────────────────────────────────────────────────
    for ent in requirements.entrances:
        ex = ent.x + ent.width / 2.0
        ey = ent.y
        svg_ex, svg_ey = _to_svg_xy(ex, ey, sh, scale)
        # Arrow pointing inward (north)
        svg_parts.append(
            f'<polygon points="{svg_ex:.1f},{svg_ey - 14:.1f} '
            f'{svg_ex - 8:.1f},{svg_ey:.1f} '
            f'{svg_ex + 8:.1f},{svg_ey:.1f}" '
            f'fill="#F87171" opacity="0.9"/>'
        )
        svg_parts.append(
            f'<text x="{svg_ex:.1f}" y="{svg_ey + 10:.1f}" '
            f'text-anchor="middle" font-size="8" fill="#F87171">ENT</text>'
        )

    # ── Legend panel ──────────────────────────────────────────────────────────
    lx = CANVAS_W + 10
    ly = MARGIN

    # Panel background
    svg_parts.append(
        f'<rect x="{lx - 5}" y="{ly - 5}" '
        f'width="{LEGEND_W - 5}" height="{CANVAS_H - MARGIN + 5}" '
        f'fill="#1E293B" rx="8" opacity="0.95"/>'
    )

    # Rank badge
    rank_color = "#F59E0B" if layout.rank == 1 else "#64748B"
    rank_label = f"#{layout.rank}"
    svg_parts.append(
        f'<circle cx="{lx + 20}" cy="{ly + 20}" r="18" fill="{rank_color}" opacity="0.9"/>'
        f'<text x="{lx + 20}" y="{ly + 25}" text-anchor="middle" '
        f'font-size="14" font-weight="700" fill="white">{rank_label}</text>'
    )

    feasible_label = "FEASIBLE" if layout.feasible else "INFEASIBLE"
    feasible_color = "#22C55E" if layout.feasible else "#EF4444"
    svg_parts.append(
        f'<text x="{lx + 45}" y="{ly + 16}" font-size="10" font-weight="600" '
        f'fill="{feasible_color}">{feasible_label}</text>'
        f'<text x="{lx + 45}" y="{ly + 30}" font-size="9" fill="#94A3B8">'
        f'{layout.candidate_id}</text>'
    )

    # Metrics
    m = layout.metrics
    metrics = [
        ("Land Util",    m.land_utilization),
        ("Green Ratio",  m.green_ratio),
        ("Parking",      m.parking_ratio),
        ("Accessibility",m.accessibility_score),
        ("Road Effic.",  m.road_efficiency),
        ("Constraints",  m.constraint_score),
    ]
    metric_colors = ["#3B82F6", "#22C55E", "#94A3B8", "#F97316", "#A78BFA", "#06B6D4"]

    svg_parts.append(
        f'<text x="{lx}" y="{ly + 55}" font-size="10" font-weight="600" fill="#CBD5E1">Metrics</text>'
    )
    for idx, ((label, value), color) in enumerate(zip(metrics, metric_colors)):
        my = ly + 70 + idx * 32
        bar_w = int(value * (LEGEND_W - 30))

        # Label + value
        svg_parts.append(
            f'<text x="{lx}" y="{my}" font-size="9" fill="#94A3B8">{label}</text>'
            f'<text x="{lx + LEGEND_W - 22}" y="{my}" font-size="9" '
            f'fill="white" text-anchor="end">{value:.2f}</text>'
        )
        # Bar track
        svg_parts.append(
            f'<rect x="{lx}" y="{my + 4}" width="{LEGEND_W - 25}" height="8" '
            f'fill="#334155" rx="4"/>'
        )
        # Bar fill
        svg_parts.append(
            f'<rect x="{lx}" y="{my + 4}" width="{bar_w}" height="8" '
            f'fill="{color}" rx="4" opacity="0.85"/>'
        )

    # Zone legend
    zone_ly = ly + 70 + len(metrics) * 32 + 15
    svg_parts.append(
        f'<text x="{lx}" y="{zone_ly}" font-size="10" font-weight="600" fill="#CBD5E1">Zones</text>'
    )
    for zi, (zone, color) in enumerate(ZONE_COLORS.items()):
        if zone == "default":
            continue
        zy = zone_ly + 14 + zi * 16
        svg_parts.append(
            f'<rect x="{lx}" y="{zy - 8}" width="10" height="10" fill="{color}" rx="2"/>'
            f'<text x="{lx + 14}" y="{zy}" font-size="9" fill="#CBD5E1">'
            f'{ZONE_LABELS.get(zone, zone).capitalize()}</text>'
        )

    # Violations summary
    if layout.validation and layout.validation.violations:
        hard_count = sum(1 for v in layout.validation.violations if v.severity == "hard")
        soft_count = sum(1 for v in layout.validation.violations if v.severity == "soft")
        viol_ly = zone_ly + 14 + (len(ZONE_COLORS) - 1) * 16 + 10
        svg_parts.append(
            f'<text x="{lx}" y="{viol_ly}" font-size="10" font-weight="600" fill="#CBD5E1">Violations</text>'
        )
        if hard_count:
            svg_parts.append(
                f'<text x="{lx}" y="{viol_ly + 14}" font-size="9" fill="#EF4444">⬛ {hard_count} hard</text>'
            )
        if soft_count:
            svg_parts.append(
                f'<text x="{lx}" y="{viol_ly + 26}" font-size="9" fill="#F59E0B">⬛ {soft_count} soft</text>'
            )

    # ── Title bar ─────────────────────────────────────────────────────────────
    title_y = CANVAS_H + 20
    svg_parts.append(
        f'<text x="{MARGIN}" y="{title_y + 14}" font-size="13" font-weight="700" '
        f'fill="#E2E8F0">AI Campus Planner — Rank {layout.rank} Layout</text>'
    )
    svg_parts.append(
        f'<text x="{MARGIN}" y="{title_y + 28}" font-size="10" fill="#64748B">'
        f'Site: {layout.site_width:.0f}m × {layout.site_height:.0f}m  |  '
        f'{len(layout.buildings)} buildings  |  '
        f'Constraint score: {layout.metrics.constraint_score:.2f}</text>'
    )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


# ── HTML comparison renderer ──────────────────────────────────────────────────

def render_comparison_html(
    layouts: List[RankedLayout],
    requirements: CampusRequirements,
) -> str:
    """
    Render an interactive HTML page comparing multiple ranked layouts.
    Opens directly in a browser — no server required.
    """
    svgs = [render_layout_svg(rl, requirements) for rl in layouts]

    tab_buttons = ""
    for rl in layouts:
        feas_badge = "🟢" if rl.feasible else "🔴"
        tab_buttons += (
            f'<button class="tab-btn" onclick="showTab({rl.rank - 1})" '
            f'id="btn-{rl.rank - 1}">'
            f'{feas_badge} Rank #{rl.rank}'
            f'</button>\n'
        )

    svg_panels = ""
    for idx, (rl, svg) in enumerate(zip(layouts, svgs)):
        display = "block" if idx == 0 else "none"
        svg_panels += (
            f'<div class="tab-panel" id="panel-{idx}" style="display:{display}">'
            f'{svg}'
            f'</div>\n'
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Campus Planner — Layout Comparison</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'Inter', system-ui, sans-serif;
    background: #020617;
    color: #E2E8F0;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 32px 16px;
  }}

  .header {{
    text-align: center;
    margin-bottom: 32px;
  }}
  .header h1 {{
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #3B82F6, #8B5CF6, #06B6D4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 8px;
  }}
  .header p {{
    font-size: 0.9rem;
    color: #64748B;
  }}

  .tab-bar {{
    display: flex;
    gap: 8px;
    margin-bottom: 20px;
    flex-wrap: wrap;
    justify-content: center;
  }}

  .tab-btn {{
    background: #1E293B;
    border: 1px solid #334155;
    color: #94A3B8;
    padding: 8px 20px;
    border-radius: 8px;
    cursor: pointer;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 600;
    transition: all 0.2s;
  }}
  .tab-btn:hover {{
    background: #334155;
    color: #E2E8F0;
    border-color: #475569;
  }}
  .tab-btn.active {{
    background: linear-gradient(135deg, #3B82F6, #8B5CF6);
    border-color: transparent;
    color: white;
    box-shadow: 0 0 16px rgba(59,130,246,0.4);
  }}

  .tab-panel {{
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 25px 50px rgba(0,0,0,0.5);
    border: 1px solid #1E293B;
  }}

  .metrics-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    margin-top: 24px;
    width: 100%;
    max-width: {TOTAL_W}px;
  }}

  .metric-card {{
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    transition: transform 0.2s;
  }}
  .metric-card:hover {{
    transform: translateY(-2px);
    border-color: #475569;
  }}
  .metric-card .value {{
    font-size: 1.6rem;
    font-weight: 700;
    color: #3B82F6;
    margin-bottom: 4px;
  }}
  .metric-card .label {{
    font-size: 0.75rem;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}

  .footer {{
    margin-top: 40px;
    text-align: center;
    color: #334155;
    font-size: 0.75rem;
  }}
</style>
</head>
<body>

<div class="header">
  <h1>🏛 AI Campus Planner</h1>
  <p>Person 3 — Constraint &amp; NSGA-II Optimization Engine</p>
  <p style="margin-top:4px;color:#475569">
    Site: {requirements.site_width:.0f}m × {requirements.site_height:.0f}m &nbsp;|&nbsp;
    Top {len(layouts)} Pareto-ranked layouts
  </p>
</div>

<div class="tab-bar">
{tab_buttons}
</div>

{svg_panels}

<div class="metrics-grid" id="metrics-grid"></div>

<div class="footer">
  Generated by optimization/visualize.py &nbsp;·&nbsp; AI Campus Planner v0.1
</div>

<script>
const layouts = {_layouts_to_js(layouts)};

function showTab(idx) {{
  document.querySelectorAll('.tab-panel').forEach((p, i) => {{
    p.style.display = i === idx ? 'block' : 'none';
  }});
  document.querySelectorAll('.tab-btn').forEach((b, i) => {{
    b.classList.toggle('active', i === idx);
  }});
  updateMetrics(idx);
}}

function updateMetrics(idx) {{
  const rl = layouts[idx];
  const m = rl.metrics;
  const grid = document.getElementById('metrics-grid');
  const entries = [
    ['Land Utilization',  m.land_utilization,  '#3B82F6'],
    ['Green Ratio',       m.green_ratio,        '#22C55E'],
    ['Parking Ratio',     m.parking_ratio,      '#94A3B8'],
    ['Accessibility',     m.accessibility_score,'#F97316'],
    ['Road Efficiency',   m.road_efficiency,    '#A78BFA'],
    ['Constraint Score',  m.constraint_score,   '#06B6D4'],
  ];
  grid.innerHTML = entries.map(([label, val, color]) =>
    `<div class="metric-card">
      <div class="value" style="color:${{color}}">${{(val*100).toFixed(1)}}%</div>
      <div class="label">${{label}}</div>
    </div>`
  ).join('');
}}

// Activate first tab
showTab(0);
document.getElementById('btn-0').classList.add('active');
</script>
</body>
</html>"""
    return html


def _layouts_to_js(layouts: List[RankedLayout]) -> str:
    """Convert layouts to a JS array literal for the HTML page."""
    import json

    def rl_dict(rl: RankedLayout) -> dict:
        return {
            "rank": rl.rank,
            "candidateId": rl.candidate_id,
            "feasible": rl.feasible,
            "metrics": {
                "land_utilization": rl.metrics.land_utilization,
                "green_ratio": rl.metrics.green_ratio,
                "parking_ratio": rl.metrics.parking_ratio,
                "accessibility_score": rl.metrics.accessibility_score,
                "road_efficiency": rl.metrics.road_efficiency,
                "constraint_score": rl.metrics.constraint_score,
            },
        }

    return json.dumps([rl_dict(rl) for rl in layouts])
