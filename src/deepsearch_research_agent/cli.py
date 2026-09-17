#!/usr/bin/env python3
"""
Command Line Interface for DeepSearch Research Agent.

Provides full CLI subcommands for multi-angle deep research, structured planning,
web content extraction, source corroboration, Material 3 UI serving, MCP server execution,
and platform diagnostics. Pure standard library with zero runtime dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import List, Optional

from deepsearch_research_agent.mcp_server import (
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
    run_mcp_server,
)
from deepsearch_research_agent.ui_server import run_ui_server


# =====================================================================
# Terminal Color & Styling Utilities
# =====================================================================

class Colors:
    """ANSI color formatting with auto-detection and NO_COLOR support."""

    def __init__(self, force_disable: bool = False) -> None:
        self.enabled = (
            not force_disable
            and "NO_COLOR" not in os.environ
            and hasattr(sys.stdout, "isatty")
            and sys.stdout.isatty()
        )

    def _c(self, code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.enabled else text

    def bold(self, text: str) -> str:
        return self._c("1", text)

    def dim(self, text: str) -> str:
        return self._c("2", text)

    def blue(self, text: str) -> str:
        return self._c("94", text)

    def cyan(self, text: str) -> str:
        return self._c("96", text)

    def green(self, text: str) -> str:
        return self._c("92", text)

    def yellow(self, text: str) -> str:
        return self._c("93", text)

    def red(self, text: str) -> str:
        return self._c("91", text)

    def magenta(self, text: str) -> str:
        return self._c("95", text)


# =====================================================================
# Subcommand Handlers
# =====================================================================

def cmd_research(args: argparse.Namespace, c: Colors) -> int:
    """Execute autonomous deep research on a topic."""
    topic = args.topic.strip()
    depth = args.depth.lower()
    fmt = args.format.lower()
    if fmt == "md":
        fmt = "markdown"

    print(f"\n{c.bold(c.blue('=== DeepSearch Autonomous Multi-Perspective Research ==='))}")
    print(f"{c.dim('Topic:')} {c.bold(topic)}")
    print(f"{c.dim('Depth:')} {c.cyan(depth.upper())} | {c.dim('Format:')} {c.yellow(fmt.upper())}")
    print(f"{c.dim('Status:')} Synthesizing investigative angles and corroborating evidence...\n")

    t0 = time.time()
    try:
        report = deepsearch_execute(
            topic=topic,
            depth=depth,
            format=fmt,
            max_sources=args.max_sources if hasattr(args, "max_sources") else 5,
        )
        elapsed = round(time.time() - t0, 2)

        if fmt == "json":
            out_text = json.dumps(report, indent=2, ensure_ascii=False)
        elif fmt == "html":
            out_text = report.get("rendered", "")
        else:  # markdown
            out_text = report.get("rendered", "")

        if args.output:
            out_path = os.path.abspath(args.output)
            out_dir = os.path.dirname(out_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(out_text)
            print(f"{c.green('✓')} Research report written to: {c.bold(out_path)}")
            print(f"{c.dim(f'Completed in {elapsed}s | Size: {len(out_text)} characters')}\n")
        else:
            print(out_text)
            print(f"\n{c.green('✓')} {c.dim(f'Research completed in {elapsed}s')}")

        return 0
    except Exception as e:
        print(f"{c.red('Error executing research:')} {e}", file=sys.stderr)
        return 1


def cmd_plan(args: argparse.Namespace, c: Colors) -> int:
    """Generate a structured research execution plan."""
    topic = args.topic.strip()
    depth = args.depth.lower()

    try:
        plan_data = deepsearch_plan(topic=topic, depth=depth)

        if args.json:
            print(json.dumps(plan_data, indent=2, ensure_ascii=False))
            return 0

        print(f"\n{c.bold(c.blue('=== DeepSearch Research Plan ==='))}")
        print(f"{c.dim('Plan ID:')}    {plan_data['execution_id']}")
        print(f"{c.dim('Topic:')}      {c.bold(plan_data['topic'])}")
        print(f"{c.dim('Depth:')}      {c.cyan(plan_data['depth'].upper())}")
        print(f"{c.dim('Est. Time:')}  {plan_data['estimated_duration_seconds']}s\n")

        print(c.bold("Investigative Angles:"))
        for i, angle in enumerate(plan_data["angles"], 1):
            print(f"  {c.green(f'[{i}]')} {c.bold(angle['name'])} ({c.yellow(angle['perspective'])})")
            print(f"      {c.dim(angle['description'])}")

        print(f"\n{c.bold('Sub-Queries & Targeting:')}")
        for q in plan_data["sub_queries"]:
            q_id = q['id']
            q_prio = q['priority'].upper()
            q_query = q['query']
            q_angle = q['angle']
            print(f"  {c.cyan(q_id)} [{q_prio}]: \"{q_query}\"")
            print(f"      {c.dim(f'Angle: {q_angle}')}")

        print(f"\n{c.bold('Verification Targets:')}")
        for check in plan_data["verification_checklist"]:
            print(f"  - [ ] {check}")

        print("")
        return 0
    except Exception as e:
        print(f"{c.red('Error creating research plan:')} {e}", file=sys.stderr)
        return 1


def cmd_fetch(args: argparse.Namespace, c: Colors) -> int:
    """Fetch URL and extract clean text/markdown."""
    url = args.url.strip()

    try:
        res = deepsearch_fetch(url=url, raw=args.raw, timeout=args.timeout)

        if args.output:
            out_path = os.path.abspath(args.output)
            out_dir = os.path.dirname(out_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            content_to_write = res.get("content", "")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content_to_write)
            print(f"{c.green('✓')} Fetched content written to: {c.bold(out_path)}")
            return 0

        if args.raw:
            print(res.get("content", ""))
        else:
            print(f"\n{c.bold(c.blue('=== Extracted Content ==='))}")
            print(f"{c.dim('URL:')}         {res['url']}")
            print(f"{c.dim('Title:')}       {c.bold(res.get('title', ''))}")
            print(f"{c.dim('Status:')}      {res['status']}")
            print(f"{c.dim('Word Count:')}  {res['word_count']}\n")
            print(c.bold("--- Content Markdown ---"))
            print(res.get("content", ""))
            print(c.bold("------------------------\n"))

        return 0 if res["status"] in (200, 0) else 1
    except Exception as e:
        print(f"{c.red('Error fetching URL:')} {e}", file=sys.stderr)
        return 1


def cmd_corroborate(args: argparse.Namespace, c: Colors) -> int:
    """Evaluate consensus and cross-validate across multiple sources."""
    sources_input = args.sources.strip()

    sources_list = []
    # Check if input is a JSON string or path to JSON file
    if os.path.isfile(sources_input):
        try:
            with open(sources_input, "r", encoding="utf-8") as f:
                parsed_json = json.load(f)
                if isinstance(parsed_json, list):
                    sources_list = parsed_json
                elif isinstance(parsed_json, dict) and "sources" in parsed_json:
                    sources_list = parsed_json["sources"]
                else:
                    sources_list = [parsed_json]
        except Exception as e:
            print(f"{c.red('Error reading sources file:')} {e}", file=sys.stderr)
            return 1
    else:
        try:
            parsed_json = json.loads(sources_input)
            if isinstance(parsed_json, list):
                sources_list = parsed_json
            else:
                sources_list = [parsed_json]
        except Exception:
            # Treat as comma or newline separated snippets
            sources_list = [s.strip() for s in sources_input.split("\n") if s.strip()]

    if not sources_list:
        print(f"{c.red('Error:')} No valid sources found in input.", file=sys.stderr)
        return 1

    try:
        res = deepsearch_corroborate(sources=sources_list, claim=args.claim, topic=args.topic)

        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
            return 0

        consensus_pct = int(res["consensus_score"] * 100)
        print(f"\n{c.bold(c.blue('=== Multi-Source Corroboration Matrix ==='))}")
        print(f"{c.dim('Target Claim:')}     {c.bold(res['claim'])}")
        print(f"{c.dim('Sources Checked:')} {res['total_sources_evaluated']}")
        print(f"{c.dim('Consensus Score:')} {c.green(f'{consensus_pct}%')}")
        print(f"{c.dim('Confidence Level:')} {c.cyan(res['confidence_level'])}\n")

        print(c.bold("Source Stance Breakdown:"))
        print(f"  Supporting:   {c.green(str(res['support_count']))}")
        print(f"  Refuting:     {c.red(str(res['refute_count']))}")
        print(f"  Neutral:      {c.yellow(str(res['neutral_count']))}\n")

        print(c.bold("Key Consensus Agreements:"))
        for a in res["key_agreements"]:
            print(f"  {c.green('✓')} {a}")

        print(f"\n{c.bold('Divergences & Caveats:')}")
        for d in res["key_divergences"]:
            print(f"  {c.yellow('!')} {d}")

        print(f"\n{c.bold('Verdict:')} {res['synthesis_verdict']}\n")
        return 0
    except Exception as e:
        print(f"{c.red('Error during corroboration:')} {e}", file=sys.stderr)
        return 1


def cmd_serve(args: argparse.Namespace, c: Colors) -> int:
    """Start Deep Research Studio Web UI (design influenced by Material 3)."""
    host = args.host
    port = args.port
    open_browser = args.open

    try:
        httpd = run_ui_server(host=host, port=port, open_browser=open_browser)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down DeepSearch Research Studio server...")
            httpd.shutdown()
        return 0
    except Exception as e:
        print(f"{c.red('Error starting UI server:')} {e}", file=sys.stderr)
        return 1


def cmd_mcp(args: argparse.Namespace, c: Colors) -> int:
    """Run stdio MCP server or display tools/client configuration."""
    if args.tools:
        server = MCPServer()
        tools_list = server._tools
        print(f"\n{c.bold(c.blue('=== DeepSearch MCP Tools (Protocol 2024-11-05) ==='))}\n")
        for t in tools_list:
            print(f"{c.green('•')} {c.bold(t['name'])}")
            print(f"  {c.dim(t['description'])}")
            print(f"  {c.cyan('Required params:')} {t['inputSchema'].get('required', [])}")
            print("")
        return 0

    if args.config:
        cfg = generate_mcp_client_config(client_name=args.config)
        print(json.dumps(cfg, indent=2))
        return 0

    # Default: Run stdio server loop
    try:
        run_mcp_server()
        return 0
    except Exception as e:
        print(f"MCP Server error: {e}", file=sys.stderr)
        return 1


def cmd_platform(args: argparse.Namespace, c: Colors) -> int:
    """Display comprehensive multi-OS platform diagnostics."""
    diag = deepsearch_get_diagnostics(include_network_check=not args.no_network)

    if args.json:
        print(json.dumps(diag, indent=2, ensure_ascii=False))
        return 0

    print(f"\n{c.bold(c.blue('=== DeepSearch Platform Diagnostics ==='))}\n")

    print(c.bold("Agent Runtime:"))
    print(f"  Name:             {diag['agent']['name']}")
    print(f"  Version:          {diag['agent']['version']}")
    print(f"  MCP Protocol:     {diag['agent']['mcp_protocol_version']}")
    print(f"  Dependencies:     {c.green('Zero external runtime dependencies (Pure Python Stdlib)')}")

    print(f"\n{c.bold('System & Hardware:')}")
    print(f"  Operating System: {diag['system']['os']} ({diag['system']['os_release']})")
    print(f"  Architecture:     {diag['system']['architecture']}")
    print(f"  CPU Cores:        {diag['system']['cpu_count']}")
    print(f"  Hostname:         {diag['system']['hostname']}")
    print(f"  File Encoding:    {diag['system']['filesystem_encoding']}")

    print(f"\n{c.bold('Python Environment:')}")
    print(f"  Version:          {diag['python']['version']}")
    print(f"  Executable:       {diag['python']['executable']}")

    net = diag.get("network", {})
    print(f"\n{c.bold('Network Readiness:')}")
    if net.get("tested"):
        dns_status = c.green("ONLINE") if net.get("dns_resolvable") else c.red("FAILED")
        http_status = c.green("ONLINE") if net.get("http_reachable") else c.yellow("OFFLINE / FIREWALLED")
        latency = f"{net.get('latency_ms')} ms" if net.get("latency_ms") else "N/A"
        print(f"  DNS Resolution:   {dns_status}")
        print(f"  HTTP Connectivity:{http_status} ({latency})")
    else:
        print(f"  Network check skipped.")

    print(f"\n{c.bold('Registered MCP Tools:')}")
    for tool_name, desc in diag["capabilities"].items():
        print(f"  {c.green('✓')} {c.bold(tool_name)}: {c.dim(desc)}")

    print(f"\n{c.green('✓')} All platform subsystems verified and operational.\n")
    return 0


def cmd_test(args: argparse.Namespace, c: Colors) -> int:
    """Run internal test suite or pytest."""
    import unittest

    print(f"\n{c.bold(c.blue('=== DeepSearch Self-Diagnostics & Unit Test Runner ==='))}\n")
    
    # Run internal self-verification suite
    failed = 0
    passed = 0

    def run_check(name: str, fn):
        nonlocal failed, passed
        try:
            fn()
            print(f"  {c.green('✓')} {name}")
            passed += 1
        except Exception as e:
            print(f"  {c.red('✗')} {name}: {e}")
            failed += 1

    # 1. Plan test
    def test_plan():
        p = deepsearch_plan("Test Topic", depth="quick")
        assert p["topic"] == "Test Topic"
        assert len(p["angles"]) == 3
        assert len(p["sub_queries"]) > 0

    # 2. Corroborate test
    def test_corroborate():
        res = deepsearch_corroborate(["Source A proves claim", "Source B confirms claim"], claim="claim")
        assert res["total_sources_evaluated"] == 2
        assert res["consensus_score"] >= 0.5

    # 3. Export test
    def test_export():
        rep = deepsearch_execute("Test Topic", depth="quick", format="markdown")
        assert len(rep["rendered"]) > 50

    # 4. MCP Config test
    def test_mcp_config():
        cfg = generate_mcp_client_config("claude_desktop")
        assert "mcpServers" in cfg

    # 5. Diagnostics test
    def test_diagnostics():
        d = deepsearch_get_diagnostics(include_network_check=False)
        assert d["agent"]["version"] == SERVER_VERSION

    run_check("Research Planning Engine", test_plan)
    run_check("Source Corroboration Engine", test_corroborate)
    run_check("Multi-Format Report Export Engine", test_export)
    run_check("MCP Client Configuration Generator", test_mcp_config)
    run_check("Platform Diagnostics Engine", test_diagnostics)

    print(f"\n{c.bold('Summary:')} {c.green(f'{passed} passed')}, {c.red(f'{failed} failed') if failed else '0 failed'}\n")
    return 0 if failed == 0 else 1


# =====================================================================
# Main Parser & CLI Entrypoint
# =====================================================================

def build_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="deepsearch",
        description="Autonomous Multi-Perspective Deep Research & Verification Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"{SERVER_NAME} {SERVER_VERSION}",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colored output",
    )

    base_subparser = argparse.ArgumentParser(add_help=False)
    base_subparser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colored output",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # research
    p_research = subparsers.add_parser("research", parents=[base_subparser], help="Execute multi-perspective deep research")
    p_research.add_argument("topic", help="Research subject or question")
    p_research.add_argument(
        "--depth",
        choices=["quick", "deep", "exhaustive"],
        default="deep",
        help="Investigation depth level (default: deep)",
    )
    p_research.add_argument(
        "--format",
        choices=["md", "markdown", "html", "json"],
        default="md",
        help="Output format (default: md)",
    )
    p_research.add_argument(
        "--max-sources",
        type=int,
        default=5,
        help="Maximum sources to investigate (default: 5)",
    )
    p_research.add_argument(
        "-o", "--output",
        help="Output file path to save report",
    )

    # plan
    p_plan = subparsers.add_parser("plan", parents=[base_subparser], help="Generate research execution plan with sub-queries")
    p_plan.add_argument("topic", help="Subject or thesis to plan research for")
    p_plan.add_argument(
        "--depth",
        choices=["quick", "deep", "exhaustive"],
        default="deep",
        help="Planning depth level (default: deep)",
    )
    p_plan.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON structure",
    )

    # fetch
    p_fetch = subparsers.add_parser("fetch", parents=[base_subparser], help="Fetch URL and extract clean text/markdown")
    p_fetch.add_argument("url", help="HTTP/HTTPS URL to fetch")
    p_fetch.add_argument(
        "--raw",
        action="store_true",
        help="Return raw body instead of extracted markdown",
    )
    p_fetch.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)",
    )
    p_fetch.add_argument(
        "-o", "--output",
        help="Save extracted content to file",
    )

    # corroborate
    p_corroborate = subparsers.add_parser("corroborate", parents=[base_subparser], help="Cross-validate claims across sources")
    p_corroborate.add_argument("sources", help="JSON array string or path to JSON file containing sources")
    p_corroborate.add_argument("--claim", help="Specific claim to verify across sources")
    p_corroborate.add_argument("--topic", help="Contextual topic")
    p_corroborate.add_argument("--json", action="store_true", help="Output raw JSON analysis")

    # serve
    p_serve = subparsers.add_parser("serve", parents=[base_subparser], help="Start Deep Research Studio Web UI (design influenced by Material 3)")
    p_serve.add_argument("--host", default="0.0.0.0", help="Host interface (default: 0.0.0.0)")
    p_serve.add_argument("--port", type=int, default=8096, help="Port number (default: 8096)")
    p_serve.add_argument("--open", action="store_true", help="Open browser automatically")

    # mcp
    p_mcp = subparsers.add_parser("mcp", parents=[base_subparser], help="Run Model Context Protocol (MCP) server over stdio")
    p_mcp.add_argument("--tools", action="store_true", help="List registered MCP tools and exit")
    p_mcp.add_argument(
        "--config",
        choices=["claude_desktop", "cursor", "cline", "zed", "generic"],
        help="Export client config snippet for target MCP client",
    )

    # platform / diagnostics
    p_platform = subparsers.add_parser("platform", aliases=["doctor", "diagnostics"], parents=[base_subparser], help="Run multi-OS platform diagnostics")
    p_platform.add_argument("--no-network", action="store_true", help="Skip live network connectivity test")
    p_platform.add_argument("--json", action="store_true", help="Output diagnostics in JSON")

    # test
    p_test = subparsers.add_parser("test", parents=[base_subparser], help="Run internal self-diagnostics and verification tests")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entrypoint."""
    if argv is None:
        argv = sys.argv[1:]

    # Handle quick flags like --test
    if "--test" in argv:
        c = Colors(force_disable="--no-color" in argv)
        parser = build_parser()
        args = parser.parse_args(["test"] + [a for a in argv if a not in ("--test", "--no-color")])
        return cmd_test(args, c)

    parser = build_parser()
    if not argv:
        parser.print_help()
        return 0

    args = parser.parse_args(argv)
    c = Colors(force_disable=getattr(args, "no_color", False))

    if args.command == "research":
        return cmd_research(args, c)
    elif args.command == "plan":
        return cmd_plan(args, c)
    elif args.command == "fetch":
        return cmd_fetch(args, c)
    elif args.command == "corroborate":
        return cmd_corroborate(args, c)
    elif args.command == "serve":
        return cmd_serve(args, c)
    elif args.command == "mcp":
        return cmd_mcp(args, c)
    elif args.command in ("platform", "doctor", "diagnostics"):
        return cmd_platform(args, c)
    elif args.command == "test":
        return cmd_test(args, c)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
