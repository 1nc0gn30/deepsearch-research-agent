# 🔍 DeepSearch Autonomous Research Agent

<p align="center">
  <img src="https://img.shields.io/badge/Deep%20Research-Studio%20v2.4-1a73e8?style=for-the-badge&logoColor=white" alt="Deep Research Studio" />
  <img src="https://img.shields.io/badge/Model%20Context%20Protocol-MCP%20Server%20Ready-1e8e3e?style=for-the-badge" alt="MCP Server Ready" />
  <img src="https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-f9ab00?style=for-the-badge&logo=python&logoColor=white" alt="Python Versions" />
  <img src="https://img.shields.io/badge/License-Apache%202.0-d93025?style=for-the-badge" alt="Apache 2.0 License" />
  <img src="https://img.shields.io/badge/CI%2FCD-15--Job%20Matrix%20Passing-9334e6?style=for-the-badge" alt="CI/CD Status" />
</p>

---

## Executive Overview

**DeepSearch** is a state-of-the-art autonomous deep research agent and consensus synthesis engine. Designed to tackle open-ended, complex scientific, technological, and market intelligence questions, DeepSearch iteratively decomposes research objectives, executes multi-angle boolean search queries, harvests and verifies primary literature, resolves contradictory empirical claims, and outputs publication-grade synthesized reports with mathematical grounding scores and interactive visualizations.

### 🌟 Key Capabilities

- 🌳 **Recursive Tree-of-Thought Query Decomposition**: Breaks down broad questions into multi-stage Directed Acyclic Graphs (DAGs) with automated Boolean operator crafting (`site:`, `filetype:pdf`, `intitle:`).
- ⚖️ **Dialectical Consensus & Contradiction Matrix**: Cross-references claims across dozens of sources, computing weighted agreement ratios and isolating contested assumptions.
- 📐 **Calibrated Confidence Scoring**: Calculates grounded confidence metrics $C \in [0, 1]$ based on domain authority, recency decay, peer-review weight, and corroboration depth.
- 🔌 **Native Model Context Protocol (MCP) Server**: Drop-in MCP integration for Claude Desktop, Cursor, Cline, Zed, and custom LLM runtimes.
- 🖥️ **Deep Research Studio UI**: Built-in web studio (design influenced by Material 3) with live query branch visualizer, consensus matrix, interactive SVG metrics charts, and copy-ready client config hub.
- 📦 **Multi-Format Export**: Generates peer-reviewed Markdown reports, interactive standalone HTML documents, and machine-readable JSON data bundles.

---

## 🏛️ System Architecture

```
+----------------------------------------------------------------------------------------------------+
|                                DEEPSEARCH SYSTEM ARCHITECTURE                                      |
+----------------------------------------------------------------------------------------------------+

                           [ Human Query / MCP Client / IDE / Web UI ]
                                                |
                                                v
               +----------------------------------------------------------------+
               |              Stage 1: Autonomous Query Planner                 |
               |   - Tree-of-Thought Decomposition (Technical, Market, Risk)    |
               |   - Search Operator Crafting (site:, filetype:pdf, boolean)    |
               +-------------------------------+--------------------------------+
                                               |
                                               v
               +----------------------------------------------------------------+
               |              Stage 2: Parallel Evidence Harvester              |
               |   - Multi-Engine Crawling (Serper, Tavily, ArXiv, PubMed)      |
               |   - Asynchronous Content Extraction & Boilerplate Scrubbing    |
               +-------------------------------+--------------------------------+
                                               |
                                               v
               +----------------------------------------------------------------+
               |           Stage 3: Domain Authority & Credibility Engine       |
               |   - Institutional Scoring (0-100), Bias Detection              |
               |   - Recency Decay Factor: R(dt) = exp(-lambda * dt)            |
               +-------------------------------+--------------------------------+
                                               |
                                               v
               +----------------------------------------------------------------+
               |            Stage 4: Consensus & Contradiction Matrix           |
               |   - Corroborating vs Refuting Claim Partitioning               |
               |   - Weighted Agreement Ratios & Conflict Flagging              |
               +-------------------------------+--------------------------------+
                                               |
                                               v
               +----------------------------------------------------------------+
               |             Stage 5: Grounded Multi-Perspective Synthesizer     |
               |   - Calibrated Confidence Math: C = sum(w_i * s_i * alpha)      |
               |   - Zero-Unreferenced-Claim Policy & Interactive Visuals       |
               +-------------------------------+--------------------------------+
                                               |
         +-------------------------------------+------------------------------------+
         |                                     |                                    |
         v                                     v                                    v
[ 📄 Markdown Research Report ]    [ 🌐 Material 3 HTML Artifact ]     [ 📊 JSON Data Bundle ]
```

---

## 🚀 Quick Start

### 1. Installation

```bash
# Install via pip
pip install deepsearch-research-agent

# Or run with uvx without installation
uvx deepsearch-research-agent --help
```

### 2. Environment Configuration

Set your preferred search and LLM API keys:
```bash
export SERPER_API_KEY="your_serper_api_key"
export TAVILY_API_KEY="your_tavily_api_key"
export OPENAI_API_KEY="your_openai_api_key"
export ANTHROPIC_API_KEY="your_anthropic_api_key"
```

### 3. Command Line Interface (CLI)

```bash
# Run quick research (1 stage, 5-10 sources)
deepsearch run "CRISPR-Cas12 vs Cas9 off-target editing rates" --depth quick

# Run exhaustive research with custom domain focus and exports
deepsearch run \
  "State of Fault-Tolerant Quantum Computing & Logical Qubit Scaling (2026)" \
  --depth exhaustive \
  --breadth 8 \
  --focus-domains "nature.com,science.org,aps.org,ieee.org" \
  --output-dir ./output-report \
  --format all
```

### 4. Python Programmatic API

```python
from deepsearch_research_agent import DeepResearchEngine, ResearchConfig

# Configure research depth and constraints
config = ResearchConfig(
    depth="exhaustive",
    breadth=8,
    enable_consensus_matrix=True,
    min_source_authority=85,
)

engine = DeepResearchEngine(config=config)
result = engine.run(
    query="State of Fault-Tolerant Quantum Computing & Logical Qubit Scaling (2026)"
)

# Access structured data
print(f"Confidence Score: {result.confidence_score:.2%}")
print(f"Harvested Sources: {len(result.sources)}")
print(f"Verified Claims: {len(result.verified_claims)}")

# Export artifacts
result.save_markdown("report.md")
result.save_html("report.html")
result.save_json("data_bundle.json")
```

---

## 🤖 Model Context Protocol (MCP) Integration

DeepSearch can be attached as a live context engine in Claude Desktop, Cursor, Cline, and Zed.

```bash
# Launch MCP Server in stdio mode
deepsearch mcp

# Launch MCP Server over SSE (HTTP streaming)
deepsearch mcp --transport sse --port 8080
```

### Drop-in Claude Desktop Configuration (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "deepsearch-research-agent": {
      "command": "uvx",
      "args": ["deepsearch-research-agent", "mcp"],
      "env": {
        "SERPER_API_KEY": "your_serper_api_key",
        "DEEPSEARCH_DEFAULT_DEPTH": "deep"
      }
    }
  }
}
```

For full integration guides for **Cursor**, **Cline**, and **Zed**, see [docs/MCP_GUIDE.md](file:///media/neo/f2fdda77-178b-4603-ae80-c7aa4cd97908/deepsearch-research-agent/docs/MCP_GUIDE.md) and the [examples/mcp-clients/](file:///media/neo/f2fdda77-178b-4603-ae80-c7aa4cd97908/deepsearch-research-agent/examples/mcp-clients/) directory.

---

## 🖥️ Deep Research Studio Web UI

DeepSearch ships with an interactive, offline-ready web studio (design influenced by Google Material 3 tokens) located at [`public/index.html`](file:///media/neo/f2fdda77-178b-4603-ae80-c7aa4cd97908/deepsearch-research-agent/public/index.html).

To launch the studio:
```bash
deepsearch studio --port 3000
```
Or open [`public/index.html`](file:///media/neo/f2fdda77-178b-4603-ae80-c7aa4cd97908/deepsearch-research-agent/public/index.html) directly in any modern browser.

### Studio Features:
1. 🔍 **Deep Research Studio**: Live multi-stage query decomposition visualizer, citation stream, and Markdown preview.
2. 📑 **Autonomous Query Planner**: Interactive Tree-of-Thought graph, custom search operator generator, and boolean string preview.
3. ⚖️ **Source & Consensus Matrix**: Interactive sources table with authority scoring, claim verification status, and corroboration gauges.
4. 📊 **Data Points & SVG Visuals**: Native SVG multi-bar, time-series, radar, and donut charts with interactive tooltips.
5. 🤖 **AI Agent & MCP Hub**: One-click configuration copier for Claude, Cursor, Cline, Zed, and live JSON-RPC tool simulator.
6. 📖 **Research Methodology Guide**: Built-in interactive architectural documentation and confidence calibration math.

---

## 📚 Documentation Directory

- [Research Methodology & Synthesis Engine](file:///media/neo/f2fdda77-178b-4603-ae80-c7aa4cd97908/deepsearch-research-agent/docs/RESEARCH_METHODOLOGY.md)
- [MCP Server Setup & Tool Specification](file:///media/neo/f2fdda77-178b-4603-ae80-c7aa4cd97908/deepsearch-research-agent/docs/MCP_GUIDE.md)
- [Autonomous Query Planning & Search Operators](file:///media/neo/f2fdda77-178b-4603-ae80-c7aa4cd97908/deepsearch-research-agent/docs/QUERY_PLANNING_GUIDE.md)

---

## 📁 Reference Examples

- [Fault-Tolerant Quantum Computing Brief (2026)](file:///media/neo/f2fdda77-178b-4603-ae80-c7aa4cd97908/deepsearch-research-agent/examples/quantum-computing-brief/)
- [Enterprise Autonomous AI Agents Market Intelligence](file:///media/neo/f2fdda77-178b-4603-ae80-c7aa4cd97908/deepsearch-research-agent/examples/market-intelligence-report/)
- [MCP Client Configurations](file:///media/neo/f2fdda77-178b-4603-ae80-c7aa4cd97908/deepsearch-research-agent/examples/mcp-clients/)

---

## 🧪 Testing & CI/CD

Run the test suite locally:
```bash
PYTHONPATH=src pytest tests/ -v
```

The repository includes a comprehensive 15-job CI matrix in [`.github/workflows/ci.yml`](file:///media/neo/f2fdda77-178b-4603-ae80-c7aa4cd97908/deepsearch-research-agent/.github/workflows/ci.yml) testing across Ubuntu, macOS, and Windows on Python 3.9, 3.10, 3.11, 3.12, and 3.13.

---

## 📄 License

Licensed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).
