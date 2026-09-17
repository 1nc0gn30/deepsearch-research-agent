"""
test_report_engine.py - Unit tests for report_engine.py (Markdown, Interactive HTML with SVG charts, JSON).
"""

import json
from pathlib import Path
import pytest

from deepsearch_research_agent.crawler import CrawlResult
from deepsearch_research_agent.planner import ResearchPlanner
from deepsearch_research_agent.report_engine import ReportGenerator, SVGChartGenerator
from deepsearch_research_agent.synthesizer import FactSynthesizer


@pytest.fixture
def sample_synthesis_and_plan():
    """Fixture providing synthesized research and a research plan."""
    crawl_data = [
        CrawlResult(
            url="https://arxiv.org/abs/2501.99999",
            status_code=200,
            title="Next-Gen Architecture for Zero-Copy Data Pipelines",
            text="In 2024, engineers demonstrated 85,000 requests per second with 14.8ms average latency. The system achieved a 42.5% efficiency improvement over legacy designs.",
            markdown="# Next-Gen Architecture\n> Zero-copy pipelines eliminate kernel memory context switches.",
            headings=["Next-Gen Architecture"],
            metadata={"author": "Systems Research Lab"},
            links=[],
            credibility_score=96.0,
            word_count=60,
            reading_time_min=0.3,
        ),
        CrawlResult(
            url="https://docs.python.org/3/howto/concurrency.html",
            status_code=200,
            title="Official Python Concurrency Standards",
            text="In 2025, PEP 703 introduced free-threaded execution. Memory overhead scaled sub-linearly.",
            markdown="# Python Concurrency\nOfficial guide to thread safety.",
            headings=["Python Concurrency"],
            metadata={},
            links=[],
            credibility_score=95.0,
            word_count=40,
            reading_time_min=0.2,
        ),
    ]

    planner = ResearchPlanner()
    plan_dict = planner.generate_plan("High Performance Python Concurrency", depth="standard")
    
    synthesizer = FactSynthesizer()
    synthesis = synthesizer.synthesize("High Performance Python Concurrency", crawl_data)

    return synthesis, plan_dict


def test_svg_chart_generator():
    """Verify SVG generation for Bar, Radar, and Donut charts."""
    # Bar Chart
    bar_svg = SVGChartGenerator.render_bar_chart(
        [("Throughput", 85000.0), ("Latency", 14.8), ("Efficiency Gain", 42.5)],
        title="Test Bar Chart",
    )
    assert "<svg" in bar_svg
    assert "</svg>" in bar_svg
    assert "Throughput" in bar_svg
    assert "<rect" in bar_svg

    # Radar Chart
    radar_svg = SVGChartGenerator.render_radar_chart(
        [("Rigor", 90.0), ("Speed", 85.0), ("Reliability", 95.0), ("Adoption", 80.0)],
        title="Test Radar Chart",
    )
    assert "<svg" in radar_svg
    assert "<polygon" in radar_svg
    assert "<circle" in radar_svg

    # Donut Chart
    donut_svg = SVGChartGenerator.render_donut_chart(
        [("High", 3, "#34d399"), ("Moderate", 2, "#818cf8")],
        title="Test Donut Chart",
    )
    assert "<svg" in donut_svg
    assert "<path" in donut_svg
    assert "High (60%)" in donut_svg or "High" in donut_svg


def test_report_generator_markdown(sample_synthesis_and_plan):
    """Verify generated Markdown research paper structure and academic citations."""
    synthesis, plan_dict = sample_synthesis_and_plan
    generator = ReportGenerator()

    md = generator.generate_markdown(synthesis)

    assert "# High Performance Python Concurrency: A Comprehensive Technical & Empirical Research Dossier" in md
    assert "## Table of Contents" in md
    assert "## 1. Executive Summary & Core Takeaways" in md
    assert "## 2. Research Methodology & Source Authority Matrix" in md
    assert "## 3. Investigation Angles & Detailed Synthesis" in md
    assert "## 4. Empirical Benchmarks & Quantitative Indicators" in md
    assert "## 8. References & Academic Bibliography" in md
    assert "[^1]:" in md  # Academic bibliography entries
    assert "arxiv.org" in md


def test_report_generator_html(sample_synthesis_and_plan):
    """Verify generated HTML report is self-contained with embedded SVG charts."""
    synthesis, plan_dict = sample_synthesis_and_plan
    generator = ReportGenerator()

    html_content = generator.generate_html(synthesis)

    assert "<!DOCTYPE html>" in html_content
    assert "<title>DeepSearch: High Performance Python Concurrency</title>" in html_content
    assert "<style>" in html_content
    assert "<svg" in html_content  # Embedded vector charts
    assert "badge" in html_content
    assert "Quantitative Benchmarks" in html_content
    assert "References & Verified Bibliography" in html_content
    assert "arxiv.org" in html_content
    assert "docs.python.org" in html_content


def test_report_generator_json(sample_synthesis_and_plan):
    """Verify generated JSON bundle is valid machine-readable data."""
    synthesis, plan_dict = sample_synthesis_and_plan
    generator = ReportGenerator()

    json_str = generator.generate_json(synthesis)
    assert isinstance(json_str, str)
    data = json.loads(json_str)

    assert data["version"] == "1.0.0"
    assert data["topic"] == "High Performance Python Concurrency"
    assert "synthesis" in data
    assert "bibliography" in data["synthesis"]
    assert len(data["synthesis"]["bibliography"]) == 2


def test_report_generator_export_all(tmp_path, sample_synthesis_and_plan):
    """Verify export_all writes .md, .html, and .json atomically to target directory."""
    synthesis, plan_dict = sample_synthesis_and_plan
    generator = ReportGenerator()

    out_dir = tmp_path / "reports_output"
    files = generator.export_all(synthesis, output_dir=out_dir, base_filename="concurrency_dossier")

    assert "markdown" in files
    assert "html" in files
    assert "json" in files

    md_path = Path(files["markdown"])
    html_path = Path(files["html"])
    json_path = Path(files["json"])

    assert md_path.exists()
    assert html_path.exists()
    assert json_path.exists()

    assert len(md_path.read_text(encoding="utf-8")) > 100
    assert len(html_path.read_text(encoding="utf-8")) > 100
    assert len(json_path.read_text(encoding="utf-8")) > 100
