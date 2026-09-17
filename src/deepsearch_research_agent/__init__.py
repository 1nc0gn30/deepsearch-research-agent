"""
deepsearch-research-agent - Autonomous Multi-Source Research & Synthesis Engine.

Pure Python 3.9–3.13 stdlib.
"""

from deepsearch_research_agent.compat import (
    atomic_write_bytes,
    atomic_write_text,
    ensure_dir,
    get_platform_info,
    is_linux,
    is_macos,
    is_termux,
    is_windows,
    open_in_browser,
    safe_filename,
    to_posix_path,
)
from deepsearch_research_agent.crawler import (
    CrawlResult,
    ExtractedDocument,
    HTMLTextExtractor,
    MockSearchEngine,
    WebCrawler,
    compute_credibility_score,
)
from deepsearch_research_agent.planner import (
    InvestigationAngle,
    QueryVariation,
    ResearchBudget,
    ResearchPlan,
    ResearchPlanner,
)
from deepsearch_research_agent.report_engine import (
    ReportGenerator,
    SVGChartGenerator,
)
from deepsearch_research_agent.synthesizer import (
    ConsensusEvaluationReport,
    ConsensusEvaluator,
    FactSynthesizer,
    KeyQuote,
    QuantitativeMetric,
    SourceCitation,
    SynthesizedInsight,
    SynthesisResult,
    TimelineEvent,
)
from deepsearch_research_agent.contradiction_detector import (
    FactClaim,
    ContradictionRecord,
    ContradictionReport,
    detect_contradictions,
)
from deepsearch_research_agent.evidence_graph import (
    CircularCitationCycle,
    EvidenceEdge,
    EvidenceGraph,
    EvidenceNode,
    ProvenanceTrace,
    build_evidence_graph_from_synthesis,
)

__version__ = "1.0.0"

__all__ = [
    # compat
    "atomic_write_text",
    "atomic_write_bytes",
    "ensure_dir",
    "get_platform_info",
    "is_termux",
    "is_windows",
    "is_macos",
    "is_linux",
    "open_in_browser",
    "safe_filename",
    "to_posix_path",
    # planner
    "ResearchPlanner",
    "ResearchPlan",
    "InvestigationAngle",
    "QueryVariation",
    "ResearchBudget",
    # crawler
    "WebCrawler",
    "HTMLTextExtractor",
    "MockSearchEngine",
    "CrawlResult",
    "ExtractedDocument",
    "compute_credibility_score",
    # synthesizer
    "FactSynthesizer",
    "ConsensusEvaluator",
    "SynthesisResult",
    "SynthesizedInsight",
    "QuantitativeMetric",
    "TimelineEvent",
    "KeyQuote",
    "SourceCitation",
    "ConsensusEvaluationReport",
    # report engine
    "ReportGenerator",
    "SVGChartGenerator",
    # contradiction detector
    "FactClaim",
    "ContradictionRecord",
    "ContradictionReport",
    "detect_contradictions",
    # evidence graph
    "EvidenceNode",
    "EvidenceEdge",
    "CircularCitationCycle",
    "ProvenanceTrace",
    "EvidenceGraph",
    "build_evidence_graph_from_synthesis",
]
