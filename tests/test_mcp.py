#!/usr/bin/env python3
"""Comprehensive Unit Tests for Model Context Protocol (MCP) Server."""

import io
import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from deepsearch_research_agent.mcp_server import (
    MCP_PROTOCOL_VERSION,
    SERVER_NAME,
    SERVER_VERSION,
    MCPServer,
    deepsearch_corroborate,
    deepsearch_execute,
    deepsearch_export_report,
    deepsearch_fetch,
    deepsearch_get_diagnostics,
    deepsearch_plan,
    generate_mcp_client_config,
)


class TestMCPServerProtocol(unittest.TestCase):
    """Test MCP JSON-RPC 2.0 protocol request routing and handlers."""

    def setUp(self):
        self.server = MCPServer()

    def test_initialize(self):
        req = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        })
        resp_str = self.server.handle_message(req)
        self.assertIsNotNone(resp_str)
        resp = json.loads(resp_str)
        self.assertEqual(resp["jsonrpc"], "2.0")
        self.assertEqual(resp["id"], 1)
        self.assertIn("result", resp)
        self.assertEqual(resp["result"]["protocolVersion"], MCP_PROTOCOL_VERSION)
        self.assertEqual(resp["result"]["serverInfo"]["name"], SERVER_NAME)
        self.assertEqual(resp["result"]["serverInfo"]["version"], SERVER_VERSION)
        self.assertIn("tools", resp["result"]["capabilities"])

    def test_notification_initialized(self):
        req = json.dumps({
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        })
        resp_str = self.server.handle_message(req)
        self.assertIsNone(resp_str)

    def test_ping(self):
        req = json.dumps({"jsonrpc": "2.0", "id": 42, "method": "ping"})
        resp_str = self.server.handle_message(req)
        self.assertIsNotNone(resp_str)
        resp = json.loads(resp_str)
        self.assertEqual(resp["id"], 42)
        self.assertEqual(resp["result"], {})

    def test_tools_list(self):
        req = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        resp_str = self.server.handle_message(req)
        resp = json.loads(resp_str)
        tools = resp["result"]["tools"]
        tool_names = [t["name"] for t in tools]

        expected_tools = [
            "deepsearch_plan",
            "deepsearch_execute",
            "deepsearch_fetch",
            "deepsearch_corroborate",
            "deepsearch_export_report",
            "deepsearch_get_diagnostics",
        ]
        for exp in expected_tools:
            self.assertIn(exp, tool_names)

        # Validate input schemas
        for t in tools:
            self.assertIn("inputSchema", t)
            self.assertEqual(t["inputSchema"]["type"], "object")

    def test_unknown_method(self):
        req = json.dumps({"jsonrpc": "2.0", "id": 99, "method": "invalid/method"})
        resp_str = self.server.handle_message(req)
        resp = json.loads(resp_str)
        self.assertIn("error", resp)
        self.assertEqual(resp["error"]["code"], -32601)

    def test_malformed_json(self):
        resp_str = self.server.handle_message("{invalid json")
        resp = json.loads(resp_str)
        self.assertIn("error", resp)
        self.assertEqual(resp["error"]["code"], -32700)

    def test_empty_message(self):
        self.assertIsNone(self.server.handle_message(""))
        self.assertIsNone(self.server.handle_message("   "))


class TestMCPTools(unittest.TestCase):
    """Test individual MCP tool execution via MCPServer.call_tool."""

    def setUp(self):
        self.server = MCPServer()

    def test_tool_deepsearch_plan(self):
        result = self.server.call_tool("deepsearch_plan", {
            "topic": "Quantum Fault Tolerance",
            "depth": "deep",
            "focus_areas": ["Surface Codes"]
        })
        self.assertFalse(result["isError"])
        content_text = result["content"][0]["text"]
        plan = json.loads(content_text)
        self.assertEqual(plan["topic"], "Quantum Fault Tolerance")
        self.assertEqual(plan["depth"], "deep")
        self.assertGreaterEqual(len(plan["angles"]), 5)
        self.assertTrue(any("Surface Codes" in a["name"] for a in plan["angles"]))

    def test_tool_deepsearch_plan_quick_and_exhaustive(self):
        p_quick = deepsearch_plan("Transformers", depth="quick")
        self.assertEqual(len(p_quick["angles"]), 3)

        p_exh = deepsearch_plan("Transformers", depth="exhaustive")
        self.assertEqual(len(p_exh["angles"]), 8)

    def test_tool_deepsearch_execute(self):
        result = self.server.call_tool("deepsearch_execute", {
            "topic": "Graph Neural Networks",
            "depth": "quick",
            "format": "markdown",
            "max_sources": 3
        })
        self.assertFalse(result["isError"])
        text = result["content"][0]["text"]
        self.assertIn("Graph Neural Networks", text)
        self.assertIn("Executive Summary", text)

    def test_tool_deepsearch_execute_json(self):
        res = deepsearch_execute("Generative Agents", depth="quick", format="json")
        self.assertIn("topic", res)
        self.assertIn("key_findings", res)
        self.assertIn("metrics", res)
        self.assertIn("sources", res)

    def test_tool_deepsearch_fetch(self):
        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.getcode.return_value = 200
            mock_resp.headers = {"Content-Type": "text/html; charset=utf-8"}
            mock_resp.read.return_value = (
                b"<html><head><title>Test Article</title></head>"
                b"<body><script>alert(1);</script><h1>Main Heading</h1><p>Important content paragraph.</p></body></html>"
            )
            mock_resp.__enter__.return_value = mock_resp
            mock_url.return_value = mock_resp

            result = self.server.call_tool("deepsearch_fetch", {"url": "https://example.com/test"})
            self.assertFalse(result["isError"])
            fetched = json.loads(result["content"][0]["text"])
            self.assertEqual(fetched["status"], 200)
            self.assertEqual(fetched["title"], "Test Article")
            self.assertIn("Main Heading", fetched["content"])
            self.assertIn("Important content paragraph", fetched["content"])
            self.assertNotIn("alert(1)", fetched["content"])

    def test_tool_deepsearch_fetch_raw(self):
        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.getcode.return_value = 200
            mock_resp.headers = {"Content-Type": "text/html"}
            mock_resp.read.return_value = b"<html><body>Raw Data</body></html>"
            mock_resp.__enter__.return_value = mock_resp
            mock_url.return_value = mock_resp

            res = deepsearch_fetch("https://example.com", raw=True)
            self.assertTrue(res["raw"])
            self.assertEqual(res["content"], "<html><body>Raw Data</body></html>")

    def test_tool_deepsearch_corroborate(self):
        sources = [
            "Source 1: Empirical benchmarks show algorithm achieves 95% precision with zero latency regression.",
            "Source 2: Independent verification confirms algorithm achieves 95% precision consistently.",
            "Source 3: Field tests refute claims of zero latency under extreme memory limits.",
        ]
        result = self.server.call_tool("deepsearch_corroborate", {
            "sources": sources,
            "claim": "Algorithm precision and latency",
        })
        self.assertFalse(result["isError"])
        corrob = json.loads(result["content"][0]["text"])
        self.assertEqual(corrob["total_sources_evaluated"], 3)
        self.assertEqual(corrob["support_count"], 2)
        self.assertEqual(corrob["refute_count"], 1)
        self.assertIn("confidence_level", corrob)

    def test_tool_deepsearch_export_report_formats(self):
        report_data = {
            "topic": "Distributed Consensus",
            "executive_summary": "Summary of consensus protocols.",
            "key_findings": ["Raft provides formal safety.", "Paxos is mathematically minimal."],
            "perspectives": [{"angle": "Safety", "perspective": "Formal", "findings": "No split-brain observed."}],
            "corroboration_matrix": {"consensus_score": 0.98, "confidence_level": "High"},
            "metrics": {"sources_analyzed": 4, "verification_rate": 0.98},
            "sources": [{"source_id": 1, "title": "Raft Paper", "url": "https://raft.github.io", "snippet": "In search of understandable consensus."}],
            "actionable_takeaways": ["Use Raft for new distributed state machines."],
        }

        # 1. Markdown
        md_res = deepsearch_export_report(report_data, format="markdown")
        self.assertIn("# Deep Research Dossier: Distributed Consensus", md_res["content"])
        self.assertIn("Raft provides formal safety.", md_res["content"])

        # 2. HTML
        html_res = deepsearch_export_report(report_data, format="html")
        self.assertIn("<!DOCTYPE html>", html_res["content"])
        self.assertIn("Distributed Consensus", html_res["content"])
        self.assertIn("m3-card", html_res["content"])

        # 3. JSON
        json_res = deepsearch_export_report(report_data, format="json")
        parsed = json.loads(json_res["content"])
        self.assertEqual(parsed["topic"], "Distributed Consensus")

        # 4. File Output
        with tempfile.TemporaryDirectory() as tmpdir:
            file_out = os.path.join(tmpdir, "report.md")
            file_res = deepsearch_export_report(report_data, format="markdown", output_path=file_out)
            self.assertTrue(os.path.isfile(file_out))
            self.assertGreater(file_res["bytes_written"], 0)

    def test_tool_deepsearch_get_diagnostics(self):
        result = self.server.call_tool("deepsearch_get_diagnostics", {"include_network_check": False})
        self.assertFalse(result["isError"])
        diag = json.loads(result["content"][0]["text"])
        self.assertEqual(diag["agent"]["name"], SERVER_NAME)
        self.assertEqual(diag["agent"]["version"], SERVER_VERSION)
        self.assertIn("os", diag["system"])
        self.assertIn("python", diag)

    def test_unknown_tool(self):
        result = self.server.call_tool("nonexistent_tool", {})
        self.assertTrue(result["isError"])


class TestMCPClientConfig(unittest.TestCase):
    """Test generation of client configuration snippets for all target IDEs."""

    def test_claude_desktop_config(self):
        cfg = generate_mcp_client_config("claude_desktop", python_path="/usr/bin/python3")
        self.assertIn("mcpServers", cfg)
        self.assertEqual(cfg["mcpServers"]["deepsearch"]["command"], "/usr/bin/python3")
        self.assertEqual(cfg["mcpServers"]["deepsearch"]["args"], ["-m", "deepsearch_research_agent", "mcp"])

    def test_cursor_config(self):
        cfg = generate_mcp_client_config("cursor")
        self.assertIn("mcpServers", cfg)
        self.assertIn("deepsearch", cfg["mcpServers"])

    def test_cline_config(self):
        cfg = generate_mcp_client_config("cline")
        self.assertIn("deepsearch", cfg["mcpServers"])
        self.assertIn("alwaysAllow", cfg["mcpServers"]["deepsearch"])

    def test_zed_config(self):
        cfg = generate_mcp_client_config("zed")
        self.assertIn("context_servers", cfg)
        self.assertIn("deepsearch", cfg["context_servers"])

    def test_generic_config(self):
        cfg = generate_mcp_client_config("generic")
        self.assertEqual(cfg["name"], "deepsearch")
        self.assertEqual(cfg["transport"], "stdio")


class TestMCPServerStream(unittest.TestCase):
    """Test stdio stream loop execution."""

    def test_stream_processing(self):
        req1 = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"})
        req2 = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        input_stream = io.StringIO(f"{req1}\n{req2}\n")
        output_stream = io.StringIO()

        server = MCPServer(stdin=input_stream, stdout=output_stream)
        server.run()

        output_lines = [line.strip() for line in output_stream.getvalue().splitlines() if line.strip()]
        self.assertEqual(len(output_lines), 2)
        resp1 = json.loads(output_lines[0])
        resp2 = json.loads(output_lines[1])
        self.assertEqual(resp1["id"], 1)
        self.assertEqual(resp2["id"], 2)


if __name__ == "__main__":
    unittest.main()
