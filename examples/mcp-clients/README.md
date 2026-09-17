# Model Context Protocol (MCP) Client Integrations

This directory contains pre-configured client configurations to connect `deepsearch-research-agent` directly into modern AI environments supporting the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/).

---

## Available MCP Tools

When registered as an MCP server, `deepsearch-research-agent` exposes the following high-level tools to your LLM assistant:

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `deep_research` | `query: str`, `depth: "quick" \| "deep" \| "exhaustive"`, `breadth: int`, `focus_domains: list[str]`, `format: "markdown" \| "json" \| "html"` | Executes an autonomous end-to-end deep research run with recursive query expansion, source harvesting, verification, and synthesis. |
| `plan_queries` | `topic: str`, `depth: int`, `angles: list[str]` | Generates a structured multi-level query tree with search operators (`site:`, `filetype:pdf`, boolean filters). |
| `verify_claims` | `claims: list[str]`, `context: str` | Cross-references specific empirical or factual claims against trusted web and academic sources, returning a consensus matrix. |
| `extract_consensus` | `query: str`, `sources: list[str]` | Analyzes contradictory or ambiguous claims across provided evidence sources and produces a calibrated agreement score. |
| `search_knowledge_graph` | `entities: list[str]`, `relation_type: str` | Traverses extracted research entities, citations, and relation triples. |

---

## 1. Claude Desktop Setup

### Configuration Path
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Installation
Copy the configuration from [claude_desktop_config.json](file:///media/neo/f2fdda77-178b-4603-ae80-c7aa4cd97908/deepsearch-research-agent/examples/mcp-clients/claude_desktop_config.json):

```json
{
  "mcpServers": {
    "deepsearch-research-agent": {
      "command": "uvx",
      "args": [
        "deepsearch-research-agent",
        "mcp"
      ],
      "env": {
        "SERPER_API_KEY": "your_serper_api_key",
        "TAVILY_API_KEY": "your_tavily_api_key",
        "DEEPSEARCH_DEFAULT_DEPTH": "deep"
      }
    }
  }
}
```

Restart Claude Desktop. Look for the 🔨 hammer icon in the bottom right corner showing `deepsearch-research-agent` tools.

---

## 2. Cursor IDE Setup

### Configuration Path
Place `cursor_mcp.json` in your project root at `.cursor/mcp.json` or globally under Cursor MCP Settings:
- **Project level**: `.cursor/mcp.json`
- **Global Settings**: `Settings` -> `Features` -> `MCP Servers` -> `Add New MCP Server`

### Configuration Snippet
See [cursor_mcp.json](file:///media/neo/f2fdda77-178b-4603-ae80-c7aa4cd97908/deepsearch-research-agent/examples/mcp-clients/cursor_mcp.json):

```json
{
  "mcpServers": {
    "deepsearch-research-agent": {
      "command": "uvx",
      "args": ["deepsearch-research-agent", "mcp"],
      "env": {
        "SERPER_API_KEY": "your_serper_api_key"
      }
    }
  }
}
```

---

## 3. Cline (VS Code Extension) Setup

### Configuration Path
- **Global Settings**: Open Cline extension settings -> `MCP Servers` -> `Edit in settings.json`
- **Path**: `~/.vscode/extensions/cline/mcp_settings.json`

### Configuration Snippet
See [cline_mcp.json](file:///media/neo/f2fdda77-178b-4603-ae80-c7aa4cd97908/deepsearch-research-agent/examples/mcp-clients/cline_mcp.json):

```json
{
  "mcpServers": {
    "deepsearch-research-agent": {
      "command": "uvx",
      "args": ["deepsearch-research-agent", "mcp"],
      "env": {
        "SERPER_API_KEY": "your_serper_api_key"
      },
      "disabled": false,
      "autoApprove": [
        "plan_queries",
        "verify_claims",
        "extract_consensus"
      ]
    }
  }
}
```

---

## 4. Zed Editor Setup

### Configuration Path
Open Zed Settings (`Cmd+,` or `Ctrl+,`), or edit `~/.config/zed/settings.json`.

### Configuration Snippet
See [zed_settings.json](file:///media/neo/f2fdda77-178b-4603-ae80-c7aa4cd97908/deepsearch-research-agent/examples/mcp-clients/zed_settings.json):

```json
{
  "context_servers": {
    "deepsearch-research-agent": {
      "command": {
        "path": "uvx",
        "args": ["deepsearch-research-agent", "mcp"],
        "env": {
          "SERPER_API_KEY": "your_serper_api_key"
        }
      }
    }
  }
}
```

---

## 5. Testing the MCP Server Directly

You can interactively test and inspect the MCP server via the official MCP inspector:

```bash
npx @modelcontextprotocol/inspector uvx deepsearch-research-agent mcp
```

Or via direct CLI stdio piping:

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python -m deepsearch_research_agent.mcp_server
```
