"""
Unit & Integration Test Suite for DeepSearch Research Agent
Validates production examples, MCP client configurations, Google Deep Research Studio UI,
CI/CD workflow definitions, and architectural documentation.
"""

import json
import os
from pathlib import Path
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestQuantumComputingExample:
    """Test suite for examples/quantum-computing-brief/"""

    @property
    def example_dir(self) -> Path:
        return REPO_ROOT / "examples" / "quantum-computing-brief"

    def test_required_files_exist(self):
        expected_files = [
            "research_report.md",
            "report.html",
            "data_bundle.json",
            "README.md",
        ]
        for filename in expected_files:
            file_path = self.example_dir / filename
            assert file_path.exists(), f"Missing required file: {file_path}"
            assert file_path.stat().st_size > 0, f"File is empty: {file_path}"

    def test_data_bundle_json_schema(self):
        json_path = self.example_dir / "data_bundle.json"
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate top-level keys
        required_keys = [
            "research_metadata",
            "query_plan",
            "harvested_sources",
            "verified_claims",
            "quantitative_datapoints",
            "synthesis_tree",
        ]
        for key in required_keys:
            assert key in data, f"Missing key in data_bundle.json: {key}"

        # Validate research_metadata
        metadata = data["research_metadata"]
        assert "report_id" in metadata
        assert "query" in metadata
        assert metadata["depth_level"] == "exhaustive"
        assert metadata["consensus_confidence_score"] > 0.9

        # Validate query_plan
        plan = data["query_plan"]
        assert "stages" in plan
        assert len(plan["stages"]) >= 4
        for stage in plan["stages"]:
            assert "stage_index" in stage
            assert "name" in stage
            assert "sub_queries" in stage
            assert len(stage["sub_queries"]) > 0

        # Validate harvested_sources
        sources = data["harvested_sources"]
        assert len(sources) >= 4
        for src in sources:
            assert "source_id" in src
            assert "title" in src
            assert "url" in src
            assert "domain" in src
            assert "domain_authority" in src
            assert src["domain_authority"] >= 80

        # Validate verified_claims
        claims = data["verified_claims"]
        assert len(claims) >= 4
        for claim in claims:
            assert "claim_id" in claim
            assert "claim_statement" in claim
            assert claim["verification_status"] in ["Verified", "Contested", "Refuted"]
            assert 0.0 <= claim["confidence_score"] <= 1.0

        # Validate quantitative_datapoints
        metrics = data["quantitative_datapoints"]
        assert len(metrics) >= 3
        for metric in metrics:
            assert "metric" in metric
            assert "value" in metric
            assert "unit" in metric
            assert "entity" in metric

    def test_markdown_report_structure(self):
        md_path = self.example_dir / "research_report.md"
        content = md_path.read_text(encoding="utf-8")

        assert "# State of Fault-Tolerant Quantum Computing" in content
        assert "Executive Summary" in content
        assert "Quantum Error Correction" in content
        assert "Google Quantum AI" in content
        assert "IBM Quantum" in content
        assert "Harvard" in content or "QuEra" in content
        assert "Quantinuum" in content
        assert "Consensus & Contestation Matrix" in content
        assert "Citations" in content or "References" in content

    def test_html_report_rendering(self):
        html_path = self.example_dir / "report.html"
        content = html_path.read_text(encoding="utf-8")

        assert "<!DOCTYPE html>" in content
        assert "<title>" in content
        assert "--google-blue" in content
        assert "Google Quantum AI" in content
        assert "<table>" in content
        assert "Executive Summary" in content


class TestMarketIntelligenceExample:
    """Test suite for examples/market-intelligence-report/"""

    @property
    def example_dir(self) -> Path:
        return REPO_ROOT / "examples" / "market-intelligence-report"

    def test_required_files_exist(self):
        expected_files = [
            "ai_agents_market_2026.md",
            "sources.json",
            "README.md",
        ]
        for filename in expected_files:
            file_path = self.example_dir / filename
            assert file_path.exists(), f"Missing required file: {file_path}"
            assert file_path.stat().st_size > 0, f"File is empty: {file_path}"

    def test_sources_json_schema(self):
        json_path = self.example_dir / "sources.json"
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "report_metadata" in data
        assert "sources" in data
        sources = data["sources"]
        assert len(sources) >= 20, f"Expected at least 20 sources, got {len(sources)}"

        for src in sources:
            assert "source_key" in src
            assert "title" in src
            assert "author_organization" in src
            assert "domain" in src
            assert "url" in src
            assert "domain_authority" in src
            assert "credibility_rating" in src
            assert "key_findings" in src
            assert "cross_referenced_claims" in src
            assert len(src["cross_referenced_claims"]) > 0

    def test_markdown_report_structure(self):
        md_path = self.example_dir / "ai_agents_market_2026.md"
        content = md_path.read_text(encoding="utf-8")

        assert "Enterprise Autonomous AI Agents" in content
        assert "Executive Summary" in content
        assert "CAGR" in content or "Market Sizing" in content
        assert "Model Context Protocol" in content or "MCP" in content
        assert "Competitive Landscape" in content
        assert "Security" in content or "Governance" in content
        assert "ROI" in content or "Case Studies" in content


class TestMcpClientConfigs:
    """Test suite for examples/mcp-clients/"""

    @property
    def mcp_dir(self) -> Path:
        return REPO_ROOT / "examples" / "mcp-clients"

    def test_all_config_files_exist_and_valid_json(self):
        json_files = [
            "claude_desktop_config.json",
            "cursor_mcp.json",
            "cline_mcp.json",
            "zed_settings.json",
        ]
        for fname in json_files:
            path = self.mcp_dir / fname
            assert path.exists(), f"Missing config file: {path}"
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                assert isinstance(data, dict), f"{fname} must be a JSON object"
                # Check for either mcpServers or context_servers
                assert "mcpServers" in data or "context_servers" in data

    def test_mcp_readme_exists(self):
        readme = self.mcp_dir / "README.md"
        assert readme.exists()
        content = readme.read_text(encoding="utf-8")
        assert "Claude Desktop" in content
        assert "Cursor" in content
        assert "Cline" in content
        assert "Zed" in content
        assert "deep_research" in content


class TestExamplesRootReadme:
    """Test suite for examples/README.md"""

    def test_examples_index(self):
        readme = REPO_ROOT / "examples" / "README.md"
        assert readme.exists()
        content = readme.read_text(encoding="utf-8")
        assert "quantum-computing-brief" in content
        assert "market-intelligence-report" in content
        assert "mcp-clients" in content


class TestPublicStudioUi:
    """Test suite for public/index.html (Google Deep Research Studio UI)"""

    @property
    def html_path(self) -> Path:
        return REPO_ROOT / "public" / "index.html"

    def test_html_exists_and_offline_ready(self):
        assert self.html_path.exists()
        content = self.html_path.read_text(encoding="utf-8")

        # Zero external CDN script tags (100% offline ready)
        assert "<script src=" not in content.lower()
        # No external Google Fonts link tag to ensure offline execution
        assert "fonts.googleapis.com" not in content

    def test_google_material_tokens_and_branding(self):
        content = self.html_path.read_text(encoding="utf-8")

        # Google Developer Color Palette
        assert "#1a73e8" in content  # Google Blue
        assert "#1e8e3e" in content  # Google Green
        assert "#f9ab00" in content  # Google Yellow
        assert "#d93025" in content  # Google Red
        assert "#9334e6" in content  # Google Purple

        # Branding
        assert "Google Deep Research Studio" in content
        assert "google-dots" in content

    def test_interactive_workspaces_and_tabs(self):
        content = self.html_path.read_text(encoding="utf-8")

        # 6 workspace tabs / sections
        assert "Deep Research Studio" in content
        assert "Autonomous Query Planner" in content
        assert "Source &amp; Consensus Matrix" in content or "Source & Consensus Matrix" in content
        assert "Data Points &amp; SVG Visuals" in content or "Data Points & SVG Visuals" in content
        assert "AI Agent &amp; MCP Hub" in content or "AI Agent & MCP Hub" in content
        assert "Methodology" in content

        # Interactive controls
        assert "researchQueryInput" in content
        assert "setDepth" in content
        assert "loadPreset" in content
        assert "copyMcpConfig" in content
        assert "copyReportMarkdown" in content
        assert "downloadJSONBundle" in content

    def test_svg_visualizations(self):
        content = self.html_path.read_text(encoding="utf-8")
        assert "<svg" in content
        assert "<polygon" in content  # Radar chart
        assert "<rect" in content     # Bar chart


class TestGithubWorkflows:
    """Test suite for .github/workflows/"""

    def test_ci_workflow_matrix(self):
        ci_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
        assert ci_path.exists()
        content = ci_path.read_text(encoding="utf-8")
        workflow = yaml.safe_load(content)

        assert "jobs" in workflow
        assert "test-matrix" in workflow["jobs"]

        matrix = workflow["jobs"]["test-matrix"]["strategy"]["matrix"]
        os_list = matrix["os"]
        py_list = matrix["python-version"]

        # Check OS matrix (3 platforms)
        assert "ubuntu-latest" in os_list
        assert "macos-latest" in os_list
        assert "windows-latest" in os_list
        assert len(os_list) == 3

        # Check Python versions (5 versions: 3.9, 3.10, 3.11, 3.12, 3.13)
        expected_py = ["3.9", "3.10", "3.11", "3.12", "3.13"]
        for py in expected_py:
            assert py in py_list

        # Total matrix combinations: 3 * 5 = 15
        total_combinations = len(os_list) * len(py_list)
        assert total_combinations == 15, f"Expected 15 matrix jobs, got {total_combinations}"

    def test_release_workflow(self):
        rel_path = REPO_ROOT / ".github" / "workflows" / "release.yml"
        assert rel_path.exists()
        content = rel_path.read_text(encoding="utf-8")
        workflow = yaml.safe_load(content)

        assert "jobs" in workflow
        assert "build-and-release" in workflow["jobs"]
        assert "sha256sum" in content or "checksum" in content


class TestDocsAndRootReadme:
    """Test suite for docs/ and root README.md"""

    def test_documentation_guides_exist(self):
        docs = [
            "docs/RESEARCH_METHODOLOGY.md",
            "docs/MCP_GUIDE.md",
            "docs/QUERY_PLANNING_GUIDE.md",
            "README.md",
        ]
        for doc in docs:
            doc_path = REPO_ROOT / doc
            assert doc_path.exists(), f"Missing doc: {doc_path}"
            assert doc_path.stat().st_size > 500, f"Doc is too brief: {doc_path}"

    def test_research_methodology_content(self):
        path = REPO_ROOT / "docs" / "RESEARCH_METHODOLOGY.md"
        content = path.read_text(encoding="utf-8")
        assert "Stage 1: Recursive Query Decomposition" in content
        assert "Stage 2: Adaptive Evidence Harvesting" in content
        assert "Stage 3: Domain Authority" in content
        assert "Stage 4: Dialectical Consensus" in content
        assert "Stage 5: Multi-Perspective Synthesis" in content

    def test_mcp_guide_content(self):
        path = REPO_ROOT / "docs" / "MCP_GUIDE.md"
        content = path.read_text(encoding="utf-8")
        assert "deep_research" in content
        assert "plan_queries" in content
        assert "verify_claims" in content
        assert "extract_consensus" in content
        assert "search_knowledge_graph" in content

    def test_query_planning_guide_content(self):
        path = REPO_ROOT / "docs" / "QUERY_PLANNING_GUIDE.md"
        content = path.read_text(encoding="utf-8")
        assert "Tree-of-Thought" in content
        assert "site:arxiv.org" in content or "site:nature.com" in content
        assert "Dynamic Beam Pruning" in content
