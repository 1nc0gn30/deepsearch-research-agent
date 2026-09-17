"""
planner.py - Intelligent Query Planner and Research Deconstructor.

Pure Python 3.9–3.13 stdlib. Formulates structured multi-angle research plans,
deconstructs complex queries into prioritized investigation angles, generates
search query variations (Boolean, exact-match, target domain, filetypes),
and allocates research resource budgets.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class QueryVariation:
    """A specific search query string with search operators and target types."""
    query: str
    query_type: str  # "exact", "boolean", "site_constrained", "filetype", "comparative", "natural"
    target_site_or_type: Optional[str] = None
    expected_source_type: str = "general"  # "academic", "documentation", "news", "benchmark", "repo", "expert_analysis"
    priority: int = 1  # 1 = High, 2 = Medium, 3 = Low


@dataclass
class InvestigationAngle:
    """A distinct sub-question or dimension of the research topic."""
    angle_id: str
    title: str
    sub_question: str
    category: str  # "architecture", "trends", "tradeoffs", "risks", "applications", "future", "benchmarks", "governance"
    priority: int  # 1 (Critical) to 3 (Supplementary)
    expected_source_types: List[str]
    query_variations: List[QueryVariation] = field(default_factory=list)
    stage: int = 1  # 1 = Foundational, 2 = Technical/In-depth, 3 = Synthesis/Outlook


@dataclass
class ResearchBudget:
    """Resource allocation budget for the research session."""
    depth: str
    target_sources_min: int
    target_sources_max: int
    max_query_iterations: int
    timeout_seconds: int
    max_crawl_workers: int
    target_word_count_min: int


@dataclass
class ResearchPlan:
    """The master research plan containing angles, query strategies, and metadata."""
    topic: str
    clean_topic: str
    depth: str
    domain_focus: str
    created_at: float
    budget: ResearchBudget
    angles: List[InvestigationAngle]
    total_queries: int
    execution_stages: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert research plan to a JSON-serializable dictionary."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Planner Engine
# ---------------------------------------------------------------------------

class ResearchPlanner:
    """
    Deconstructs research topics into comprehensive, multi-angle investigation
    plans with specialized search queries and source expectations.
    """

    # Depth presets
    DEPTH_BUDGETS: Dict[str, Dict[str, int]] = {
        "quick": {
            "target_sources_min": 3,
            "target_sources_max": 6,
            "max_query_iterations": 4,
            "timeout_seconds": 30,
            "max_crawl_workers": 3,
            "target_word_count_min": 1000,
        },
        "standard": {
            "target_sources_min": 6,
            "target_sources_max": 12,
            "max_query_iterations": 8,
            "timeout_seconds": 60,
            "max_crawl_workers": 5,
            "target_word_count_min": 2500,
        },
        "deep": {
            "target_sources_min": 12,
            "target_sources_max": 25,
            "max_query_iterations": 16,
            "timeout_seconds": 120,
            "max_crawl_workers": 8,
            "target_word_count_min": 5000,
        },
        "comprehensive": {
            "target_sources_min": 20,
            "target_sources_max": 40,
            "max_query_iterations": 24,
            "timeout_seconds": 240,
            "max_crawl_workers": 10,
            "target_word_count_min": 8000,
        },
    }

    # Standard Domain Templates
    DOMAIN_ANGLE_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
        "technical": [
            {
                "title": "Architecture & Core Mechanisms",
                "sub_question": "What is the foundational architecture, system design, and mathematical/mechanical principles underlying {topic}?",
                "category": "architecture",
                "priority": 1,
                "stage": 1,
                "sources": ["documentation", "academic", "repo"],
            },
            {
                "title": "Technical Tradeoffs & Comparisons",
                "sub_question": "How does {topic} compare to state-of-the-art alternatives in performance, latency, scalability, and complexity?",
                "category": "tradeoffs",
                "priority": 1,
                "stage": 2,
                "sources": ["benchmark", "academic", "documentation"],
            },
            {
                "title": "Implementation & Practical Deployment",
                "sub_question": "What are real-world production setups, best practices, reference implementations, and tooling ecosystems for {topic}?",
                "category": "applications",
                "priority": 2,
                "stage": 2,
                "sources": ["repo", "documentation", "expert_analysis"],
            },
            {
                "title": "Bottlenecks, Failure Modes & Edge Cases",
                "sub_question": "What are the primary performance bottlenecks, security vulnerabilities, and failure modes observed in {topic}?",
                "category": "risks",
                "priority": 2,
                "stage": 2,
                "sources": ["benchmark", "expert_analysis", "documentation"],
            },
            {
                "title": "Future Evolution & Active Research",
                "sub_question": "What are the latest open research problems, roadmap milestones, and next-generation iterations for {topic}?",
                "category": "future",
                "priority": 3,
                "stage": 3,
                "sources": ["academic", "expert_analysis", "news"],
            },
        ],
        "business": [
            {
                "title": "Market Dynamics & Industry Landscape",
                "sub_question": "What is the current market size, growth trajectory, competitive landscape, and economic drivers of {topic}?",
                "category": "trends",
                "priority": 1,
                "stage": 1,
                "sources": ["news", "expert_analysis"],
            },
            {
                "title": "Cost Structure & Unit Economics",
                "sub_question": "What are the capital expenditures, operational costs, monetization models, and ROI metrics for {topic}?",
                "category": "tradeoffs",
                "priority": 1,
                "stage": 2,
                "sources": ["expert_analysis", "news"],
            },
            {
                "title": "Adoption Barriers & Strategic Risks",
                "sub_question": "What regulatory hurdles, compliance risks, vendor lock-in, and organizational friction impact {topic}?",
                "category": "risks",
                "priority": 2,
                "stage": 2,
                "sources": ["expert_analysis", "governance"],
            },
            {
                "title": "Key Players & Case Studies",
                "sub_question": "Who are the dominant enterprises/startups in {topic} and what do their customer case studies reveal?",
                "category": "applications",
                "priority": 2,
                "stage": 2,
                "sources": ["news", "expert_analysis"],
            },
            {
                "title": "Future Outlook & Market Predictions",
                "sub_question": "How is {topic} expected to evolve over the next 3–5 years in market share and disruption potential?",
                "category": "future",
                "priority": 3,
                "stage": 3,
                "sources": ["expert_analysis", "news"],
            },
        ],
        "scientific": [
            {
                "title": "Theoretical Foundations & Hypotheses",
                "sub_question": "What fundamental theoretical frameworks, physical/biological laws, or formal axioms govern {topic}?",
                "category": "architecture",
                "priority": 1,
                "stage": 1,
                "sources": ["academic"],
            },
            {
                "title": "Experimental Methodologies & Benchmarks",
                "sub_question": "What empirical datasets, experimental setups, measurement protocols, and baseline metrics exist for {topic}?",
                "category": "benchmarks",
                "priority": 1,
                "stage": 2,
                "sources": ["academic", "benchmark"],
            },
            {
                "title": "Key Discoveries & Quantitative Findings",
                "sub_question": "What are the most significant validated findings, statistical significance rates, and empirical breakthroughs in {topic}?",
                "category": "applications",
                "priority": 1,
                "stage": 2,
                "sources": ["academic"],
            },
            {
                "title": "Methodological Limitations & Debates",
                "sub_question": "Where does the scientific community hold conflicting interpretations, reproducibility issues, or methodological critiques regarding {topic}?",
                "category": "risks",
                "priority": 2,
                "stage": 2,
                "sources": ["academic", "expert_analysis"],
            },
            {
                "title": "Unsolved Problems & Next Frontiers",
                "sub_question": "What are the highest-impact open questions and upcoming experimental frontiers in {topic}?",
                "category": "future",
                "priority": 3,
                "stage": 3,
                "sources": ["academic"],
            },
        ],
        "general": [
            {
                "title": "Overview & Core Definitions",
                "sub_question": "What is {topic}, what is its origin, and why is it currently significant?",
                "category": "architecture",
                "priority": 1,
                "stage": 1,
                "sources": ["documentation", "news"],
            },
            {
                "title": "Current State & Major Developments",
                "sub_question": "What are the latest breakthroughs, widespread applications, and active trends in {topic}?",
                "category": "trends",
                "priority": 1,
                "stage": 2,
                "sources": ["news", "expert_analysis"],
            },
            {
                "title": "Pros, Cons & Critical Tradeoffs",
                "sub_question": "What are the primary advantages, drawbacks, and alternative approaches to {topic}?",
                "category": "tradeoffs",
                "priority": 2,
                "stage": 2,
                "sources": ["expert_analysis", "documentation"],
            },
            {
                "title": "Key Challenges & Controversies",
                "sub_question": "What safety, ethical, legal, or logistical challenges are associated with {topic}?",
                "category": "risks",
                "priority": 2,
                "stage": 2,
                "sources": ["news", "expert_analysis"],
            },
            {
                "title": "Future Outlook & Trajectory",
                "sub_question": "Where is {topic} headed in the next 2 to 5 years?",
                "category": "future",
                "priority": 3,
                "stage": 3,
                "sources": ["news", "expert_analysis"],
            },
        ],
    }

    def __init__(self, default_depth: str = "deep") -> None:
        self.default_depth = default_depth if default_depth in self.DEPTH_BUDGETS else "deep"

    # -----------------------------------------------------------------------
    # Domain & Keyword Inference
    # -----------------------------------------------------------------------

    def infer_domain(self, query: str) -> str:
        """Infer the most suitable domain category from topic keywords."""
        q_lower = query.lower()

        # Scientific indicators
        scientific_keywords = [
            "quantum", "crispr", "genetics", "biology", "physics", "chemistry",
            "clinical", "genome", "molecular", "astronomy", "neuroscience", "protein"
        ]
        if any(w in q_lower for w in scientific_keywords):
            return "scientific"

        # Business / Market indicators
        business_keywords = [
            "market", "revenue", "valuation", "investment", "business model", "saas",
            "growth", "roi", "cagr", "gdp", "industry", "pricing", "commercialization"
        ]
        if any(w in q_lower for w in business_keywords):
            return "business"

        # Technical indicators
        tech_keywords = [
            "system architecture", "software architecture", "neural architecture", "model architecture",
            "transformer", "algorithm", "llm", "compiler", "database", "distributed",
            "api", "framework", "kernel", "protocol", "benchmark", "rust", "python",
            "inference", "latency", "gpu", "cuda", "memory", "attention mechanism", "concurrency"
        ]
        if any(w in q_lower for w in tech_keywords):
            return "technical"

        return "general"

    def clean_topic_string(self, topic: str) -> str:
        """Clean and normalize the topic string."""
        clean = re.sub(r'["\']', '', topic)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean or "General Research Topic"

    # -----------------------------------------------------------------------
    # Query Variation Generation
    # -----------------------------------------------------------------------

    def generate_query_variations(
        self,
        topic: str,
        angle_title: str,
        category: str,
        expected_sources: List[str],
    ) -> List[QueryVariation]:
        """
        Generate recursive search query variations including exact phrases,
        boolean operators, site restrictions, and filetype qualifiers.
        """
        topic_clean = self.clean_topic_string(topic)
        variations: List[QueryVariation] = []

        # 1. Natural language / descriptive query
        variations.append(QueryVariation(
            query=f"{topic_clean} {angle_title}",
            query_type="natural",
            expected_source_type=expected_sources[0] if expected_sources else "general",
            priority=1,
        ))

        # 2. Exact match phrase variation
        variations.append(QueryVariation(
            query=f'"{topic_clean}" {category}',
            query_type="exact",
            expected_source_type=expected_sources[0] if expected_sources else "general",
            priority=1,
        ))

        # 3. Boolean query tailored to category
        if category == "architecture":
            variations.append(QueryVariation(
                query=f'"{topic_clean}" AND (architecture OR "system design" OR mechanism OR pipeline)',
                query_type="boolean",
                expected_source_type="documentation",
                priority=1,
            ))
        elif category == "tradeoffs":
            variations.append(QueryVariation(
                query=f'"{topic_clean}" AND (comparison OR tradeoffs OR benchmark OR vs OR latency)',
                query_type="boolean",
                expected_source_type="benchmark",
                priority=1,
            ))
        elif category == "risks":
            variations.append(QueryVariation(
                query=f'"{topic_clean}" AND (limitations OR vulnerabilities OR "failure modes" OR challenges)',
                query_type="boolean",
                expected_source_type="expert_analysis",
                priority=2,
            ))
        elif category == "future":
            variations.append(QueryVariation(
                query=f'"{topic_clean}" AND (roadmap OR "future trends" OR "open problems" OR 2026 OR 2025)',
                query_type="boolean",
                expected_source_type="expert_analysis",
                priority=2,
            ))
        elif category == "trends":
            variations.append(QueryVariation(
                query=f'"{topic_clean}" AND ("market share" OR growth OR forecast OR adoption)',
                query_type="boolean",
                expected_source_type="news",
                priority=1,
            ))
        else:
            variations.append(QueryVariation(
                query=f'"{topic_clean}" AND (analysis OR overview OR breakdown)',
                query_type="boolean",
                expected_source_type="general",
                priority=2,
            ))

        # 4. Academic or Documented Site-constrained variation if appropriate
        if "academic" in expected_sources:
            variations.append(QueryVariation(
                query=f'"{topic_clean}" site:arxiv.org OR site:openreview.net OR site:ieee.org',
                query_type="site_constrained",
                target_site_or_type="academic_portals",
                expected_source_type="academic",
                priority=2,
            ))
            variations.append(QueryVariation(
                query=f'"{topic_clean}" {category} filetype:pdf',
                query_type="filetype",
                target_site_or_type="pdf",
                expected_source_type="academic",
                priority=3,
            ))
        elif "documentation" in expected_sources:
            variations.append(QueryVariation(
                query=f'"{topic_clean}" (documentation OR spec OR RFC OR guide)',
                query_type="natural",
                expected_source_type="documentation",
                priority=2,
            ))

        if "repo" in expected_sources:
            variations.append(QueryVariation(
                query=f'"{topic_clean}" site:github.com',
                query_type="site_constrained",
                target_site_or_type="github.com",
                expected_source_type="repo",
                priority=2,
            ))

        return variations

    # -----------------------------------------------------------------------
    # Topic Deconstruction
    # -----------------------------------------------------------------------

    def deconstruct_topic(
        self,
        topic: str,
        domain_focus: Optional[str] = None,
        max_angles: int = 6,
    ) -> List[InvestigationAngle]:
        """
        Deconstruct a topic into 3 to 6 distinct investigation angles based
        on domain characteristics.
        """
        clean_topic = self.clean_topic_string(topic)
        effective_domain = domain_focus or self.infer_domain(clean_topic)
        templates = self.DOMAIN_ANGLE_TEMPLATES.get(effective_domain, self.DOMAIN_ANGLE_TEMPLATES["general"])

        angles: List[InvestigationAngle] = []
        for idx, tmpl in enumerate(templates[:max_angles], start=1):
            angle_id = f"angle_{idx:02d}"
            title = tmpl["title"]
            sub_q = tmpl["sub_question"].format(topic=clean_topic)
            category = tmpl["category"]
            priority = tmpl["priority"]
            stage = tmpl.get("stage", 1)
            sources = tmpl.get("sources", ["general"])

            variations = self.generate_query_variations(
                topic=clean_topic,
                angle_title=title,
                category=category,
                expected_sources=sources,
            )

            angles.append(InvestigationAngle(
                angle_id=angle_id,
                title=title,
                sub_question=sub_q,
                category=category,
                priority=priority,
                expected_source_types=sources,
                query_variations=variations,
                stage=stage,
            ))

        return angles

    def estimate_research_budget(self, depth: str = "deep") -> ResearchBudget:
        """Estimate the resource budget and execution limits for a given depth."""
        d_key = depth.lower()
        cfg = self.DEPTH_BUDGETS.get(d_key, self.DEPTH_BUDGETS["deep"])
        return ResearchBudget(
            depth=d_key if d_key in self.DEPTH_BUDGETS else "deep",
            target_sources_min=cfg["target_sources_min"],
            target_sources_max=cfg["target_sources_max"],
            max_query_iterations=cfg["max_query_iterations"],
            timeout_seconds=cfg["timeout_seconds"],
            max_crawl_workers=cfg["max_crawl_workers"],
            target_word_count_min=cfg["target_word_count_min"],
        )

    # -----------------------------------------------------------------------
    # Plan Generation
    # -----------------------------------------------------------------------

    def generate_plan(
        self,
        topic_or_query: str,
        depth: str = "deep",
        domain_focus: Optional[str] = None,
        max_subqueries: int = 6,
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive, structured research plan.

        Args:
            topic_or_query: Primary research topic or complex user question.
            depth: Research depth ('quick', 'standard', 'deep', 'comprehensive').
            domain_focus: Optional domain override ('technical', 'business', 'scientific', 'general').
            max_subqueries: Max investigation angles to generate (3 to 6).

        Returns:
            Dict containing the complete serialized ResearchPlan.
        """
        clean_topic = self.clean_topic_string(topic_or_query)
        effective_domain = domain_focus or self.infer_domain(clean_topic)
        budget = self.estimate_research_budget(depth)
        num_angles = max(3, min(6, max_subqueries))

        angles = self.deconstruct_topic(
            topic=clean_topic,
            domain_focus=effective_domain,
            max_angles=num_angles,
        )

        total_queries = sum(len(a.query_variations) for a in angles)

        # Build Stage Dependency Graph
        stages: Dict[int, List[Dict[str, Any]]] = {}
        for angle in angles:
            st = angle.stage
            if st not in stages:
                stages[st] = []
            stages[st].append({
                "angle_id": angle.angle_id,
                "title": angle.title,
                "priority": angle.priority,
                "query_count": len(angle.query_variations),
            })

        stage_descriptions = {
            1: "Foundational Discovery & Architectural Framing",
            2: "In-Depth Technical Examination, Benchmarking & Tradeoffs",
            3: "Critical Synthesis, Future Roadmap & Open Questions",
        }

        execution_stages = [
            {
                "stage": st_num,
                "name": stage_descriptions.get(st_num, f"Stage {st_num}"),
                "angles": stages[st_num],
            }
            for st_num in sorted(stages.keys())
        ]

        plan = ResearchPlan(
            topic=topic_or_query,
            clean_topic=clean_topic,
            depth=budget.depth,
            domain_focus=effective_domain,
            created_at=time.time(),
            budget=budget,
            angles=angles,
            total_queries=total_queries,
            execution_stages=execution_stages,
        )

        return plan.to_dict()

    # -----------------------------------------------------------------------
    # Exporters
    # -----------------------------------------------------------------------

    def export_plan_json(self, plan: Dict[str, Any], indent: int = 2) -> str:
        """Export research plan as formatted JSON."""
        return json.dumps(plan, indent=indent, ensure_ascii=False)

    def export_plan_markdown(self, plan: Dict[str, Any]) -> str:
        """Export research plan as structured Markdown."""
        topic = plan.get("clean_topic", plan.get("topic", "Research Plan"))
        depth = plan.get("depth", "deep").title()
        domain = plan.get("domain_focus", "General").title()
        budget = plan.get("budget", {})
        angles = plan.get("angles", [])

        lines = [
            f"# Research Plan: {topic}",
            "",
            f"**Depth:** {depth} | **Domain Focus:** {domain} | **Total Query Variations:** {plan.get('total_queries', 0)}",
            "",
            "## 1. Resource Allocation & Budget",
            f"- **Target Sources:** {budget.get('target_sources_min', 0)} – {budget.get('target_sources_max', 0)} sources",
            f"- **Max Query Iterations:** {budget.get('max_query_iterations', 0)} iterations",
            f"- **Max Concurrency:** {budget.get('max_crawl_workers', 0)} workers",
            f"- **Timeout Limit:** {budget.get('timeout_seconds', 0)} seconds",
            f"- **Target Synthesized Words:** ~{budget.get('target_word_count_min', 0)}+ words",
            "",
            "## 2. Investigation Angles & Query Matrix",
            "",
        ]

        for angle in angles:
            prio_label = {1: "High (P1)", 2: "Medium (P2)", 3: "Low (P3)"}.get(angle.get("priority", 1), "P1")
            sources_str = ", ".join(angle.get("expected_source_types", []))
            lines.append(f"### {angle.get('title', 'Angle')} `[{prio_label}]`")
            lines.append(f"> **Sub-Question:** {angle.get('sub_question', '')}")
            lines.append(f"**Target Source Types:** `{sources_str}` | **Stage:** {angle.get('stage', 1)}")
            lines.append("")
            lines.append("#### Query Variations:")
            for qv in angle.get("query_variations", []):
                q_type = qv.get("query_type", "natural")
                q_text = qv.get("query", "")
                src_type = qv.get("expected_source_type", "general")
                lines.append(f"- `[{q_type.upper()}]` `{q_text}` *(Target: {src_type})*")
            lines.append("")

        lines.append("## 3. Execution Pipeline Stages")
        for stage in plan.get("execution_stages", []):
            lines.append(f"### Stage {stage.get('stage')}: {stage.get('name')}")
            for a in stage.get("angles", []):
                lines.append(f"- **{a.get('title')}** ({a.get('query_count')} queries)")
            lines.append("")

        return "\n".join(lines)
