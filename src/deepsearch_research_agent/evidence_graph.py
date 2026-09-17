"""Evidence Provenance Graph, Circular Citation Detection, and Authority Propagation.

Constructs directed evidence graphs for autonomous deep research:
1. Traces citation lineages and claim provenance back to primary sources.
2. Detects circular reporting, echo chambers, and self-referential loops.
3. Computes TrustRank / eigenvector authority scores across evidence chains.
4. Generates Material 3-styled SVG network graphs and structured audit tables.

100% Python Standard Library (3.9-3.13). Zero external runtime dependencies.
"""

from __future__ import annotations

import html
import math
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class EvidenceNode:
    """A discrete node in the research evidence provenance graph."""

    node_id: str
    node_type: str  # 'primary_source', 'document', 'claim', 'metric', 'derived_conclusion'
    label: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    authority_score: float = 1.0  # Computed credibility/authority rating

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "label": self.label,
            "metadata": self.metadata,
            "authority_score": round(self.authority_score, 4),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvidenceNode:
        return cls(
            node_id=str(data["node_id"]),
            node_type=str(data.get("node_type", "document")),
            label=str(data.get("label", "")),
            metadata=dict(data.get("metadata", {})),
            authority_score=float(data.get("authority_score", 1.0)),
        )


@dataclass
class EvidenceEdge:
    """A directed relationship between evidence nodes."""

    source_id: str
    target_id: str
    relation: str  # 'cites', 'supports', 'refutes', 'corroborates', 'derives_from'
    weight: float = 1.0
    evidence_snippet: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
            "weight": round(self.weight, 3),
            "evidence_snippet": self.evidence_snippet,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvidenceEdge:
        return cls(
            source_id=str(data["source_id"]),
            target_id=str(data["target_id"]),
            relation=str(data.get("relation", "cites")),
            weight=float(data.get("weight", 1.0)),
            evidence_snippet=str(data.get("evidence_snippet", "")),
        )


@dataclass
class CircularCitationCycle:
    """A detected loop or echo chamber in the citation network."""

    cycle_path: List[str]
    cycle_type: str  # 'circular_reporting', 'echo_chamber', 'self_citation'
    severity: str    # 'critical', 'high', 'medium'
    nodes_involved: List[str]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProvenanceTrace:
    """Ancestry lineage trace for a specific research claim or conclusion."""

    target_id: str
    root_sources: List[Dict[str, Any]]
    paths: List[List[str]]
    max_depth: int
    is_grounded: bool
    circular_dependencies: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Evidence Graph Engine
# ---------------------------------------------------------------------------

class EvidenceGraph:
    """Directed graph representing claims, sources, and citation provenance."""

    def __init__(self) -> None:
        self.nodes: Dict[str, EvidenceNode] = {}
        self.edges: List[EvidenceEdge] = []
        self._adj: Dict[str, List[str]] = {}       # source -> [targets]
        self._rev_adj: Dict[str, List[str]] = {}   # target -> [sources]

    def add_node(
        self,
        node_or_id: Union[EvidenceNode, str, None] = None,
        node_type: str = "document",
        label: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        authority_score: float = 1.0,
        node_id: Optional[str] = None,
    ) -> EvidenceNode:
        """Add or update an evidence node."""
        actual_id = node_or_id if node_or_id is not None else node_id
        if actual_id is None:
            raise ValueError("Must provide node_or_id or node_id")
        if isinstance(actual_id, EvidenceNode):
            node = actual_id
        else:
            node = EvidenceNode(
                node_id=str(actual_id),
                node_type=node_type,
                label=label or str(actual_id),
                metadata=metadata or {},
                authority_score=authority_score,
            )

        self.nodes[node.node_id] = node
        if node.node_id not in self._adj:
            self._adj[node.node_id] = []
        if node.node_id not in self._rev_adj:
            self._rev_adj[node.node_id] = []
        return node

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation: str = "cites",
        weight: float = 1.0,
        evidence_snippet: str = "",
    ) -> EvidenceEdge:
        """Add a directed edge between nodes. Automatically registers nodes if absent."""
        if source_id not in self.nodes:
            self.add_node(source_id, label=source_id)
        if target_id not in self.nodes:
            self.add_node(target_id, label=target_id)

        edge = EvidenceEdge(
            source_id=source_id,
            target_id=target_id,
            relation=relation,
            weight=weight,
            evidence_snippet=evidence_snippet,
        )
        self.edges.append(edge)
        self._adj[source_id].append(target_id)
        self._rev_adj[target_id].append(source_id)
        return edge

    def get_node(self, node_id: str) -> Optional[EvidenceNode]:
        """Retrieve node by ID."""
        return self.nodes.get(node_id)

    def detect_circular_citations(self) -> List[CircularCitationCycle]:
        """Detect all simple cycles in the directed graph using DFS cycle backtracking."""
        visited: Set[str] = set()
        rec_stack: List[str] = []
        rec_set: Set[str] = set()
        detected_cycles: List[List[str]] = []

        def dfs(u: str) -> None:
            visited.add(u)
            rec_stack.append(u)
            rec_set.add(u)

            for v in self._adj.get(u, []):
                if v not in visited:
                    dfs(v)
                elif v in rec_set:
                    # Found cycle: extract from v to u
                    idx = rec_stack.index(v)
                    cycle = rec_stack[idx:] + [v]
                    # Normalize cycle representation for deduplication
                    core = cycle[:-1]
                    min_idx = core.index(min(core))
                    norm = core[min_idx:] + core[:min_idx]
                    if norm not in [c[:-1] for c in detected_cycles]:
                        detected_cycles.append(norm + [norm[0]])

            rec_stack.pop()
            rec_set.remove(u)

        for node_id in sorted(self.nodes.keys()):
            if node_id not in visited:
                dfs(node_id)

        cycles: List[CircularCitationCycle] = []
        for c in detected_cycles:
            length = len(c) - 1
            if length == 1:
                ctype = "self_citation"
                sev = "medium"
                desc = f"Node '{c[0]}' contains a recursive self-referential loop."
            elif length == 2:
                ctype = "circular_reporting"
                sev = "critical"
                desc = f"Direct mutual citation detected between '{c[0]}' and '{c[1]}' (potential circular reporting)."
            else:
                ctype = "echo_chamber"
                sev = "high"
                chain = " -> ".join(c)
                desc = f"Multi-hop echo chamber cycle ({length} nodes): {chain}"

            cycles.append(
                CircularCitationCycle(
                    cycle_path=c,
                    cycle_type=ctype,
                    severity=sev,
                    nodes_involved=list(set(c[:-1])),
                    explanation=desc,
                )
            )

        return cycles

    def detect_echo_chambers(self) -> List[Dict[str, Any]]:
        """Identify closed clusters of claims/sources that reference each other without external root evidence."""
        cycles = self.detect_circular_citations()
        if not cycles:
            return []

        echo_groups: List[Dict[str, Any]] = []
        for cyc in cycles:
            # Check if any node in the cycle has an incoming edge from an external primary source
            cycle_nodes = set(cyc.nodes_involved)
            external_inputs = 0
            for n in cycle_nodes:
                for parent in self._rev_adj.get(n, []):
                    if parent not in cycle_nodes:
                        parent_node = self.nodes.get(parent)
                        if parent_node and parent_node.node_type in ("primary_source", "document"):
                            external_inputs += 1

            is_isolated = (external_inputs == 0)
            echo_groups.append({
                "cycle": cyc.cycle_path,
                "nodes": list(cycle_nodes),
                "is_isolated_echo_chamber": is_isolated,
                "external_grounding_sources": external_inputs,
                "severity": "critical" if is_isolated else "warning",
            })
        return echo_groups

    def compute_eigenvector_authority(
        self,
        damping: float = 0.85,
        max_iter: int = 50,
        tol: float = 1e-6,
    ) -> Dict[str, float]:
        """Compute TrustRank / PageRank-style credibility flow across evidence edges."""
        n = len(self.nodes)
        if n == 0:
            return {}

        node_keys = sorted(self.nodes.keys())
        # Base seed from initial metadata credibility_score
        initial_seeds: Dict[str, float] = {}
        total_seed = 0.0
        for k in node_keys:
            node = self.nodes[k]
            seed = float(node.metadata.get("credibility_score", 1.0))
            if node.node_type == "primary_source":
                seed *= 1.5
            initial_seeds[k] = max(0.1, seed)
            total_seed += initial_seeds[k]

        # Normalize seeds
        for k in node_keys:
            initial_seeds[k] /= total_seed

        scores = dict(initial_seeds)

        # Relation multipliers
        rel_mult = {
            "supports": 1.2,
            "corroborates": 1.1,
            "cites": 1.0,
            "derives_from": 0.9,
            "refutes": -0.5,
        }

        for _ in range(max_iter):
            new_scores: Dict[str, float] = {k: (1.0 - damping) * initial_seeds[k] for k in node_keys}

            for edge in self.edges:
                src, tgt = edge.source_id, edge.target_id
                if src in self.nodes and tgt in self.nodes:
                    out_deg = max(1, len(self._adj.get(src, [])))
                    mult = rel_mult.get(edge.relation, 1.0)
                    transfer = (scores[src] / out_deg) * mult * edge.weight
                    new_scores[tgt] += damping * transfer

            # Clamp negative scores to 0.01
            for k in node_keys:
                new_scores[k] = max(0.01, new_scores[k])

            # Normalize sum to 1.0
            s_sum = sum(new_scores.values()) or 1.0
            for k in node_keys:
                new_scores[k] /= s_sum

            # Check convergence
            diff = sum(abs(new_scores[k] - scores[k]) for k in node_keys)
            scores = new_scores
            if diff < tol:
                break

        # Scale scores to 0.0 - 100.0 for intuitive inspection
        max_s = max(scores.values()) if scores else 1.0
        scaled_scores: Dict[str, float] = {}
        for k, v in scores.items():
            scaled = round((v / max_s) * 100.0, 2)
            scaled_scores[k] = scaled
            self.nodes[k].authority_score = scaled

        return scaled_scores

    def trace_provenance(self, node_id: str, max_depth: int = 10) -> ProvenanceTrace:
        """Trace the full upstream lineage of an evidence node back to primary sources."""
        if node_id not in self.nodes:
            return ProvenanceTrace(
                target_id=node_id,
                root_sources=[],
                paths=[],
                max_depth=0,
                is_grounded=False,
                circular_dependencies=[],
            )

        paths: List[List[str]] = []
        cycles_found: Set[str] = set()

        def dfs_trace(curr: str, path: List[str], depth: int) -> None:
            if depth > max_depth:
                paths.append(list(path))
                return

            parents = self._rev_adj.get(curr, [])
            if not parents:
                paths.append(list(path))
                return

            for p in parents:
                if p in path:
                    cycles_found.add(f"{curr} -> {p}")
                    paths.append(list(path) + [p + " [CYCLE]"])
                else:
                    dfs_trace(p, path + [p], depth + 1)

        dfs_trace(node_id, [node_id], 0)

        # Collect root sources
        root_nodes: Dict[str, Dict[str, Any]] = {}
        for p in paths:
            terminal = p[-1].replace(" [CYCLE]", "")
            if terminal in self.nodes:
                tnode = self.nodes[terminal]
                if tnode.node_type in ("primary_source", "document") or len(self._rev_adj.get(terminal, [])) == 0:
                    root_nodes[terminal] = tnode.to_dict()

        is_grounded = any(
            r.get("node_type") in ("primary_source", "document") for r in root_nodes.values()
        ) and len(cycles_found) == 0

        actual_max_depth = max((len(p) for p in paths), default=0)

        return ProvenanceTrace(
            target_id=node_id,
            root_sources=list(root_nodes.values()),
            paths=paths,
            max_depth=actual_max_depth,
            is_grounded=is_grounded,
            circular_dependencies=sorted(list(cycles_found)),
        )

    def generate_svg_graph(
        self,
        width: int = 900,
        height: int = 600,
        title: str = "DeepSearch Provenance & Evidence Graph",
    ) -> str:
        """Render a standalone, Material 3-styled SVG visualization of the evidence network."""
        # Compute 2D layout positions using radial/concentric or force-directed coordinates
        node_keys = sorted(self.nodes.keys())
        node_count = len(node_keys)
        positions: Dict[str, Tuple[float, float]] = {}

        if node_count == 0:
            return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><text x="50%" y="50%" fill="#888">Empty Graph</text></svg>'

        # Center point
        cx, cy = width / 2.0, height / 2.0 + 20
        radius_x = (width - 160) / 2.0
        radius_y = (height - 180) / 2.0

        for i, k in enumerate(node_keys):
            angle = (2.0 * math.pi * i) / node_count
            px = cx + radius_x * math.cos(angle)
            py = cy + radius_y * math.sin(angle)
            positions[k] = (px, py)

        # Detect cycles for highlight styling
        cycles = self.detect_circular_citations()
        cycle_nodes: Set[str] = set()
        for c in cycles:
            cycle_nodes.update(c.nodes_involved)

        # SVG palette influenced by Material 3 tokens
        bg_color = "#111318"          # surface
        surface_card = "#1e1f25"      # surface-container
        primary_color = "#a8c7fa"     # primary
        accent_color = "#81c995"      # tertiary (green)
        warning_color = "#fdd663"     # warning yellow
        danger_color = "#f28b82"      # error red
        text_primary = "#e2e2e9"      # on-surface
        text_dim = "#9da3ae"          # outline / dim text

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
            f'  <defs>',
            f'    <marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">',
            f'      <polygon points="0 0, 8 3, 0 6" fill="{primary_color}" opacity="0.8"/>',
            f'    </marker>',
            f'    <marker id="arrow-danger" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">',
            f'      <polygon points="0 0, 8 3, 0 6" fill="{danger_color}" opacity="0.9"/>',
            f'    </marker>',
            f'    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">',
            f'      <feGaussianBlur stdDeviation="4" result="blur"/>',
            f'      <feComposite in="SourceGraphic" in2="blur" operator="over"/>',
            f'    </filter>',
            f'  </defs>',
            f'  <!-- Background Canvas -->',
            f'  <rect width="{width}" height="{height}" fill="{bg_color}" rx="12"/>',
            f'  <!-- Grid Pattern -->',
            f'  <g stroke="#282a30" stroke-width="0.5" stroke-dasharray="4,4">',
        ]

        # Light grid lines
        for gx in range(40, width, 80):
            svg_parts.append(f'    <line x1="{gx}" y1="40" x2="{gx}" y2="{height-20}"/>')
        for gy in range(40, height, 80):
            svg_parts.append(f'    <line x1="40" y1="{gy}" x2="{width-40}" y2="{gy}"/>')
        svg_parts.append(f'  </g>')

        # Title and Header
        svg_parts.append(f'  <g transform="translate(24, 32)">')
        svg_parts.append(f'    <text fill="{primary_color}" font-family="Roboto, sans-serif" font-size="16" font-weight="bold">{html.escape(title)}</text>')
        cycle_badge = f' | Cycles Detected: {len(cycles)}' if cycles else ' | Provenance Integrity: Verified'
        badge_color = danger_color if cycles else accent_color
        svg_parts.append(f'    <text x="0" y="20" fill="{badge_color}" font-family="Roboto, sans-serif" font-size="12">{badge_color and cycle_badge}</text>')
        svg_parts.append(f'  </g>')

        # Draw Edges
        svg_parts.append(f'  <!-- Directed Edges -->')
        for edge in self.edges:
            if edge.source_id in positions and edge.target_id in positions:
                x1, y1 = positions[edge.source_id]
                x2, y2 = positions[edge.target_id]
                is_in_cycle = edge.source_id in cycle_nodes and edge.target_id in cycle_nodes
                stroke = danger_color if is_in_cycle else primary_color
                marker = "arrow-danger" if is_in_cycle else "arrow"
                opacity = "0.9" if is_in_cycle else "0.5"
                width_line = "2.5" if is_in_cycle else "1.5"

                svg_parts.append(
                    f'    <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                    f'stroke="{stroke}" stroke-width="{width_line}" stroke-opacity="{opacity}" '
                    f'marker-end="url(#{marker})"/>'
                )

                # Edge relation label
                mid_x = (x1 + x2) / 2.0
                mid_y = (y1 + y2) / 2.0
                rel_clean = edge.relation.replace("_", " ")
                svg_parts.append(
                    f'    <text x="{mid_x:.1f}" y="{mid_y - 4:.1f}" fill="{text_dim}" '
                    f'font-family="Roboto, sans-serif" font-size="9" text-anchor="middle">{rel_clean}</text>'
                )

        # Draw Nodes
        svg_parts.append(f'  <!-- Evidence Nodes -->')
        for k, (nx, ny) in positions.items():
            node = self.nodes[k]
            in_cycle = k in cycle_nodes
            border_color = danger_color if in_cycle else (accent_color if node.node_type == "primary_source" else primary_color)
            glow_attr = 'filter="url(#glow)"' if in_cycle else ''

            # Node card box
            box_w, box_h = 130, 48
            bx = nx - box_w / 2.0
            by = ny - box_h / 2.0

            svg_parts.append(f'    <g transform="translate({bx:.1f}, {by:.1f})" {glow_attr}>')
            svg_parts.append(
                f'      <rect width="{box_w}" height="{box_h}" rx="8" fill="{surface_card}" '
                f'stroke="{border_color}" stroke-width="2"/>'
            )
            # Node Type pill
            type_pill = node.node_type.replace("_", " ").upper()[:12]
            svg_parts.append(
                f'      <text x="8" y="16" fill="{border_color}" font-family="Roboto, sans-serif" '
                f'font-size="9" font-weight="bold">{type_pill}</text>'
            )
            # Authority score pill
            svg_parts.append(
                f'      <text x="{box_w - 8}" y="16" fill="{text_dim}" font-family="Roboto, sans-serif" '
                f'font-size="9" text-anchor="end">{node.authority_score:.1f}</text>'
            )
            # Node Label (truncated)
            disp_label = (node.label[:18] + '..') if len(node.label) > 18 else node.label
            svg_parts.append(
                f'      <text x="8" y="34" fill="{text_primary}" font-family="Roboto, sans-serif" '
                f'font-size="11" font-weight="500">{html.escape(disp_label)}</text>'
            )
            svg_parts.append(f'    </g>')

        svg_parts.append(f'</svg>')
        return "\n".join(svg_parts)

    def export_audit_markdown(self) -> str:
        """Produce a structured Markdown audit table documenting all claims and provenance."""
        lines = [
            "# DeepSearch Evidence Provenance & Citation Audit",
            "",
            f"**Total Nodes**: {len(self.nodes)} | **Total Directed Edges**: {len(self.edges)}",
            "",
            "## 1. Network Nodes & Computed Authority",
            "",
            "| Node ID | Type | Label | Authority | In-Degree | Out-Degree | Grounded |",
            "|:---|:---|:---|:---|:---|:---|:---|",
        ]

        cycles = self.detect_circular_citations()
        cycle_nodes = set()
        for c in cycles:
            cycle_nodes.update(c.nodes_involved)

        for k in sorted(self.nodes.keys()):
            node = self.nodes[k]
            in_deg = len(self._rev_adj.get(k, []))
            out_deg = len(self._adj.get(k, []))
            grounded = "No (Cycle)" if k in cycle_nodes else ("Yes" if in_deg > 0 or node.node_type == "primary_source" else "Single/Root")
            lines.append(
                f"| `{node.node_id}` | {node.node_type} | {node.label} | **{node.authority_score:.1f}** | {in_deg} | {out_deg} | {grounded} |"
            )

        lines.extend([
            "",
            "## 2. Circular Citation & Echo Chamber Analysis",
            "",
        ])

        if not cycles:
            lines.append("✓ **Zero circular citations detected.** Evidence graph is a clean Directed Acyclic Graph (DAG).")
        else:
            lines.append(f"⚠️ **Detected {len(cycles)} circular loops or echo chambers:**")
            lines.append("")
            for idx, cyc in enumerate(cycles, 1):
                path_str = " &rarr; ".join(f"`{n}`" for n in cyc.cycle_path)
                lines.append(f"**{idx}. [{cyc.severity.upper()}] {cyc.cycle_type}**: {path_str}")
                lines.append(f"- *Explanation*: {cyc.explanation}")
                lines.append("")

        lines.extend([
            "---",
            "*Audit generated by DeepSearch Research Agent Evidence Provenance Engine.*",
        ])
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize complete graph to dictionary."""
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
            "circular_cycles": [c.to_dict() for c in self.detect_circular_citations()],
            "echo_chambers": self.detect_echo_chambers(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvidenceGraph:
        """Reconstruct graph from dictionary."""
        graph = cls()
        for n_data in data.get("nodes", []):
            graph.add_node(EvidenceNode.from_dict(n_data))
        for e_data in data.get("edges", []):
            graph.add_edge(
                source_id=e_data["source_id"],
                target_id=e_data["target_id"],
                relation=e_data.get("relation", "cites"),
                weight=float(e_data.get("weight", 1.0)),
                evidence_snippet=e_data.get("evidence_snippet", ""),
            )
        return graph


# ---------------------------------------------------------------------------
# Synthesis Builder Helper
# ---------------------------------------------------------------------------

def build_evidence_graph_from_synthesis(synthesis_data: Union[Dict[str, Any], Any]) -> EvidenceGraph:
    """Build an EvidenceGraph automatically from synthesis results, citations, and claims."""
    graph = EvidenceGraph()

    if not isinstance(synthesis_data, dict):
        if hasattr(synthesis_data, "to_dict"):
            synthesis_data = synthesis_data.to_dict()
        else:
            return graph

    citations = synthesis_data.get("citations", [])
    # Add source citation nodes
    for cit in citations:
        c_id = f"source_{cit.get('citation_id', 1)}"
        graph.add_node(
            node_id=c_id,
            node_type="primary_source",
            label=cit.get("title", c_id),
            metadata={
                "url": cit.get("url", ""),
                "domain": cit.get("domain", ""),
                "credibility_score": cit.get("credibility_score", 0.8),
            },
        )

    # Add insight nodes & citation edges
    insights = synthesis_data.get("insights", [])
    for idx, ins in enumerate(insights, 1):
        ins_id = f"insight_{idx}"
        graph.add_node(
            node_id=ins_id,
            node_type="derived_conclusion",
            label=ins.get("title", f"Insight {idx}"),
            metadata={
                "category": ins.get("category", "general"),
                "consensus_level": ins.get("consensus_level", "High Consensus"),
            },
        )
        for c_idx in ins.get("supporting_citations", []):
            src_node = f"source_{c_idx}"
            graph.add_edge(
                source_id=src_node,
                target_id=ins_id,
                relation="supports",
                weight=1.2,
                evidence_snippet=ins.get("summary", ""),
            )

    # Add quantitative metrics
    metrics = synthesis_data.get("metrics", [])
    for idx, met in enumerate(metrics, 1):
        met_id = f"metric_{idx}"
        val_str = f"{met.get('value')} {met.get('unit', '')}".strip()
        graph.add_node(
            node_id=met_id,
            node_type="metric",
            label=f"{met.get('label', 'Metric')}: {val_str}",
            metadata={"raw_text": met.get("raw_text", "")},
        )
        c_idx = met.get("citation_idx")
        if c_idx:
            graph.add_edge(
                source_id=f"source_{c_idx}",
                target_id=met_id,
                relation="derives_from",
                weight=1.0,
            )

    # Compute authority scores
    graph.compute_eigenvector_authority()
    return graph
