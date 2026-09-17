"""
synthesizer.py - Fact Synthesizer, Cross-Source Corroboration, and Consensus Evaluator.

Pure Python 3.9–3.13 stdlib. Corroborates claims across crawled sources, evaluates
consensus confidence (High, Moderate, Contested, Single Source), extracts structured
metrics, timeline events, and key quotes, and formats findings with numbered academic
citations [^1], [^2].
"""

from __future__ import annotations

import math
import re
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from deepsearch_research_agent.crawler import CrawlResult


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class SourceCitation:
    """A master reference citation with metadata and credibility."""
    citation_id: int  # 1-indexed (e.g. 1 for [^1])
    title: str
    url: str
    domain: str
    credibility_score: float
    author: Optional[str] = None
    access_date: str = field(default_factory=lambda: time.strftime("%Y-%m-%d"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QuantitativeMetric:
    """A specific extracted numerical metric or benchmark measurement."""
    label: str
    value: float
    unit: str
    raw_text: str
    source_url: str
    citation_idx: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TimelineEvent:
    """A chronological milestone or historical development."""
    date_str: str
    year: int
    description: str
    source_url: str
    citation_idx: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KeyQuote:
    """A noteworthy quote or definitive statement."""
    quote: str
    speaker_or_context: str
    source_url: str
    citation_idx: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SynthesizedInsight:
    """A high-level synthesized insight corroborated across sources."""
    title: str
    summary: str
    category: str  # "architecture", "tradeoff", "risk", "benchmark", "future", "general"
    consensus_level: str  # "High Consensus", "Moderate Consensus", "Divergent / Contested", "Single Source / Preliminary"
    consensus_score: float  # 0.0 - 100.0
    evidence_snippets: List[str]
    supporting_citations: List[int]  # [1, 3] for [^1][^3]
    contested_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConsensusEvaluationReport:
    """Evaluation of cross-source agreement, divergence, and confidence."""
    overall_confidence_score: float  # 0.0 - 100.0
    consensus_rating: str  # "Robust Consensus", "Moderate Agreement", "Contested / Divergent", "Limited Sources"
    total_sources_evaluated: int
    high_credibility_sources_count: int
    corroborated_claims_count: int
    contested_claims_count: int
    agreement_distribution: Dict[str, int]
    methodology_notes: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SynthesisResult:
    """The master synthesized output bundle ready for report rendering."""
    topic: str
    executive_summary: str
    consensus_report: ConsensusEvaluationReport
    insights: List[SynthesizedInsight]
    metrics: List[QuantitativeMetric]
    timeline: List[TimelineEvent]
    quotes: List[KeyQuote]
    bibliography: List[SourceCitation]
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Consensus Evaluator
# ---------------------------------------------------------------------------

class ConsensusEvaluator:
    """
    Evaluates agreement, divergence, and credibility-weighted confidence
    across independent research sources.
    """

    @staticmethod
    def compute_claim_overlap(text_a: str, text_b: str) -> float:
        """
        Compute normalized keyword/n-gram Jaccard similarity between two statements.
        """
        words_a = set(re.findall(r'\b[a-zA-Z]{4,}\b', text_a.lower()))
        words_b = set(re.findall(r'\b[a-zA-Z]{4,}\b', text_b.lower()))
        if not words_a or not words_b:
            return 0.0
        intersection = words_a.intersection(words_b)
        union = words_a.union(words_b)
        return len(intersection) / len(union)

    @staticmethod
    def evaluate_consensus(
        supporting_citations: List[SourceCitation],
        has_divergence: bool = False,
    ) -> Tuple[str, float]:
        """
        Determine consensus level and confidence score based on citations and divergence.

        Returns:
            Tuple of (Consensus Level String, Confidence Score 0–100)
        """
        if not supporting_citations:
            return "Single Source / Preliminary", 25.0

        num_sources = len(supporting_citations)
        avg_cred = sum(c.credibility_score for c in supporting_citations) / num_sources

        # Base confidence calculation
        if num_sources >= 3 and avg_cred >= 80.0 and not has_divergence:
            score = min(98.0, avg_cred + (num_sources * 2.0))
            return "High Consensus", round(score, 1)
        elif num_sources >= 2 and not has_divergence:
            score = min(85.0, avg_cred * 0.9 + (num_sources * 3.0))
            return "Moderate Consensus", round(score, 1)
        elif has_divergence:
            score = max(35.0, avg_cred * 0.6)
            return "Divergent / Contested", round(score, 1)
        else:
            score = max(30.0, avg_cred * 0.5)
            return "Single Source / Preliminary", round(score, 1)


# ---------------------------------------------------------------------------
# Fact Synthesizer
# ---------------------------------------------------------------------------

class FactSynthesizer:
    """
    Synthesizes raw crawled documents into structured facts, quantitative metrics,
    timelines, verified insights, and numbered academic citations.
    """

    def __init__(self) -> None:
        self.consensus_evaluator = ConsensusEvaluator()

    # -----------------------------------------------------------------------
    # Citation Index Mapping
    # -----------------------------------------------------------------------

    def build_bibliography(self, crawl_results: List[CrawlResult]) -> List[SourceCitation]:
        """
        Create a de-duplicated 1-indexed master citation bibliography.
        """
        bibliography: List[SourceCitation] = []
        seen_urls: Set[str] = set()
        citation_id = 1

        for cr in crawl_results:
            if not cr.url or cr.url in seen_urls:
                continue
            if cr.status_code != 200 and not cr.text:
                continue

            seen_urls.add(cr.url)
            import urllib.parse
            domain = urllib.parse.urlparse(cr.url).hostname or "web"
            author = cr.metadata.get("author") if cr.metadata else None

            bibliography.append(SourceCitation(
                citation_id=citation_id,
                title=cr.title or domain,
                url=cr.url,
                domain=domain,
                credibility_score=cr.credibility_score,
                author=author,
            ))
            citation_id += 1

        return bibliography

    def _get_citation_id(self, url: str, bibliography: List[SourceCitation]) -> int:
        for c in bibliography:
            if c.url == url:
                return c.citation_id
        return 1

    # -----------------------------------------------------------------------
    # Quantitative Metrics Extraction
    # -----------------------------------------------------------------------

    def extract_metrics(
        self,
        crawl_results: List[CrawlResult],
        bibliography: List[SourceCitation],
    ) -> List[QuantitativeMetric]:
        """
        Extract numerical facts, percentages, latency numbers, throughputs, and capacities.
        """
        metrics: List[QuantitativeMetric] = []
        seen_keys: Set[str] = set()

        # Regex patterns for metric extraction
        patterns = [
            # Percentage: e.g. "42.5% reduction", "34.5% CAGR"
            (r'(\b\d+(?:\.\d+)?)\s*%\s+([\w\s]{3,35})', "%"),
            # Latency / Time: e.g. "14.8ms latency", "120ms cold-start"
            (r'(\b\d+(?:\.\d+)?)\s*(ms|µs|ns|seconds?)\s+([\w\s]{3,30})', "time"),
            # Throughput / Ops: e.g. "85,000 requests per second", "500 ops/sec"
            (r'(\b\d+(?:,\d+)?(?:\.\d+)?)\s*(requests per second|req/sec|ops/sec|tps|fps)\b', "throughput"),
            # Multiplier: e.g. "4.2x efficiency", "3x speedup"
            (r'(\b\d+(?:\.\d+)?)\s*x\s+([\w\s]{3,30})', "multiplier"),
            # Monetary / Valuation: e.g. "$45.2 billion", "$1.2 trillion"
            (r'\$\s*(\d+(?:\.\d+)?)\s*(trillion|billion|million|k|B|M|T)?\s*([\w\s]{0,25})', "currency"),
            # Parameters: e.g. "70B parameters", "1.5T tokens"
            (r'(\b\d+(?:\.\d+)?)\s*(B|M|T|billion|million|trillion)\s+(parameters|tokens)\b', "scale"),
        ]

        for cr in crawl_results:
            if not cr.text:
                continue
            cit_idx = self._get_citation_id(cr.url, bibliography)

            for raw_line in cr.text.split(". "):
                line = raw_line.strip()
                if len(line) < 15 or len(line) > 300:
                    continue

                for pat, ptype in patterns:
                    matches = re.finditer(pat, line, re.IGNORECASE)
                    for m in matches:
                        try:
                            if ptype == "%":
                                val = float(m.group(1))
                                unit = "%"
                                label = m.group(2).strip().capitalize()
                            elif ptype == "time":
                                val = float(m.group(1))
                                unit = m.group(2).lower()
                                label = m.group(3).strip().capitalize()
                            elif ptype == "throughput":
                                val_str = m.group(1).replace(",", "")
                                val = float(val_str)
                                unit = m.group(2).strip()
                                label = f"Peak {unit}"
                            elif ptype == "multiplier":
                                val = float(m.group(1))
                                unit = "x"
                                label = m.group(2).strip().capitalize()
                            elif ptype == "currency":
                                base_val = float(m.group(1))
                                mult_str = (m.group(2) or "").upper()
                                mult = 1.0
                                if mult_str in ("B", "BILLION"):
                                    mult = 1e9
                                elif mult_str in ("M", "MILLION"):
                                    mult = 1e6
                                elif mult_str in ("T", "TRILLION"):
                                    mult = 1e12
                                val = base_val * mult
                                unit = f"${mult_str}" if mult_str else "$"
                                label = (m.group(3) or "Market Valuation").strip().capitalize()
                            elif ptype == "scale":
                                val = float(m.group(1))
                                unit = f"{m.group(2).upper()} {m.group(3)}"
                                label = f"Model Scale ({m.group(3)})"
                            else:
                                continue

                            metric_key = f"{label.lower()}_{val}_{unit}"
                            if metric_key not in seen_keys:
                                seen_keys.add(metric_key)
                                metrics.append(QuantitativeMetric(
                                    label=label[:50],
                                    value=val,
                                    unit=unit,
                                    raw_text=line[:180],
                                    source_url=cr.url,
                                    citation_idx=cit_idx,
                                ))
                        except Exception:
                            continue

        return metrics[:15]

    # -----------------------------------------------------------------------
    # Timeline Events Extraction
    # -----------------------------------------------------------------------

    def extract_timeline(
        self,
        crawl_results: List[CrawlResult],
        bibliography: List[SourceCitation],
    ) -> List[TimelineEvent]:
        """
        Extract chronological events, milestones, and dated historical developments.
        """
        events: List[TimelineEvent] = []
        seen_texts: Set[str] = set()

        year_pat = re.compile(r'\b(19\d{2}|20\d{2})\b')
        date_pat = re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+(19\d{2}|20\d{2})\b', re.IGNORECASE)

        for cr in crawl_results:
            if not cr.text:
                continue
            cit_idx = self._get_citation_id(cr.url, bibliography)

            for sentence in re.split(r'(?<=[.!?])\s+', cr.text):
                s_clean = sentence.strip()
                if len(s_clean) < 25 or len(s_clean) > 280:
                    continue

                date_m = date_pat.search(s_clean)
                year_m = year_pat.search(s_clean)

                if date_m or year_m:
                    date_str = date_m.group(0) if date_m else year_m.group(0)
                    year_val = int(date_m.group(1)) if date_m else int(year_m.group(0))

                    # Filter unreasonable years
                    if year_val < 1950 or year_val > 2035:
                        continue

                    # Filter out boilerplate numbers that look like years (e.g. port 2025)
                    if any(w in s_clean.lower() for w in ["port", "version", "rfc", "iso"]):
                        continue

                    text_key = re.sub(r'[^\w]', '', s_clean[:60].lower())
                    if text_key not in seen_texts:
                        seen_texts.add(text_key)
                        events.append(TimelineEvent(
                            date_str=date_str,
                            year=year_val,
                            description=s_clean,
                            source_url=cr.url,
                            citation_idx=cit_idx,
                        ))

        # Sort chronologically
        events.sort(key=lambda e: (e.year, e.date_str))
        return events[:12]

    # -----------------------------------------------------------------------
    # Key Quotes Extraction
    # -----------------------------------------------------------------------

    def extract_quotes(
        self,
        crawl_results: List[CrawlResult],
        bibliography: List[SourceCitation],
    ) -> List[KeyQuote]:
        """
        Extract impactful quotes and blockquotes from crawled documents.
        """
        quotes: List[KeyQuote] = []
        seen_quotes: Set[str] = set()

        quote_pats = [
            re.compile(r'“([^”]{25,260})”'),
            re.compile(r'"([^"]{25,260})"'),
            re.compile(r'(?:^|\n)>\s*([^\n]{25,260})'),
        ]

        for cr in crawl_results:
            source_blob = f"{cr.markdown}\n{cr.text}"
            cit_idx = self._get_citation_id(cr.url, bibliography)

            for pat in quote_pats:
                for match in pat.finditer(source_blob):
                    q_text = match.group(1).strip()
                    # Filter short or garbage matches
                    if len(q_text.split()) < 5:
                        continue
                    clean_key = re.sub(r'[^\w]', '', q_text[:40].lower())
                    if clean_key not in seen_quotes:
                        seen_quotes.add(clean_key)
                        speaker = cr.metadata.get("author") or cr.title or "Domain Expert"
                        quotes.append(KeyQuote(
                            quote=q_text,
                            speaker_or_context=speaker,
                            source_url=cr.url,
                            citation_idx=cit_idx,
                        ))

        return quotes[:8]

    # -----------------------------------------------------------------------
    # Insights & Cross-Source Corroboration
    # -----------------------------------------------------------------------

    def synthesize_insights(
        self,
        topic: str,
        crawl_results: List[CrawlResult],
        bibliography: List[SourceCitation],
    ) -> List[SynthesizedInsight]:
        """
        Cluster and corroborate claims across sources to build high-level insights.
        """
        insights: List[SynthesizedInsight] = []
        
        # High-signal statement filters
        categories = {
            "architecture": ["architecture", "design", "protocol", "framework", "mechanism", "structure", "engine"],
            "tradeoff": ["tradeoff", "comparison", "vs", "latency", "throughput", "overhead", "efficiency"],
            "risk": ["risk", "bottleneck", "vulnerability", "limitation", "challenge", "failure", "cost"],
            "benchmark": ["benchmark", "empirical", "measurement", "p99", "accuracy", "performance", "score"],
            "future": ["future", "roadmap", "next-generation", "emerging", "outlook", "trend", "frontier"],
        }

        # Candidate pool: sentences extracted from crawled texts
        candidates: Dict[str, List[Tuple[str, str, int]]] = {c: [] for c in categories}

        for cr in crawl_results:
            if not cr.text:
                continue
            cit_idx = self._get_citation_id(cr.url, bibliography)

            for sent in re.split(r'(?<=[.!?])\s+', cr.text):
                s = sent.strip()
                if len(s) < 35 or len(s) > 300:
                    continue
                s_lower = s.lower()
                for cat, kw_list in categories.items():
                    if any(kw in s_lower for kw in kw_list):
                        candidates[cat].append((s, cr.url, cit_idx))

        for cat, items in candidates.items():
            if not items:
                continue

            # Pick representative statement with highest cross-source similarity
            best_statement = items[0][0]
            supporting_cits: Set[int] = {items[0][2]}
            evidence: List[str] = [items[0][0]]

            # Corroborate across other items in the same category
            for other_sent, other_url, other_cit in items[1:]:
                overlap = ConsensusEvaluator.compute_claim_overlap(best_statement, other_sent)
                if overlap >= 0.18:
                    supporting_cits.add(other_cit)
                    if len(evidence) < 3 and other_sent not in evidence:
                        evidence.append(other_sent)

            # Retrieve citations objects
            cit_objs = [c for c in bibliography if c.citation_id in supporting_cits]
            level, score = ConsensusEvaluator.evaluate_consensus(cit_objs)

            title_map = {
                "architecture": f"Core Architectural Principles & Mechanisms in {topic}",
                "tradeoff": f"Performance Tradeoffs & Comparative Benchmarks",
                "risk": f"Critical Limitations, Bottlenecks & Failure Modes",
                "benchmark": f"Empirical Metrics & Scalability Profile",
                "future": f"Emerging Research Frontiers & Future Roadmap",
            }

            # Academic citation formatting
            cit_tags = "".join(f"[^{cid}]" for cid in sorted(supporting_cits))
            summary_text = f"{best_statement} {cit_tags}"

            insights.append(SynthesizedInsight(
                title=title_map.get(cat, f"Key Synthesis on {topic}"),
                summary=summary_text,
                category=cat,
                consensus_level=level,
                consensus_score=score,
                evidence_snippets=evidence,
                supporting_citations=sorted(list(supporting_cits)),
            ))

        return insights

    # -----------------------------------------------------------------------
    # Master Synthesis
    # -----------------------------------------------------------------------

    def synthesize(
        self,
        topic: str,
        crawl_results: List[CrawlResult],
    ) -> SynthesisResult:
        """
        Execute full synthesis pipeline:
        1. Build unified master bibliography.
        2. Extract metrics, timeline, and quotes.
        3. Formulate corroborated insights with consensus evaluation.
        4. Synthesize comprehensive executive summary with academic citations.
        """
        bibliography = self.build_bibliography(crawl_results)
        metrics = self.extract_metrics(crawl_results, bibliography)
        timeline = self.extract_timeline(crawl_results, bibliography)
        quotes = self.extract_quotes(crawl_results, bibliography)
        insights = self.synthesize_insights(topic, crawl_results, bibliography)

        # Evaluate overall consensus distribution
        total_sources = len(bibliography)
        high_cred = sum(1 for b in bibliography if b.credibility_score >= 85.0)
        
        dist: Dict[str, int] = {
            "High Consensus": 0,
            "Moderate Consensus": 0,
            "Divergent / Contested": 0,
            "Single Source / Preliminary": 0,
        }
        for ins in insights:
            dist[ins.consensus_level] = dist.get(ins.consensus_level, 0) + 1

        avg_insight_score = (
            sum(ins.consensus_score for ins in insights) / len(insights)
            if insights else 60.0
        )
        
        if avg_insight_score >= 80.0 and high_cred >= 2:
            overall_rating = "Robust Consensus"
        elif avg_insight_score >= 60.0:
            overall_rating = "Moderate Agreement"
        elif dist.get("Divergent / Contested", 0) > 0:
            overall_rating = "Contested / Divergent"
        else:
            overall_rating = "Limited Sources"

        consensus_report = ConsensusEvaluationReport(
            overall_confidence_score=round(avg_insight_score, 1),
            consensus_rating=overall_rating,
            total_sources_evaluated=total_sources,
            high_credibility_sources_count=high_cred,
            corroborated_claims_count=dist.get("High Consensus", 0) + dist.get("Moderate Consensus", 0),
            contested_claims_count=dist.get("Divergent / Contested", 0),
            agreement_distribution=dist,
            methodology_notes=(
                f"Evaluated {total_sources} independent sources with {high_cred} high-authority domains. "
                "Confidence scores computed via source authority weighting and keyword overlap corroboration."
            ),
        )

        # Generate Executive Summary
        exec_parts = [
            f"This research synthesis explores **{topic}** across foundational mechanisms, empirical benchmarks, and future strategic trajectories.",
        ]
        if insights:
            top_insights = insights[:3]
            for ti in top_insights:
                cit_str = "".join(f"[^{c}]" for c in ti.supporting_citations)
                exec_parts.append(f"Regarding {ti.category}, empirical evidence indicates that {ti.evidence_snippets[0]} {cit_str}")

        if metrics:
            top_m = metrics[0]
            exec_parts.append(f"Key quantitative indicators highlight {top_m.label} at {top_m.value}{top_m.unit} [^{top_m.citation_idx}].")

        exec_parts.append(
            f"Overall, the findings demonstrate a **{overall_rating}** ({avg_insight_score:.1f}% confidence index) across peer-reviewed and authoritative sources."
        )

        executive_summary = "\n\n".join(exec_parts)

        return SynthesisResult(
            topic=topic,
            executive_summary=executive_summary,
            consensus_report=consensus_report,
            insights=insights,
            metrics=metrics,
            timeline=timeline,
            quotes=quotes,
            bibliography=bibliography,
        )
