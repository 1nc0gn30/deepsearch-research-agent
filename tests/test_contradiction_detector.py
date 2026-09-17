"""Tests for evidence contradiction detector and verification matrix."""

from deepsearch_research_agent.contradiction_detector import (
    ContradictionReport,
    FactClaim,
    detect_contradictions,
)


def test_empty_claims():
    report = detect_contradictions([])
    assert isinstance(report, ContradictionReport)
    assert report.total_claims == 0
    assert report.contradictions_count == 0
    assert not report.is_disputed


def test_numeric_divergence_detection():
    claims = [
        FactClaim(
            claim_id="c1",
            source_url="https://source-a.com",
            source_title="Analyst Group A",
            statement="Global AI chip market is estimated at $45 billion in 2024.",
            entity="AI Chip Market",
            attribute="market_size_2024",
            numeric_value=45.0,
            numeric_unit="Billion USD",
        ),
        FactClaim(
            claim_id="c2",
            source_url="https://source-b.com",
            source_title="Research Firm B",
            statement="AI accelerators market reached $85B in 2024.",
            entity="ai chip market",
            attribute="market_size_2024",
            numeric_value=85.0,
            numeric_unit="Billion USD",
        ),
    ]

    report = detect_contradictions(claims, numeric_tolerance=0.20)
    assert report.total_claims == 2
    assert report.contradictions_count == 1
    assert report.is_disputed
    conflict = report.contradictions[0]
    assert conflict.conflict_type == "numeric_divergence"
    assert conflict.severity == "minor" or conflict.severity == "major" or conflict.severity == "critical"
    assert "Analyst Group A" in conflict.explanation
    assert "Research Firm B" in conflict.explanation


def test_temporal_and_sentiment_conflicts():
    claims = [
        # Temporal conflict
        {
            "claim_id": "c3",
            "source_title": "Source C",
            "entity": "quantum-processor",
            "attribute": "launch_date",
            "date_value": "2024-03-15",
        },
        {
            "claim_id": "c4",
            "source_title": "Source D",
            "entity": "quantum-processor",
            "attribute": "launch_date",
            "date_value": "2024-11-20",
        },
        # Sentiment conflict
        {
            "claim_id": "c5",
            "source_title": "Clinical Trial Alpha",
            "entity": "compound-x",
            "attribute": "trial_outcome",
            "sentiment_polarity": 0.85,
        },
        {
            "claim_id": "c6",
            "source_title": "FDA Warning Memo",
            "entity": "compound-x",
            "attribute": "trial_outcome",
            "sentiment_polarity": -0.75,
        },
    ]

    report = detect_contradictions(claims)
    assert report.total_claims == 4
    assert report.contradictions_count == 2
    types = [c.conflict_type for c in report.contradictions]
    assert "temporal_mismatch" in types
    assert "sentiment_conflict" in types
