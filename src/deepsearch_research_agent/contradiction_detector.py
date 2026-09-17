"""Cross-Source Evidence Contradiction Detector and Fact Verification Matrix.

Scans research claims extracted across multiple web documents to detect:
1. Numeric divergence (e.g. market size estimates differing by >20%).
2. Temporal mismatches (e.g. conflicting release dates or historical milestones).
3. Polarity/Sentiment conflicts (e.g. conflicting efficacy or failure reports).

100% Python Standard Library. Zero external dependencies.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Union


@dataclass
class FactClaim:
    """A discrete verifiable factual assertion extracted from a research source."""

    claim_id: str
    source_url: str
    source_title: str
    statement: str
    entity: str
    attribute: str
    numeric_value: Optional[float] = None
    numeric_unit: Optional[str] = None
    date_value: Optional[str] = None
    sentiment_polarity: float = 0.0  # -1.0 (strongly negative) to +1.0 (strongly positive)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ContradictionRecord:
    """Identified factual contradiction between two source claims."""

    claim_a: FactClaim
    claim_b: FactClaim
    conflict_type: str  # 'numeric_divergence', 'temporal_mismatch', 'sentiment_conflict'
    divergence_ratio: float
    severity: str  # 'critical', 'major', 'minor'
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_a": self.claim_a.to_dict(),
            "claim_b": self.claim_b.to_dict(),
            "conflict_type": self.conflict_type,
            "divergence_ratio": round(self.divergence_ratio, 3),
            "severity": self.severity,
            "explanation": self.explanation,
        }


@dataclass
class ContradictionReport:
    """Comprehensive analysis of cross-source factual coherence and contradictions."""

    total_claims: int
    contradictions_count: int
    contradictions: List[ContradictionRecord]
    consensus_rate: float  # 0.0 to 100.0%
    is_disputed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_claims": self.total_claims,
            "contradictions_count": self.contradictions_count,
            "contradictions": [c.to_dict() for c in self.contradictions],
            "consensus_rate": round(self.consensus_rate, 1),
            "is_disputed": self.is_disputed,
        }


def detect_contradictions(
    claims: Sequence[Union[Dict[str, Any], FactClaim]],
    numeric_tolerance: float = 0.20,
) -> ContradictionReport:
    """Audit a collection of extracted fact claims for conflicts and disagreements.

    Args:
        claims: Sequence of FactClaim objects or dictionaries.
        numeric_tolerance: Maximum relative difference threshold before flagging numeric conflict (default 20%).

    Returns:
        ContradictionReport detailing all conflicting claim pairs and consensus rate.
    """
    parsed_claims: List[FactClaim] = []
    for c in claims:
        if isinstance(c, FactClaim):
            parsed_claims.append(c)
        elif isinstance(c, dict):
            parsed_claims.append(
                FactClaim(
                    claim_id=str(c.get("claim_id", f"claim-{len(parsed_claims)+1}")),
                    source_url=str(c.get("source_url", "")),
                    source_title=str(c.get("source_title", "")),
                    statement=str(c.get("statement", "")),
                    entity=str(c.get("entity", "")).strip().lower(),
                    attribute=str(c.get("attribute", "")).strip().lower(),
                    numeric_value=float(c["numeric_value"]) if c.get("numeric_value") is not None else None,
                    numeric_unit=str(c["numeric_unit"]) if c.get("numeric_unit") else None,
                    date_value=str(c["date_value"]) if c.get("date_value") else None,
                    sentiment_polarity=float(c.get("sentiment_polarity", 0.0)),
                )
            )

    if len(parsed_claims) < 2:
        return ContradictionReport(
            total_claims=len(parsed_claims),
            contradictions_count=0,
            contradictions=[],
            consensus_rate=100.0,
            is_disputed=False,
        )

    # Group claims by (entity, attribute)
    groups: Dict[tuple[str, str], List[FactClaim]] = {}
    for fc in parsed_claims:
        if fc.entity and fc.attribute:
            key = (fc.entity.strip().lower(), fc.attribute.strip().lower())
            groups.setdefault(key, []).append(fc)

    contradictions: List[ContradictionRecord] = []

    for (entity, attr), group in groups.items():
        if len(group) < 2:
            continue

        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                c1 = group[i]
                c2 = group[j]

                # 1. Numeric Divergence
                if c1.numeric_value is not None and c2.numeric_value is not None:
                    denom = max(abs(c1.numeric_value), abs(c2.numeric_value))
                    if denom > 0:
                        diff = abs(c1.numeric_value - c2.numeric_value) / denom
                        if diff > numeric_tolerance:
                            sev = "critical" if diff > 0.50 else "major"
                            unit_str = f" {c1.numeric_unit}" if c1.numeric_unit else ""
                            contradictions.append(
                                ContradictionRecord(
                                    claim_a=c1,
                                    claim_b=c2,
                                    conflict_type="numeric_divergence",
                                    divergence_ratio=diff,
                                    severity=sev,
                                    explanation=(
                                        f"Discrepancy of {round(diff * 100, 1)}% on '{entity}.{attr}': "
                                        f"{c1.source_title} claims {c1.numeric_value}{unit_str}, "
                                        f"whereas {c2.source_title} claims {c2.numeric_value}{unit_str}."
                                    ),
                                )
                            )

                # 2. Temporal Mismatch
                if c1.date_value and c2.date_value and c1.date_value != c2.date_value:
                    contradictions.append(
                        ContradictionRecord(
                            claim_a=c1,
                            claim_b=c2,
                            conflict_type="temporal_mismatch",
                            divergence_ratio=1.0,
                            severity="major",
                            explanation=(
                                f"Conflicting dates for '{entity}.{attr}': "
                                f"{c1.source_title} states '{c1.date_value}', "
                                f"but {c2.source_title} states '{c2.date_value}'."
                            ),
                        )
                    )

                # 3. Sentiment / Polarity Conflict
                if (c1.sentiment_polarity >= 0.4 and c2.sentiment_polarity <= -0.4) or (
                    c1.sentiment_polarity <= -0.4 and c2.sentiment_polarity >= 0.4
                ):
                    contradictions.append(
                        ContradictionRecord(
                            claim_a=c1,
                            claim_b=c2,
                            conflict_type="sentiment_conflict",
                            divergence_ratio=abs(c1.sentiment_polarity - c2.sentiment_polarity) / 2.0,
                            severity="critical",
                            explanation=(
                                f"Direct outcome contradiction on '{entity}.{attr}': "
                                f"{c1.source_title} reports positive result (polarity {c1.sentiment_polarity}), "
                                f"while {c2.source_title} reports negative result (polarity {c2.sentiment_polarity})."
                            ),
                        )
                    )

    total_possible_comparisons = max(1, len(parsed_claims) * (len(parsed_claims) - 1) // 2)
    consensus_rate = max(0.0, 100.0 - (len(contradictions) / total_possible_comparisons * 100.0))

    return ContradictionReport(
        total_claims=len(parsed_claims),
        contradictions_count=len(contradictions),
        contradictions=contradictions,
        consensus_rate=consensus_rate,
        is_disputed=len(contradictions) > 0,
    )
