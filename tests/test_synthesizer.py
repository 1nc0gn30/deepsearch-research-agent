"""
test_synthesizer.py - Unit tests for synthesizer.py (FactSynthesizer, ConsensusEvaluator, Metrics, Citations).
"""

import pytest
from deepsearch_research_agent.crawler import CrawlResult
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


@pytest.fixture
def sample_crawl_results():
    """Fixture providing diverse simulated crawl results."""
    return [
        CrawlResult(
            url="https://arxiv.org/abs/2501.12345",
            status_code=200,
            title="Transformer Latency Optimization: An Empirical Study",
            text="In 2024, researchers achieved a 42.5% reduction in attention latency. The foundational architecture utilizes FlashAttention-3. Peak throughput reached 85,000 requests per second under heavy load. A key limitation remains cold-start memory overhead.",
            markdown="# Transformer Latency Optimization\n> Reliable architectural synthesis requires rigorous cross-validation.",
            headings=["Transformer Latency Optimization"],
            metadata={"author": "Dr. Alice Smith", "description": "Benchmark study on LLM inference latency."},
            links=[],
            credibility_score=96.0,
            word_count=50,
            reading_time_min=0.25,
        ),
        CrawlResult(
            url="https://nature.com/articles/s41586-2025",
            status_code=200,
            title="Next-Generation Neural Accelerators and Kernel Design",
            text="In 2025, hardware innovations yielded 4.2x efficiency speedups across distributed clusters. Empirical benchmarks show memory overhead scaling sub-linearly. Future roadmaps point to optical interconnects by 2028.",
            markdown="# Neural Accelerators\nEmpirical benchmarks show memory overhead scaling sub-linearly.",
            headings=["Neural Accelerators"],
            metadata={"author": "Nature Computational Group"},
            links=[],
            credibility_score=97.0,
            word_count=45,
            reading_time_min=0.22,
        ),
        CrawlResult(
            url="https://docs.python.org/3/howto/async.html",
            status_code=200,
            title="Official Distributed Runtime Architecture Guide",
            text="The runtime architecture guarantees fault isolation. Mean request latency is measured at 14.8ms under standard workloads.",
            markdown="# Distributed Runtime Architecture Guide\nMean request latency is measured at 14.8ms.",
            headings=["Distributed Runtime Architecture Guide"],
            metadata={},
            links=[],
            credibility_score=95.0,
            word_count=30,
            reading_time_min=0.15,
        ),
    ]


def test_consensus_evaluator_overlap():
    """Verify keyword overlap calculation."""
    s1 = "Distributed runtime architecture optimizes throughput and latency."
    s2 = "The system design optimizes throughput and reduces request latency."
    s3 = "Unrelated biological study of plant genetics."

    overlap_high = ConsensusEvaluator.compute_claim_overlap(s1, s2)
    overlap_low = ConsensusEvaluator.compute_claim_overlap(s1, s3)

    assert overlap_high > 0.2
    assert overlap_low == 0.0


def test_consensus_evaluator_levels():
    """Verify consensus level classifications based on source count and credibility."""
    sources_high = [
        SourceCitation(citation_id=1, title="S1", url="https://arxiv.org/1", domain="arxiv.org", credibility_score=95.0),
        SourceCitation(citation_id=2, title="S2", url="https://nature.com/2", domain="nature.com", credibility_score=96.0),
        SourceCitation(citation_id=3, title="S3", url="https://mit.edu/3", domain="mit.edu", credibility_score=94.0),
    ]

    level, score = ConsensusEvaluator.evaluate_consensus(sources_high, has_divergence=False)
    assert level == "High Consensus"
    assert score >= 85.0

    # Divergence case
    level_div, score_div = ConsensusEvaluator.evaluate_consensus(sources_high, has_divergence=True)
    assert level_div == "Divergent / Contested"
    assert score_div < 80.0

    # Single source
    level_single, score_single = ConsensusEvaluator.evaluate_consensus([sources_high[0]], has_divergence=False)
    assert level_single == "Single Source / Preliminary"


def test_fact_synthesizer_bibliography(sample_crawl_results):
    """Verify bibliography generation with 1-indexed master citation list."""
    synthesizer = FactSynthesizer()
    bib = synthesizer.build_bibliography(sample_crawl_results)

    assert len(bib) == 3
    assert bib[0].citation_id == 1
    assert bib[1].citation_id == 2
    assert bib[2].citation_id == 3
    assert bib[0].url == "https://arxiv.org/abs/2501.12345"
    assert bib[0].author == "Dr. Alice Smith"
    assert bib[0].credibility_score >= 90.0


def test_fact_synthesizer_metric_extraction(sample_crawl_results):
    """Verify extraction of percentages, latency, throughput, and multiplier metrics."""
    synthesizer = FactSynthesizer()
    bib = synthesizer.build_bibliography(sample_crawl_results)
    metrics = synthesizer.extract_metrics(sample_crawl_results, bib)

    assert len(metrics) >= 3
    labels = [m.label.lower() for m in metrics]
    units = [m.unit for m in metrics]
    values = [m.value for m in metrics]

    assert "%" in units or any("latency" in l for l in labels)
    assert any(v == 42.5 for v in values)
    assert any(m.citation_idx in [1, 2, 3] for m in metrics)


def test_fact_synthesizer_timeline_extraction(sample_crawl_results):
    """Verify extraction and chronological sorting of timeline events."""
    synthesizer = FactSynthesizer()
    bib = synthesizer.build_bibliography(sample_crawl_results)
    events = synthesizer.extract_timeline(sample_crawl_results, bib)

    assert len(events) >= 2
    years = [e.year for e in events]
    # Verify chronological ordering
    assert years == sorted(years)
    assert 2024 in years
    assert 2025 in years


def test_fact_synthesizer_quote_extraction(sample_crawl_results):
    """Verify extraction of blockquotes and quotation marks."""
    synthesizer = FactSynthesizer()
    bib = synthesizer.build_bibliography(sample_crawl_results)
    quotes = synthesizer.extract_quotes(sample_crawl_results, bib)

    assert len(quotes) >= 1
    assert any("Reliable architectural synthesis" in q.quote for q in quotes)
    assert quotes[0].citation_idx == 1


def test_fact_synthesizer_full_synthesis(sample_crawl_results):
    """Verify complete end-to-end synthesis pipeline."""
    synthesizer = FactSynthesizer()
    result = synthesizer.synthesize("Deep Learning Inference Optimization", sample_crawl_results)

    assert isinstance(result, SynthesisResult)
    assert result.topic == "Deep Learning Inference Optimization"
    assert len(result.executive_summary) > 50
    assert "[^" in result.executive_summary  # Contains academic citation tags
    assert isinstance(result.consensus_report, ConsensusEvaluationReport)
    assert result.consensus_report.total_sources_evaluated == 3
    assert result.consensus_report.high_credibility_sources_count == 3
    assert len(result.insights) >= 2
    assert len(result.bibliography) == 3

    # Check that dictionary serialization works seamlessly
    d = result.to_dict()
    assert isinstance(d, dict)
    assert d["topic"] == "Deep Learning Inference Optimization"
