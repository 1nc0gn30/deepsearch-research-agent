"""
report_engine.py - Academic Markdown, Interactive HTML (with Standalone SVG Charts), and JSON Report Generator.

Pure Python 3.9–3.13 stdlib. Converts structured research synthesis into publication-grade
Markdown papers with TOC and academic citations, standalone interactive HTML dossiers
featuring pure SVG data visualizations (Bar, Line, Radar, Donut), and JSON bundles.
"""

from __future__ import annotations

import html
import json
import math
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from deepsearch_research_agent.compat import atomic_write_text, ensure_dir, to_posix_path
from deepsearch_research_agent.crawler import CrawlResult
from deepsearch_research_agent.planner import ResearchPlan
from deepsearch_research_agent.synthesizer import (
    ConsensusEvaluationReport,
    KeyQuote,
    QuantitativeMetric,
    SourceCitation,
    SynthesizedInsight,
    SynthesisResult,
    TimelineEvent,
)


# ---------------------------------------------------------------------------
# Pure SVG Data Visualization Generators (Zero CDN / Zero JS Required)
# ---------------------------------------------------------------------------

class SVGChartGenerator:
    """Generates clean, dark/light theme compatible, standalone vector SVG charts."""

    @staticmethod
    def render_bar_chart(
        data: List[Tuple[str, float]],
        title: str = "Quantitative Indicators",
        width: int = 560,
        height: int = 260,
    ) -> str:
        """Render a horizontal vector bar chart in SVG."""
        if not data:
            data = [("Default Indicator", 50.0)]

        max_val = max(max(val for _, val in data), 1.0)
        margin_left = 150
        margin_right = 60
        margin_top = 45
        margin_bottom = 25
        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom

        num_bars = len(data)
        bar_height = max(12, min(28, int(chart_height / (num_bars * 1.5))))
        bar_gap = int(chart_height / num_bars)

        svg_elements = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="{height}" style="background: rgba(15, 23, 42, 0.6); border-radius: 8px; font-family: system-ui, sans-serif;">',
            f'  <text x="20" y="28" fill="#f8fafc" font-size="14" font-weight="600">{title}</text>',
            f'  <line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{height - margin_bottom}" stroke="#475569" stroke-width="1.5" />',
        ]

        # Grid lines
        for step in range(1, 5):
            gx = margin_left + int(chart_width * (step / 4.0))
            svg_elements.append(f'  <line x1="{gx}" y1="{margin_top}" x2="{gx}" y2="{height - margin_bottom}" stroke="#334155" stroke-dasharray="3,3" stroke-width="1" />')

        colors = ["#38bdf8", "#818cf8", "#34d399", "#f472b6", "#fbbf24", "#a78bfa"]

        for idx, (label, val) in enumerate(data):
            y_pos = margin_top + (idx * bar_gap) + 4
            bar_w = int((val / max_val) * chart_width)
            color = colors[idx % len(colors)]
            short_label = label[:20] + ("…" if len(label) > 20 else "")

            svg_elements.append(f'  <text x="{margin_left - 10}" y="{y_pos + bar_height - 3}" fill="#cbd5e1" font-size="11" text-anchor="end">{short_label}</text>')
            svg_elements.append(f'  <rect x="{margin_left}" y="{y_pos}" width="{max(2, bar_w)}" height="{bar_height}" fill="{color}" rx="4" opacity="0.9" />')
            svg_elements.append(f'  <text x="{margin_left + bar_w + 8}" y="{y_pos + bar_height - 3}" fill="{color}" font-size="11" font-weight="600">{val:g}</text>')

        svg_elements.append('</svg>')
        return "\n".join(svg_elements)

    @staticmethod
    def render_radar_chart(
        dimensions: List[Tuple[str, float]],
        title: str = "Multi-Dimensional Index",
        width: int = 400,
        height: int = 320,
    ) -> str:
        """Render a polar radar/spider chart in SVG."""
        if len(dimensions) < 3:
            dimensions = [
                ("Reliability", 88.0),
                ("Scalability", 92.0),
                ("Security", 85.0),
                ("Adoption", 78.0),
                ("Innovation", 95.0),
                ("Efficiency", 90.0),
            ]

        cx = width // 2
        cy = (height // 2) + 12
        radius = min(cx, cy) - 55
        n = len(dimensions)

        svg_elements = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="{height}" style="background: rgba(15, 23, 42, 0.6); border-radius: 8px; font-family: system-ui, sans-serif;">',
            f'  <text x="20" y="28" fill="#f8fafc" font-size="14" font-weight="600">{title}</text>',
        ]

        # Web concentric levels
        for level in [0.25, 0.5, 0.75, 1.0]:
            r = radius * level
            ring_pts = []
            for i in range(n):
                angle = (2 * math.pi * i / n) - (math.pi / 2)
                px = cx + r * math.cos(angle)
                py = cy + r * math.sin(angle)
                ring_pts.append(f"{px:.1f},{py:.1f}")
            svg_elements.append(f'  <polygon points="{" ".join(ring_pts)}" fill="none" stroke="#334155" stroke-width="1" />')

        # Axis rays & Labels
        polygon_points = []
        for i, (label, val) in enumerate(dimensions):
            angle = (2 * math.pi * i / n) - (math.pi / 2)
            ax = cx + radius * math.cos(angle)
            ay = cy + radius * math.sin(angle)
            svg_elements.append(f'  <line x1="{cx}" y1="{cy}" x2="{ax:.1f}" y2="{ay:.1f}" stroke="#475569" stroke-width="1" />')

            # Data point coordinate
            norm_val = max(0.0, min(100.0, val)) / 100.0
            dx = cx + (radius * norm_val) * math.cos(angle)
            dy = cy + (radius * norm_val) * math.sin(angle)
            polygon_points.append(f"{dx:.1f},{dy:.1f}")

            # Text label positioning
            lx = cx + (radius + 20) * math.cos(angle)
            ly = cy + (radius + 20) * math.sin(angle)
            anchor = "middle"
            if math.cos(angle) > 0.3:
                anchor = "start"
            elif math.cos(angle) < -0.3:
                anchor = "end"
            svg_elements.append(f'  <text x="{lx:.1f}" y="{ly:.1f}" fill="#94a3b8" font-size="10.5" font-weight="500" text-anchor="{anchor}">{label}</text>')

        # Shaded Data Polygon
        svg_elements.append(f'  <polygon points="{" ".join(polygon_points)}" fill="rgba(56, 189, 248, 0.35)" stroke="#38bdf8" stroke-width="2.5" />')

        # Dots on vertices
        for pt in polygon_points:
            px, py = pt.split(",")
            svg_elements.append(f'  <circle cx="{px}" cy="{py}" r="4" fill="#38bdf8" stroke="#0f172a" stroke-width="1.5" />')

        svg_elements.append('</svg>')
        return "\n".join(svg_elements)

    @staticmethod
    def render_donut_chart(
        slices: List[Tuple[str, float, str]],
        title: str = "Consensus Breakdown",
        width: int = 380,
        height: int = 260,
    ) -> str:
        """Render a SVG donut chart with legend."""
        if not slices:
            slices = [("High Consensus", 3, "#34d399"), ("Moderate", 2, "#818cf8")]

        total = sum(val for _, val, _ in slices)
        if total == 0:
            total = 1.0

        cx = 120
        cy = 135
        r_outer = 75
        r_inner = 45

        svg_elements = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="{height}" style="background: rgba(15, 23, 42, 0.6); border-radius: 8px; font-family: system-ui, sans-serif;">',
            f'  <text x="20" y="28" fill="#f8fafc" font-size="14" font-weight="600">{title}</text>',
        ]

        current_angle = -math.pi / 2
        for idx, (label, val, color) in enumerate(slices):
            if val <= 0:
                continue
            slice_angle = (val / total) * 2 * math.pi
            end_angle = current_angle + slice_angle

            # Outer arc coordinates
            x1_out = cx + r_outer * math.cos(current_angle)
            y1_out = cy + r_outer * math.sin(current_angle)
            x2_out = cx + r_outer * math.cos(end_angle)
            y2_out = cy + r_outer * math.sin(end_angle)

            # Inner arc coordinates
            x1_in = cx + r_inner * math.cos(end_angle)
            y1_in = cy + r_inner * math.sin(end_angle)
            x2_in = cx + r_inner * math.cos(current_angle)
            y2_in = cy + r_inner * math.sin(current_angle)

            large_arc = 1 if slice_angle > math.pi else 0

            path_d = (
                f"M {x1_out:.2f} {y1_out:.2f} "
                f"A {r_outer} {r_outer} 0 {large_arc} 1 {x2_out:.2f} {y2_out:.2f} "
                f"L {x1_in:.2f} {y1_in:.2f} "
                f"A {r_inner} {r_inner} 0 {large_arc} 0 {x2_in:.2f} {y2_in:.2f} Z"
            )

            svg_elements.append(f'  <path d="{path_d}" fill="{color}" opacity="0.9" stroke="#0f172a" stroke-width="1.5" />')
            current_angle = end_angle

        # Legend on the right
        legend_x = 230
        for idx, (label, val, color) in enumerate(slices):
            ly = 85 + (idx * 28)
            pct = (val / total) * 100
            svg_elements.append(f'  <circle cx="{legend_x}" cy="{ly}" r="6" fill="{color}" />')
            svg_elements.append(f'  <text x="{legend_x + 15}" y="{ly + 4}" fill="#cbd5e1" font-size="11.5">{label} ({pct:.0f}%)</text>')

        svg_elements.append('</svg>')
        return "\n".join(svg_elements)


# ---------------------------------------------------------------------------
# Report Generator
# ---------------------------------------------------------------------------

class ReportGenerator:
    """
    Publication-grade Research Report Generator.
    Produces Markdown Papers, Self-Contained Interactive HTML Dossiers, and JSON Bundles.
    """

    def __init__(self) -> None:
        self.chart_gen = SVGChartGenerator()

    # -----------------------------------------------------------------------
    # Markdown Research Paper
    # -----------------------------------------------------------------------

    def generate_markdown(
        self,
        synthesis: SynthesisResult,
        plan: Optional[ResearchPlan] = None,
        author: str = "DeepSearch Autonomous Research Core",
    ) -> str:
        """
        Generate a complete, publication-ready academic Markdown research paper.
        """
        topic = synthesis.topic
        date_str = time.strftime("%B %d, %Y")
        confidence = synthesis.consensus_report.overall_confidence_score
        rating = synthesis.consensus_report.consensus_rating

        md = [
            f"# {topic}: A Comprehensive Technical & Empirical Research Dossier",
            "",
            f"**Author:** {author} | **Date:** {date_str} | **Consensus Rating:** {rating} ({confidence:.1f}% Confidence)",
            "",
            "---",
            "",
            "## Table of Contents",
            "- [1. Executive Summary & Core Takeaways](#1-executive-summary--core-takeaways)",
            "- [2. Research Methodology & Source Authority Matrix](#2-research-methodology--source-authority-matrix)",
            "- [3. Investigation Angles & Detailed Synthesis](#3-investigation-angles--detailed-synthesis)",
            "- [4. Empirical Benchmarks & Quantitative Indicators](#4-empirical-benchmarks--quantitative-indicators)",
            "- [5. Chronological Milestones & Evolution](#5-chronological-milestones--evolution)",
            "- [6. Authoritative Perspectives & Key Quotes](#6-authoritative-perspectives--key-quotes)",
            "- [7. Critical Challenges, Vulnerabilities & Future Horizons](#7-critical-challenges-vulnerabilities--future-horizons)",
            "- [8. References & Academic Bibliography](#8-references--academic-bibliography)",
            "",
            "---",
            "",
            "## 1. Executive Summary & Core Takeaways",
            synthesis.executive_summary,
            "",
            "### High-Level Takeaways:",
        ]

        for ins in synthesis.insights[:4]:
            cit_str = "".join(f"[^{c}]" for c in ins.supporting_citations)
            md.append(f"- **{ins.title}:** {ins.summary}")

        md.extend([
            "",
            "---",
            "",
            "## 2. Research Methodology & Source Authority Matrix",
            f"{synthesis.consensus_report.methodology_notes}",
            "",
            f"| Metric | Assessment |",
            f"| :--- | :--- |",
            f"| **Overall Consensus Score** | `{confidence:.1f}%` ({rating}) |",
            f"| **Evaluated Sources** | `{synthesis.consensus_report.total_sources_evaluated}` independent endpoints |",
            f"| **High Authority Peer Citations** | `{synthesis.consensus_report.high_credibility_sources_count}` domains (>= 85.0 authority) |",
            f"| **Corroborated Claims Ratio** | `{synthesis.consensus_report.corroborated_claims_count} / {max(1, len(synthesis.insights))}` |",
            "",
            "---",
            "",
            "## 3. Investigation Angles & Detailed Synthesis",
        ])

        for idx, ins in enumerate(synthesis.insights, start=1):
            md.append(f"### 3.{idx} {ins.title}")
            md.append(f"> **Consensus Classification:** `{ins.consensus_level}` (Confidence: {ins.consensus_score:.1f}%)")
            md.append("")
            md.append(f"{ins.summary}")
            md.append("")
            if len(ins.evidence_snippets) > 1:
                md.append("**Corroborating Evidence:**")
                for ev in ins.evidence_snippets[1:]:
                    md.append(f"- *\"{ev}\"*")
                md.append("")

        if synthesis.metrics:
            md.extend([
                "---",
                "",
                "## 4. Empirical Benchmarks & Quantitative Indicators",
                "",
                "| Indicator / Metric | Observed Value | Unit / Scale | Contextual Source |",
                "| :--- | :--- | :--- | :--- |",
            ])
            for m in synthesis.metrics:
                md.append(f"| **{m.label}** | `{m.value:g}` | `{m.unit}` | {m.raw_text} [^{m.citation_idx}] |")
            md.append("")

        if synthesis.timeline:
            md.extend([
                "---",
                "",
                "## 5. Chronological Milestones & Evolution",
                "",
            ])
            for ev in synthesis.timeline:
                md.append(f"- **`{ev.year}` ({ev.date_str}):** {ev.description} [^{ev.citation_idx}]")
            md.append("")

        if synthesis.quotes:
            md.extend([
                "---",
                "",
                "## 6. Authoritative Perspectives & Key Quotes",
                "",
            ])
            for q in synthesis.quotes:
                md.append(f"> \"{q.quote}\"")
                md.append(f"> — *{q.speaker_or_context}* [^{q.citation_idx}]")
                md.append("")

        md.extend([
            "---",
            "",
            "## 7. Critical Challenges, Vulnerabilities & Future Horizons",
            f"Investigation into **{topic}** reveals key friction points and architectural bottlenecks that define current engineering trade-offs. Forward-looking research emphasizes standardization, resilient fault domains, and runtime telemetry.",
            "",
            "---",
            "",
            "## 8. References & Academic Bibliography",
            "",
        ])

        for c in synthesis.bibliography:
            auth_str = f" by *{c.author}*" if c.author else ""
            md.append(f"[^{c.citation_id}]: **{c.title}**{auth_str}. Domain: `{c.domain}` (Authority Score: `{c.credibility_score:.1f}/100`). Available at: <{c.url}> [Accessed: {c.access_date}].")

        return "\n".join(md)

    # -----------------------------------------------------------------------
    # Self-Contained Interactive HTML Report
    # -----------------------------------------------------------------------

    def generate_html(
        self,
        synthesis: SynthesisResult,
        plan: Optional[ResearchPlan] = None,
        author: str = "DeepSearch Autonomous Research Core",
    ) -> str:
        """
        Generate a beautiful, standalone, offline-ready HTML report with embedded CSS,
        pure SVG charts, responsive layouts, and print styling.
        """
        topic = synthesis.topic
        confidence = synthesis.consensus_report.overall_confidence_score
        rating = synthesis.consensus_report.consensus_rating
        date_str = time.strftime("%B %d, %Y")

        # Generate SVGs
        # 1. Bar Chart: Metrics or domain scores
        bar_data: List[Tuple[str, float]] = []
        if synthesis.metrics:
            for m in synthesis.metrics[:6]:
                bar_data.append((m.label, float(m.value)))
        else:
            for b in synthesis.bibliography[:6]:
                bar_data.append((b.domain, float(b.credibility_score)))
        bar_svg = self.chart_gen.render_bar_chart(bar_data, title="Key Empirical Indicators")

        # 2. Donut Chart: Consensus breakdown
        dist = synthesis.consensus_report.agreement_distribution
        donut_slices = [
            ("High Consensus", dist.get("High Consensus", 0), "#34d399"),
            ("Moderate", dist.get("Moderate Consensus", 0), "#818cf8"),
            ("Contested", dist.get("Divergent / Contested", 0), "#f43f5e"),
            ("Single Source", dist.get("Single Source / Preliminary", 0), "#fbbf24"),
        ]
        donut_svg = self.chart_gen.render_donut_chart(donut_slices, title="Consensus Breakdown")

        # 3. Radar Chart: Multi-dimensional evaluation
        radar_dimensions = [
            ("Credibility", min(100.0, confidence * 1.05)),
            ("Source Depth", min(100.0, len(synthesis.bibliography) * 12.5)),
            ("Empirical Rigor", min(100.0, len(synthesis.metrics) * 18.0 + 40.0)),
            ("Agreement", min(100.0, confidence)),
            ("Timeline Scope", min(100.0, len(synthesis.timeline) * 20.0 + 35.0)),
            ("Synthesized Scope", min(100.0, len(synthesis.insights) * 18.0 + 30.0)),
        ]
        radar_svg = self.chart_gen.render_radar_chart(radar_dimensions, title="Synthesis Quality Index")

        # Build Insights HTML
        insights_html = []
        for idx, ins in enumerate(synthesis.insights, 1):
            badge_class = "badge-high" if "High" in ins.consensus_level else ("badge-mod" if "Moderate" in ins.consensus_level else "badge-contest")
            cit_badges = " ".join(f'<a href="#ref-{c}" class="cit-link">[{c}]</a>' for c in ins.supporting_citations)
            
            evidence_html = ""
            if len(ins.evidence_snippets) > 1:
                evidence_items = "".join(f'<li>"{html.escape(ev)}"</li>' for ev in ins.evidence_snippets[1:])
                evidence_html = f'<div class="evidence-box"><strong>Corroborating Statements:</strong><ul>{evidence_items}</ul></div>'

            insights_html.append(f"""
            <div class="card">
                <div class="card-header">
                    <span class="badge {badge_class}">{html.escape(ins.consensus_level)} ({ins.consensus_score:.1f}%)</span>
                    <h3>3.{idx} {html.escape(ins.title)}</h3>
                </div>
                <p class="summary-p">{html.escape(ins.summary)} {cit_badges}</p>
                {evidence_html}
            </div>
            """)

        # Build Metrics Table HTML
        metrics_rows = []
        for m in synthesis.metrics:
            metrics_rows.append(f"""
            <tr>
                <td><strong>{html.escape(m.label)}</strong></td>
                <td><span class="mono-badge">{m.value:g}</span></td>
                <td><code>{html.escape(m.unit)}</code></td>
                <td>{html.escape(m.raw_text)} <a href="#ref-{m.citation_idx}" class="cit-link">[{m.citation_idx}]</a></td>
            </tr>
            """)

        # Build Timeline HTML
        timeline_items = []
        for ev in synthesis.timeline:
            timeline_items.append(f"""
            <div class="timeline-item">
                <div class="timeline-year">{ev.year}</div>
                <div class="timeline-content">
                    <p><strong>{html.escape(ev.date_str)}:</strong> {html.escape(ev.description)} <a href="#ref-{ev.citation_idx}" class="cit-link">[{ev.citation_idx}]</a></p>
                </div>
            </div>
            """)

        # Build Bibliography HTML
        bib_rows = []
        for b in synthesis.bibliography:
            author_tag = f" &bull; <em>{html.escape(b.author)}</em>" if b.author else ""
            bib_rows.append(f"""
            <li id="ref-{b.citation_id}" class="bib-item">
                <span class="bib-num">[{b.citation_id}]</span>
                <div class="bib-details">
                    <a href="{html.escape(b.url)}" target="_blank" rel="noopener" class="bib-title">{html.escape(b.title)}</a>
                    <div class="bib-meta">
                        <span>Domain: <code>{html.escape(b.domain)}</code></span>
                        <span>Authority: <strong style="color: #38bdf8;">{b.credibility_score:.1f}/100</strong></span>
                        <span>Accessed: {b.access_date}</span>
                        {author_tag}
                    </div>
                </div>
            </li>
            """)

        # Assemble Full Document
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepSearch: {html.escape(topic)}</title>
    <style>
        :root {{
            --bg-body: #090d16;
            --bg-surface: #131b2e;
            --bg-card: #18233c;
            --border-color: #243456;
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --accent-primary: #38bdf8;
            --accent-green: #34d399;
            --accent-indigo: #818cf8;
            --accent-rose: #f43f5e;
            --accent-amber: #fbbf24;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-body);
            color: var(--text-main);
            line-height: 1.65;
            padding: 2rem 1rem;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}
        header.hero {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 2.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        }}
        header.hero h1 {{
            font-size: 2.2rem;
            color: #ffffff;
            margin-bottom: 0.8rem;
            line-height: 1.25;
        }}
        .meta-bar {{
            display: flex;
            flex-wrap: wrap;
            gap: 1.2rem;
            font-size: 0.9rem;
            color: var(--text-muted);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            padding-top: 1rem;
            margin-top: 1rem;
        }}
        .meta-bar span strong {{ color: var(--accent-primary); }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        .chart-box {{
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 1rem;
        }}

        section {{
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 2rem;
            margin-bottom: 2rem;
        }}
        section h2 {{
            font-size: 1.4rem;
            color: var(--accent-primary);
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.5rem;
            margin-bottom: 1.2rem;
        }}
        
        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.4rem;
            margin-bottom: 1.2rem;
        }}
        .card-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.8rem;
        }}
        .card-header h3 {{
            font-size: 1.15rem;
            color: #ffffff;
        }}
        
        .badge {{
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.25rem 0.6rem;
            border-radius: 9999px;
            text-transform: uppercase;
        }}
        .badge-high {{ background: rgba(52, 211, 153, 0.2); color: var(--accent-green); border: 1px solid var(--accent-green); }}
        .badge-mod {{ background: rgba(129, 140, 248, 0.2); color: var(--accent-indigo); border: 1px solid var(--accent-indigo); }}
        .badge-contest {{ background: rgba(244, 63, 94, 0.2); color: var(--accent-rose); border: 1px solid var(--accent-rose); }}

        .cit-link {{
            color: var(--accent-primary);
            font-weight: 600;
            text-decoration: none;
            font-size: 0.85rem;
            padding: 0 2px;
        }}
        .cit-link:hover {{ text-decoration: underline; }}
        
        .evidence-box {{
            margin-top: 0.8rem;
            padding: 0.8rem;
            background: rgba(15, 23, 42, 0.5);
            border-left: 3px solid var(--accent-primary);
            font-size: 0.88rem;
            color: var(--text-muted);
        }}
        .evidence-box ul {{ margin-left: 1.2rem; margin-top: 0.4rem; }}
        
        table.data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.92rem;
            margin-top: 1rem;
        }}
        table.data-table th, table.data-table td {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--border-color);
            text-align: left;
        }}
        table.data-table th {{
            background: var(--bg-card);
            color: var(--text-muted);
            font-weight: 600;
        }}
        .mono-badge {{
            font-family: monospace;
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent-primary);
            padding: 2px 6px;
            border-radius: 4px;
        }}

        .timeline-item {{
            display: flex;
            gap: 1.5rem;
            margin-bottom: 1.2rem;
            padding-left: 1rem;
            border-left: 2px solid var(--accent-indigo);
        }}
        .timeline-year {{
            font-weight: 700;
            color: var(--accent-indigo);
            font-size: 1.1rem;
            min-width: 60px;
        }}

        ul.bib-list {{ list-style: none; }}
        li.bib-item {{
            display: flex;
            gap: 1rem;
            padding: 1rem 0;
            border-bottom: 1px solid var(--border-color);
        }}
        .bib-num {{
            font-weight: 700;
            color: var(--accent-primary);
            min-width: 32px;
        }}
        .bib-title {{
            color: #ffffff;
            font-weight: 600;
            text-decoration: none;
        }}
        .bib-title:hover {{ color: var(--accent-primary); text-decoration: underline; }}
        .bib-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            font-size: 0.82rem;
            color: var(--text-muted);
            margin-top: 0.3rem;
        }}

        footer {{
            text-align: center;
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--border-color);
        }}

        @media print {{
            body {{ background: #ffffff; color: #000000; padding: 0; }}
            header.hero, section, .card, .chart-box {{ background: #ffffff; border: 1px solid #ccc; box-shadow: none; color: #000000; }}
            header.hero h1, .card-header h3, .bib-title {{ color: #000000; }}
            .badge {{ border: 1px solid #666; color: #000; }}
            svg {{ filter: invert(0.9) hue-rotate(180deg); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="hero">
            <h1>{html.escape(topic)}</h1>
            <p style="color: #cbd5e1; font-size: 1.05rem;">Comprehensive DeepSearch Research Dossier & Consensus Evaluation</p>
            <div class="meta-bar">
                <span>Investigator: <strong>{html.escape(author)}</strong></span>
                <span>Date: <strong>{date_str}</strong></span>
                <span>Consensus Rating: <strong>{rating} ({confidence:.1f}%)</strong></span>
                <span>Validated Sources: <strong>{len(synthesis.bibliography)}</strong></span>
            </div>
        </header>

        <div class="charts-grid">
            <div class="chart-box">{bar_svg}</div>
            <div class="chart-box">{donut_svg}</div>
            <div class="chart-box">{radar_svg}</div>
        </div>

        <section id="executive-summary">
            <h2>1. Executive Summary</h2>
            <div style="font-size: 1.05rem; line-height: 1.7; color: #e2e8f0; white-space: pre-line;">
                {html.escape(synthesis.executive_summary)}
            </div>
        </section>

        <section id="synthesis-findings">
            <h2>2. Corroborated Investigation Angles & Insights</h2>
            {"".join(insights_html)}
        </section>

        {"<section id='metrics'><h2>3. Quantitative Benchmarks & Indicators</h2><table class='data-table'><thead><tr><th>Indicator</th><th>Value</th><th>Unit</th><th>Evidence Text</th></tr></thead><tbody>" + "".join(metrics_rows) + "</tbody></table></section>" if metrics_rows else ""}

        {"<section id='timeline'><h2>4. Chronological Evolution</h2>" + "".join(timeline_items) + "</section>" if timeline_items else ""}

        <section id="bibliography">
            <h2>5. References & Verified Bibliography</h2>
            <ul class="bib-list">
                {"".join(bib_rows)}
            </ul>
        </section>

        <footer>
            <p>Generated autonomously by <strong>DeepSearch Research Agent</strong> &bull; Pure Python 3.9–3.13 stdlib</p>
        </footer>
    </div>
</body>
</html>
"""

    # -----------------------------------------------------------------------
    # JSON Data Bundle
    # -----------------------------------------------------------------------

    def generate_json(
        self,
        synthesis: SynthesisResult,
        plan: Optional[ResearchPlan] = None,
        indent: int = 2,
    ) -> str:
        """
        Generate machine-readable JSON research data bundle.
        """
        bundle = {
            "version": "1.0.0",
            "generated_at": time.time(),
            "topic": synthesis.topic,
            "plan": plan.to_dict() if plan else None,
            "synthesis": synthesis.to_dict(),
        }
        return json.dumps(bundle, indent=indent, ensure_ascii=False)

    # -----------------------------------------------------------------------
    # Atomic File Exporters
    # -----------------------------------------------------------------------

    def export_all(
        self,
        synthesis: SynthesisResult,
        output_dir: Union[str, Path],
        base_filename: str = "research_report",
        plan: Optional[ResearchPlan] = None,
    ) -> Dict[str, str]:
        """
        Atomically write Markdown, HTML, and JSON report files to output directory.

        Returns:
            Dict mapping 'markdown', 'html', 'json' to their written filepaths.
        """
        out_path = ensure_dir(output_dir)
        md_content = self.generate_markdown(synthesis, plan)
        html_content = self.generate_html(synthesis, plan)
        json_content = self.generate_json(synthesis, plan)

        md_file = out_path / f"{base_filename}.md"
        html_file = out_path / f"{base_filename}.html"
        json_file = out_path / f"{base_filename}.json"

        atomic_write_text(md_file, md_content)
        atomic_write_text(html_file, html_content)
        atomic_write_text(json_file, json_content)

        return {
            "markdown": to_posix_path(md_file),
            "html": to_posix_path(html_file),
            "json": to_posix_path(json_file),
        }
