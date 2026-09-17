#!/usr/bin/env python3
"""Comprehensive Unit Tests for CLI (Command Line Interface)."""

import io
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from deepsearch_research_agent.cli import build_parser, main
from deepsearch_research_agent.mcp_server import SERVER_NAME, SERVER_VERSION


class TestCLIParsing(unittest.TestCase):
    """Test CLI argument parsing."""

    def setUp(self):
        self.parser = build_parser()

    def test_parser_version(self):
        self.assertEqual(self.parser.prog, "deepsearch")

    def test_parser_research_args(self):
        args = self.parser.parse_args(["research", "Vector Databases", "--depth", "exhaustive", "--format", "json"])
        self.assertEqual(args.command, "research")
        self.assertEqual(args.topic, "Vector Databases")
        self.assertEqual(args.depth, "exhaustive")
        self.assertEqual(args.format, "json")

    def test_parser_plan_args(self):
        args = self.parser.parse_args(["plan", "Transformer Decoders", "--depth", "quick", "--json"])
        self.assertEqual(args.command, "plan")
        self.assertEqual(args.topic, "Transformer Decoders")
        self.assertEqual(args.depth, "quick")
        self.assertTrue(args.json)

    def test_parser_fetch_args(self):
        args = self.parser.parse_args(["fetch", "https://example.com/docs", "--raw", "--timeout", "5"])
        self.assertEqual(args.command, "fetch")
        self.assertEqual(args.url, "https://example.com/docs")
        self.assertTrue(args.raw)
        self.assertEqual(args.timeout, 5)

    def test_parser_corroborate_args(self):
        args = self.parser.parse_args(["corroborate", '["src1", "src2"]', "--claim", "Claim text", "--json"])
        self.assertEqual(args.command, "corroborate")
        self.assertEqual(args.claim, "Claim text")
        self.assertTrue(args.json)

    def test_parser_mcp_args(self):
        args = self.parser.parse_args(["mcp", "--tools"])
        self.assertEqual(args.command, "mcp")
        self.assertTrue(args.tools)

        args_cfg = self.parser.parse_args(["mcp", "--config", "cursor"])
        self.assertEqual(args_cfg.config, "cursor")

    def test_parser_platform_args(self):
        args = self.parser.parse_args(["platform", "--no-network", "--json"])
        self.assertEqual(args.command, "platform")
        self.assertTrue(args.no_network)
        self.assertTrue(args.json)


class TestCLIExecution(unittest.TestCase):
    """Test CLI execution of subcommands and outputs."""

    def test_no_args_shows_help(self):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            exit_code = main([])
            self.assertEqual(exit_code, 0)
            self.assertIn("usage:", mock_out.getvalue())

    def test_research_command_stdout(self):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            exit_code = main(["research", "State Space Models", "--depth", "quick", "--format", "markdown", "--no-color"])
            self.assertEqual(exit_code, 0)
            output = mock_out.getvalue()
            self.assertIn("State Space Models", output)
            self.assertIn("Executive Summary", output)

    def test_research_command_output_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "out_report.md")
            exit_code = main(["research", "Diffusion Transformers", "--depth", "quick", "--output", out_file, "--no-color"])
            self.assertEqual(exit_code, 0)
            self.assertTrue(os.path.isfile(out_file))
            with open(out_file, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("Diffusion Transformers", content)

    def test_plan_command_stdout_and_json(self):
        # Plain text
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            exit_code = main(["plan", "FlashAttention", "--depth", "quick", "--no-color"])
            self.assertEqual(exit_code, 0)
            output = mock_out.getvalue()
            self.assertIn("DeepSearch Research Plan", output)
            self.assertIn("FlashAttention", output)

        # JSON
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            exit_code = main(["plan", "FlashAttention", "--depth", "quick", "--json", "--no-color"])
            self.assertEqual(exit_code, 0)
            parsed = json.loads(mock_out.getvalue())
            self.assertEqual(parsed["topic"], "FlashAttention")
            self.assertIn("angles", parsed)

    def test_fetch_command(self):
        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.getcode.return_value = 200
            mock_resp.headers = {"Content-Type": "text/html"}
            mock_resp.read.return_value = b"<html><head><title>CLI Test</title></head><body><p>CLI Content</p></body></html>"
            mock_resp.__enter__.return_value = mock_resp
            mock_url.return_value = mock_resp

            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                exit_code = main(["fetch", "https://example.com/test", "--no-color"])
                self.assertEqual(exit_code, 0)
                output = mock_out.getvalue()
                self.assertIn("CLI Test", output)
                self.assertIn("CLI Content", output)

    def test_corroborate_command_inline_and_file(self):
        # Inline JSON
        sources_json = json.dumps([
            "Source 1 confirms accuracy benchmark of 98%",
            "Source 2 confirms accuracy benchmark of 98%"
        ])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            exit_code = main(["corroborate", sources_json, "--claim", "Accuracy benchmark", "--no-color"])
            self.assertEqual(exit_code, 0)
            output = mock_out.getvalue()
            self.assertIn("Multi-Source Corroboration Matrix", output)
            self.assertIn("Consensus Score", output)

        # File input
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write(sources_json)
            f_name = f.name

        try:
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                exit_code = main(["corroborate", f_name, "--json", "--no-color"])
                self.assertEqual(exit_code, 0)
                res = json.loads(mock_out.getvalue())
                self.assertEqual(res["total_sources_evaluated"], 2)
        finally:
            if os.path.exists(f_name):
                os.remove(f_name)

    def test_platform_diagnostics_command(self):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            exit_code = main(["platform", "--no-network", "--no-color"])
            self.assertEqual(exit_code, 0)
            output = mock_out.getvalue()
            self.assertIn("Platform Diagnostics", output)
            self.assertIn("Zero external runtime dependencies", output)

        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            exit_code = main(["platform", "--no-network", "--json", "--no-color"])
            self.assertEqual(exit_code, 0)
            data = json.loads(mock_out.getvalue())
            self.assertEqual(data["agent"]["name"], SERVER_NAME)

    def test_mcp_tools_and_config_command(self):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            exit_code = main(["mcp", "--tools", "--no-color"])
            self.assertEqual(exit_code, 0)
            output = mock_out.getvalue()
            self.assertIn("deepsearch_plan", output)
            self.assertIn("deepsearch_execute", output)

        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            exit_code = main(["mcp", "--config", "claude_desktop", "--no-color"])
            self.assertEqual(exit_code, 0)
            cfg = json.loads(mock_out.getvalue())
            self.assertIn("mcpServers", cfg)

    def test_test_command(self):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            exit_code = main(["test", "--no-color"])
            self.assertEqual(exit_code, 0)
            output = mock_out.getvalue()
            self.assertIn("Summary:", output)
            self.assertIn("0 failed", output)

    def test_test_flag(self):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            exit_code = main(["--test", "--no-color"])
            self.assertEqual(exit_code, 0)
            output = mock_out.getvalue()
            self.assertIn("0 failed", output)


if __name__ == "__main__":
    unittest.main()
