"""
test_planner.py - Unit tests for planner.py (ResearchPlanner, QueryVariations, Budgets).
"""

import json
import pytest
from deepsearch_research_agent.planner import (
    InvestigationAngle,
    QueryVariation,
    ResearchBudget,
    ResearchPlan,
    ResearchPlanner,
)


def test_planner_initialization():
    """Verify default planner initializes with correct preset depth."""
    planner = ResearchPlanner()
    assert planner.default_depth == "deep"

    planner_quick = ResearchPlanner(default_depth="quick")
    assert planner_quick.default_depth == "quick"

    planner_invalid = ResearchPlanner(default_depth="non_existent")
    assert planner_invalid.default_depth == "deep"


def test_infer_domain():
    """Verify domain inference identifies technical, business, and scientific queries."""
    planner = ResearchPlanner()

    assert planner.infer_domain("Transformer Attention Mechanism and Latency Optimization") == "technical"
    assert planner.infer_domain("Global SaaS Market Revenue and CAGR 2026") == "business"
    assert planner.infer_domain("CRISPR Genome Editing in Molecular Biology") == "scientific"
    assert planner.infer_domain("History of Modern Architecture in Europe") == "general"


def test_clean_topic_string():
    """Verify string normalization for topic inputs."""
    planner = ResearchPlanner()
    assert planner.clean_topic_string('  "AI Agents" & \'LLMs\'   ') == "AI Agents & LLMs"
    assert planner.clean_topic_string("") == "General Research Topic"


def test_estimate_research_budget():
    """Verify budget allocations across depth settings."""
    planner = ResearchPlanner()
    
    b_quick = planner.estimate_research_budget("quick")
    assert b_quick.depth == "quick"
    assert b_quick.target_sources_min == 3
    assert b_quick.timeout_seconds == 30

    b_deep = planner.estimate_research_budget("deep")
    assert b_deep.depth == "deep"
    assert b_deep.target_sources_min == 12
    assert b_deep.target_sources_max == 25
    assert b_deep.timeout_seconds == 120

    b_comp = planner.estimate_research_budget("comprehensive")
    assert b_comp.target_sources_min == 20
    assert b_comp.max_query_iterations == 24


def test_deconstruct_topic():
    """Verify topic deconstruction produces 3–6 angles with valid query variations."""
    planner = ResearchPlanner()
    angles = planner.deconstruct_topic("PostgreSQL Distributed Query Engine", domain_focus="technical", max_angles=5)
    
    assert len(angles) == 5
    for a in angles:
        assert isinstance(a, InvestigationAngle)
        assert a.title
        assert a.sub_question
        assert a.category in ["architecture", "tradeoffs", "applications", "risks", "future", "benchmarks", "trends"]
        assert a.priority in (1, 2, 3)
        assert len(a.query_variations) >= 3
        for qv in a.query_variations:
            assert isinstance(qv, QueryVariation)
            assert qv.query
            assert qv.query_type in ["natural", "exact", "boolean", "site_constrained", "filetype", "comparative"]


def test_generate_plan_technical():
    """Verify complete plan generation for technical topic."""
    planner = ResearchPlanner()
    plan_dict = planner.generate_plan(
        topic_or_query="Distributed Consensus in Raft vs Paxos",
        depth="deep",
        domain_focus="technical",
        max_subqueries=5,
    )

    assert plan_dict["topic"] == "Distributed Consensus in Raft vs Paxos"
    assert plan_dict["depth"] == "deep"
    assert plan_dict["domain_focus"] == "technical"
    assert "budget" in plan_dict
    assert "angles" in plan_dict
    assert len(plan_dict["angles"]) == 5
    assert plan_dict["total_queries"] > 10
    assert len(plan_dict["execution_stages"]) >= 2


def test_generate_plan_business():
    """Verify plan generation for business topic with domain override."""
    planner = ResearchPlanner()
    plan_dict = planner.generate_plan(
        topic_or_query="Generative AI Enterprise Adoption ROI",
        depth="standard",
        domain_focus="business",
    )

    assert plan_dict["domain_focus"] == "business"
    assert plan_dict["budget"]["target_sources_min"] == 6
    assert len(plan_dict["angles"]) >= 3


def test_export_plan_json_and_markdown():
    """Verify JSON and Markdown export formats."""
    planner = ResearchPlanner()
    plan_dict = planner.generate_plan("Rust Async Runtimes Tokio vs async-std")

    json_str = planner.export_plan_json(plan_dict)
    assert isinstance(json_str, str)
    parsed = json.loads(json_str)
    assert parsed["topic"] == "Rust Async Runtimes Tokio vs async-std"

    md_str = planner.export_plan_markdown(plan_dict)
    assert isinstance(md_str, str)
    assert "# Research Plan: Rust Async Runtimes Tokio vs async-std" in md_str
    assert "## 1. Resource Allocation & Budget" in md_str
    assert "## 2. Investigation Angles & Query Matrix" in md_str
    assert "## 3. Execution Pipeline Stages" in md_str
