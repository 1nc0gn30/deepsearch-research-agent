"""Unit tests for Evidence Provenance Graph, Circular Citation Detection, and Authority Engine."""

import json
import pytest
from deepsearch_research_agent.evidence_graph import (
    CircularCitationCycle,
    EvidenceEdge,
    EvidenceGraph,
    EvidenceNode,
    ProvenanceTrace,
    build_evidence_graph_from_synthesis,
)
from deepsearch_research_agent.mcp_server import MCPServer, deepsearch_evidence_graph
from deepsearch_research_agent.cli import build_parser, cmd_provenance, Colors


class TestEvidenceDataModels:
    def test_node_creation_and_dict(self):
        node = EvidenceNode(
            node_id="doc_1",
            node_type="primary_source",
            label="arXiv:2401.0001",
            metadata={"domain": "arxiv.org", "credibility_score": 0.95},
            authority_score=85.5,
        )
        d = node.to_dict()
        assert d["node_id"] == "doc_1"
        assert d["node_type"] == "primary_source"
        assert d["authority_score"] == 85.5
        
        reconstructed = EvidenceNode.from_dict(d)
        assert reconstructed.node_id == "doc_1"
        assert reconstructed.metadata["domain"] == "arxiv.org"

    def test_edge_creation_and_dict(self):
        edge = EvidenceEdge(
            source_id="doc_1",
            target_id="claim_1",
            relation="supports",
            weight=1.5,
            evidence_snippet="Experiment proves 2.3x speedup",
        )
        d = edge.to_dict()
        assert d["source_id"] == "doc_1"
        assert d["relation"] == "supports"
        assert d["weight"] == 1.5

        reconstructed = EvidenceEdge.from_dict(d)
        assert reconstructed.target_id == "claim_1"
        assert reconstructed.evidence_snippet == "Experiment proves 2.3x speedup"


class TestCycleAndEchoChamberDetection:
    def test_acyclic_dag_has_no_cycles(self):
        graph = EvidenceGraph()
        graph.add_node("source_1", node_type="primary_source")
        graph.add_node("claim_1", node_type="claim")
        graph.add_node("conclusion_1", node_type="derived_conclusion")

        graph.add_edge("source_1", "claim_1", relation="supports")
        graph.add_edge("claim_1", "conclusion_1", relation="derives_from")

        cycles = graph.detect_circular_citations()
        assert len(cycles) == 0
        echo_chambers = graph.detect_echo_chambers()
        assert len(echo_chambers) == 0

    def test_detect_direct_mutual_circular_reporting(self):
        graph = EvidenceGraph()
        # Source A cites Source B which cites Source A
        graph.add_node("source_A", node_type="document", label="Blog A")
        graph.add_node("source_B", node_type="document", label="News Outlet B")
        graph.add_edge("source_A", "source_B", relation="cites")
        graph.add_edge("source_B", "source_A", relation="cites")

        cycles = graph.detect_circular_citations()
        assert len(cycles) >= 1
        c = cycles[0]
        assert c.cycle_type == "circular_reporting"
        assert c.severity == "critical"
        assert "source_A" in c.nodes_involved
        assert "source_B" in c.nodes_involved

    def test_detect_multi_hop_echo_chamber(self):
        graph = EvidenceGraph()
        # Node 1 -> Node 2 -> Node 3 -> Node 1
        graph.add_edge("site_alpha", "forum_beta", relation="cites")
        graph.add_edge("forum_beta", "tweet_gamma", relation="cites")
        graph.add_edge("tweet_gamma", "site_alpha", relation="cites")

        cycles = graph.detect_circular_citations()
        assert len(cycles) >= 1
        c = cycles[0]
        assert c.cycle_type == "echo_chamber"
        assert len(c.nodes_involved) == 3

        echo_chambers = graph.detect_echo_chambers()
        assert len(echo_chambers) >= 1
        assert echo_chambers[0]["is_isolated_echo_chamber"] is True


class TestAuthorityAndProvenanceTracing:
    def test_eigenvector_authority_propagation(self):
        graph = EvidenceGraph()
        graph.add_node("peer_reviewed_paper", node_type="primary_source", metadata={"credibility_score": 1.0})
        graph.add_node("unverified_blog", node_type="document", metadata={"credibility_score": 0.2})
        graph.add_node("solid_claim", node_type="claim")
        graph.add_node("shaky_claim", node_type="claim")

        graph.add_edge("peer_reviewed_paper", "solid_claim", relation="supports", weight=2.0)
        graph.add_edge("unverified_blog", "shaky_claim", relation="cites", weight=0.5)

        scores = graph.compute_eigenvector_authority()
        assert "solid_claim" in scores
        assert "shaky_claim" in scores
        # Claim backed by peer reviewed primary source should have higher authority
        assert scores["solid_claim"] > scores["shaky_claim"]

    def test_trace_provenance_grounded(self):
        graph = EvidenceGraph()
        graph.add_node("root_doc", node_type="primary_source", label="Primary Document")
        graph.add_node("claim_x", node_type="claim", label="Claim X")
        graph.add_node("thesis_y", node_type="derived_conclusion", label="Thesis Y")

        graph.add_edge("root_doc", "claim_x", relation="supports")
        graph.add_edge("claim_x", "thesis_y", relation="derives_from")

        trace = graph.trace_provenance("thesis_y")
        assert trace.is_grounded is True
        assert len(trace.root_sources) == 1
        assert trace.root_sources[0]["node_id"] == "root_doc"
        assert trace.max_depth == 3

    def test_trace_provenance_ungrounded_circular(self):
        graph = EvidenceGraph()
        graph.add_edge("loop_a", "loop_b")
        graph.add_edge("loop_b", "loop_a")

        trace = graph.trace_provenance("loop_a")
        assert trace.is_grounded is False
        assert len(trace.circular_dependencies) > 0


class TestSynthesisIntegrationAndRendering:
    def test_build_from_synthesis_data(self):
        synthesis_mock = {
            "citations": [
                {"citation_id": 1, "title": "Study 1", "url": "https://doi.org/1", "credibility_score": 0.9},
                {"citation_id": 2, "title": "Study 2", "url": "https://doi.org/2", "credibility_score": 0.85},
            ],
            "insights": [
                {
                    "title": "Quantum Supremacy Verified",
                    "summary": "Verified across two benchmarks",
                    "supporting_citations": [1, 2],
                    "consensus_level": "High Consensus",
                }
            ],
            "metrics": [
                {
                    "label": "Quantum Error Rate",
                    "value": 0.001,
                    "unit": "%",
                    "citation_idx": 1,
                }
            ],
        }

        graph = build_evidence_graph_from_synthesis(synthesis_mock)
        assert len(graph.nodes) >= 4  # 2 citations + 1 insight + 1 metric
        assert len(graph.edges) >= 3
        assert graph.get_node("source_1") is not None
        assert graph.get_node("insight_1") is not None

    def test_generate_svg_graph(self):
        graph = EvidenceGraph()
        graph.add_node("src1", node_type="primary_source", label="Source Alpha")
        graph.add_node("claim1", node_type="claim", label="Claim Beta")
        graph.add_edge("src1", "claim1", relation="supports")
        graph.compute_eigenvector_authority()

        svg = graph.generate_svg_graph(width=800, height=500)
        assert "<svg" in svg
        assert "</svg>" in svg
        assert "Source Alpha" in svg
        assert "Claim Beta" in svg
        assert "#a8c7fa" in svg  # Material 3 primary color token

    def test_export_audit_markdown(self):
        graph = EvidenceGraph()
        graph.add_node("doc_1", node_type="primary_source", label="Doc 1")
        graph.add_node("claim_1", node_type="claim", label="Claim 1")
        graph.add_edge("doc_1", "claim_1", relation="supports")
        graph.compute_eigenvector_authority()

        md = graph.export_audit_markdown()
        assert "# DeepSearch Evidence Provenance & Citation Audit" in md
        assert "`doc_1`" in md
        assert "`claim_1`" in md
        assert "Zero circular citations detected" in md


class TestMCPEvidenceGraphTool:
    def test_mcp_tool_execution(self):
        server = MCPServer()
        args = {
            "nodes": [
                {"id": "docA", "node_type": "primary_source", "label": "Document A"},
                {"id": "docB", "node_type": "document", "label": "Document B"},
            ],
            "edges": [
                {"source": "docA", "target": "docB", "relation": "supports"},
            ],
            "include_svg": True,
            "trace_target": "docB",
        }
        res = server.call_tool("deepsearch_evidence_graph", args)
        assert res["isError"] is False
        body = json.loads(res["content"][0]["text"])
        assert body["status"] == "success"
        assert body["total_nodes"] == 2
        assert body["total_edges"] == 1
        assert body["svg"] is not None
        assert body["provenance_trace"]["is_grounded"] is True


class TestCLIProvenanceCommand:
    def test_cli_parser_and_execution(self, tmp_path, capsys):
        parser = build_parser()
        svg_out = str(tmp_path / "graph.svg")
        args = parser.parse_args(["provenance", "--export-svg", svg_out])
        
        c = Colors(force_disable=True)
        ret = cmd_provenance(args, c)
        assert ret == 0
        captured = capsys.readouterr()
        assert "DeepSearch Evidence Provenance & Citation Audit" in captured.out
        assert "SVG Evidence Graph saved" in captured.out

        # Verify SVG was written
        with open(svg_out, "r", encoding="utf-8") as f:
            content = f.read()
            assert "<svg" in content
