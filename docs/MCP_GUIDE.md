# DeepSearch Model Context Protocol (MCP) Server Guide

The `deepsearch-research-agent` includes a first-class, production-grade **Model Context Protocol (MCP)** server enabling direct integration with AI desktop clients, IDEs, and custom agent runtimes.

---

## 1. Overview of Exposed MCP Tools

The server implements the Model Context Protocol (JSON-RPC 2.0) exposing five core research tools:

### 1. `deep_research`
Performs an autonomous, recursive multi-stage research investigation and returns structured synthesis.

* **Parameters:**
  - `query` (*string*, required): The core research question or topic.
  - `depth` (*string*, optional, default: `"deep"`): `"quick"` (1 stage, 5-10 sources), `"deep"` (3 stages, 15-25 sources), or `"exhaustive"` (5 stages, 40+ sources).
  - `breadth` (*integer*, optional, default: `6`): Number of parallel query expansion branches per stage.
  - `focus_domains` (*array of strings*, optional): Specific domain filters (e.g. `["nature.com", "arxiv.org"]`).
  - `format` (*string*, optional, default: `"markdown"`): Output representation: `"markdown"`, `"json"`, or `"html"`.

* **Return Payload:**
  Markdown report, JSON data bundle, or HTML document with citation graph, verified claims, and confidence scores.

---

### 2. `plan_queries`
Generates a hierarchical Tree-of-Thought search plan with customized search operators.

* **Parameters:**
  - `topic` (*string*, required): Topic to explore.
  - `depth` (*integer*, optional, default: `3`): Tree decomposition depth.
  - `angles` (*array of strings*, optional): Explicit sub-angles to expand (e.g. `["benchmarks", "economics", "risks"]`).

* **Return Payload:**
  JSON tree of sub-queries with boolean operators, `site:` filters, and dependency ordering.

---

### 3. `verify_claims`
Cross-references empirical or factual claims against trusted web and academic literature.

* **Parameters:**
  - `claims` (*array of strings*, required): List of specific factual assertions.
  - `context` (*string*, optional): Additional background context.

* **Return Payload:**
  Array of verified claims with confidence ratings (`0.0 - 1.0`), consensus statuses (`Verified`, `Contested`, `Refuted`), and supporting source citations.

---

### 4. `extract_consensus`
Evaluates controversial or disputed claims across provided source texts and computes agreement ratios.

* **Parameters:**
  - `query` (*string*, required): The contested question or proposition.
  - `sources` (*array of strings*, optional): Optional list of URLs or raw text bodies.

* **Return Payload:**
  Dialectical synthesis presenting majority consensus, minority viewpoints, and residual ambiguities.

---

### 5. `search_knowledge_graph`
Queries the extracted research entity-relation graph.

* **Parameters:**
  - `entities` (*array of strings*, required): Target entity names or concepts.
  - `relation_type` (*string*, optional): Filter relations (e.g. `is_a`, `measures`, `competes_with`, `contradicts`).

---

## 2. Server Architecture & Transports

The DeepSearch MCP Server supports two primary transport modes:

```
[ AI Assistant / IDE ] 
          |
          |-- 1. Standard Input/Output (stdio) -- [ python -m deepsearch_research_agent.mcp_server ]
          |
          |-- 2. Server-Sent Events (SSE HTTP) -- [ http://localhost:8080/sse ]
```

### Stdio Transport (Default for Claude & IDEs)
- Low latency, process-lifecycle bound.
- Launched automatically by Claude Desktop, Cursor, Cline, or Zed as a subprocess.

### SSE / HTTP Transport (For Remote & Multi-Tenant Deployments)
- Run standalone:
  ```bash
  deepsearch mcp --transport sse --port 8080 --host 0.0.0.0
  ```
- Endpoint: `http://localhost:8080/sse`

---

## 3. Client Setup Configurations

### 3.1 Claude Desktop
Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "deepsearch-research-agent": {
      "command": "uvx",
      "args": ["deepsearch-research-agent", "mcp"],
      "env": {
        "SERPER_API_KEY": "your_serper_key_here",
        "TAVILY_API_KEY": "your_tavily_key_here",
        "DEEPSEARCH_DEFAULT_DEPTH": "deep"
      }
    }
  }
}
```

### 3.2 Cursor IDE
Add to `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "deepsearch-research-agent": {
      "command": "uvx",
      "args": ["deepsearch-research-agent", "mcp"],
      "env": {
        "SERPER_API_KEY": "your_serper_key_here"
      }
    }
  }
}
```

### 3.3 Cline Extension
Add to `cline_mcp.json`:
```json
{
  "mcpServers": {
    "deepsearch-research-agent": {
      "command": "uvx",
      "args": ["deepsearch-research-agent", "mcp"],
      "env": {
        "SERPER_API_KEY": "your_serper_key_here"
      },
      "disabled": false,
      "autoApprove": ["plan_queries", "verify_claims"]
    }
  }
}
```

### 3.4 Zed Editor
Add to `~/.config/zed/settings.json`:
```json
{
  "context_servers": {
    "deepsearch-research-agent": {
      "command": {
        "path": "uvx",
        "args": ["deepsearch-research-agent", "mcp"],
        "env": {
          "SERPER_API_KEY": "your_serper_key_here"
        }
      }
    }
  }
}
```

---

## 4. Error Handling & Timeout Guardrails

- **Subprocess Timeout**: Long-running research tasks default to a 180-second timeout with intermediate progress notifications sent via MCP logging notifications.
- **Graceful Degradation**: If an API provider (e.g. Serper, Tavily, ArXiv) fails or rate-limits, the engine automatically falls back to secondary web scraping providers without terminating the run.
- **Cache Persistence**: Completed query nodes are cached locally in `~/.cache/deepsearch/` to prevent redundant network requests.
