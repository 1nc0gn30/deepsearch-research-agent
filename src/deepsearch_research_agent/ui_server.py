#!/usr/bin/env python3
"""
Zero-Dependency Web UI Server & REST API for DeepSearch Research Agent.

Serves Google Material 3 Deep Research Studio frontend and provides REST endpoints for
planning, deep research execution, content fetching, claim corroboration, report export,
MCP configuration delivery, and ZIP research bundle generation.
"""

from __future__ import annotations

import html
import io
import json
import logging
import mimetypes
import os
import sys
import time
import urllib.parse
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple

from deepsearch_research_agent.mcp_server import (
    SERVER_NAME,
    SERVER_VERSION,
    deepsearch_corroborate,
    deepsearch_execute,
    deepsearch_export_report,
    deepsearch_fetch,
    deepsearch_get_diagnostics,
    deepsearch_plan,
    generate_mcp_client_config,
)

logger = logging.getLogger("deepsearch_research_agent.ui_server")
SERVER_START_TIME = time.time()


# =====================================================================
# Fallback Embedded Material 3 Web UI (if public/index.html is absent)
# =====================================================================

EMBEDDED_STUDIO_HTML = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DeepSearch Research Studio &bull; Google Material 3</title>
  <style>
    :root {
      --md-sys-color-primary: #a8c7fa;
      --md-sys-color-on-primary: #062e6f;
      --md-sys-color-primary-container: #0842a0;
      --md-sys-color-on-primary-container: #d3e3fd;
      --md-sys-color-surface: #111318;
      --md-sys-color-surface-container: #1e1f25;
      --md-sys-color-surface-container-high: #282a30;
      --md-sys-color-on-surface: #e2e2e9;
      --md-sys-color-on-surface-variant: #c4c6d0;
      --md-sys-color-outline: #8e9099;
      --md-sys-color-outline-variant: #44474f;
      --md-sys-color-secondary-container: #334460;
      --md-sys-color-tertiary: #a6cc70;
      --font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', Oxygen, Ubuntu, Cantarell, sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--md-sys-color-surface);
      color: var(--md-sys-color-on-surface);
      font-family: var(--font-family);
      line-height: 1.6;
      padding: 1.5rem;
    }
    .app-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--md-sys-color-outline-variant);
      margin-bottom: 1.5rem;
    }
    .app-title {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      color: var(--md-sys-color-primary);
      font-size: 1.6rem;
      font-weight: 700;
    }
    .badge {
      font-size: 0.75rem;
      background: var(--md-sys-color-secondary-container);
      color: var(--md-sys-color-on-surface);
      padding: 0.2rem 0.6rem;
      border-radius: 6px;
    }
    .grid {
      display: grid;
      grid-template-columns: 340px 1fr;
      gap: 1.5rem;
    }
    @media (max-width: 900px) {
      .grid { grid-template-columns: 1fr; }
    }
    .panel {
      background: var(--md-sys-color-surface-container);
      border: 1px solid var(--md-sys-color-outline-variant);
      border-radius: 16px;
      padding: 1.5rem;
    }
    .panel h2 {
      font-size: 1.15rem;
      color: var(--md-sys-color-primary);
      margin-bottom: 1rem;
    }
    .form-group {
      margin-bottom: 1.25rem;
    }
    label {
      display: block;
      font-size: 0.85rem;
      color: var(--md-sys-color-on-surface-variant);
      margin-bottom: 0.35rem;
      font-weight: 500;
    }
    input[type="text"], select, textarea {
      width: 100%;
      background: var(--md-sys-color-surface-container-high);
      border: 1px solid var(--md-sys-color-outline-variant);
      color: var(--md-sys-color-on-surface);
      padding: 0.75rem 1rem;
      border-radius: 8px;
      font-size: 0.95rem;
      font-family: inherit;
    }
    input:focus, select:focus, textarea:focus {
      outline: none;
      border-color: var(--md-sys-color-primary);
    }
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: var(--md-sys-color-primary);
      color: var(--md-sys-color-on-primary);
      border: none;
      padding: 0.75rem 1.5rem;
      border-radius: 10px;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      width: 100%;
      transition: opacity 0.2s;
    }
    .btn:hover { opacity: 0.9; }
    .btn-secondary {
      background: var(--md-sys-color-surface-container-high);
      color: var(--md-sys-color-primary);
      border: 1px solid var(--md-sys-color-outline-variant);
      margin-top: 0.5rem;
    }
    .results-panel {
      min-height: 480px;
    }
    .status-bar {
      display: flex;
      gap: 1rem;
      font-size: 0.85rem;
      color: var(--md-sys-color-on-surface-variant);
      margin-bottom: 1rem;
    }
    pre.output-view {
      background: #090a0f;
      border: 1px solid var(--md-sys-color-outline-variant);
      border-radius: 12px;
      padding: 1.25rem;
      overflow-x: auto;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 0.88rem;
      max-height: 540px;
      white-space: pre-wrap;
    }
  </style>
</head>
<body>
  <header class="app-header">
    <div class="app-title">
      <span>&#x1F50D; DeepSearch Research Studio</span>
      <span class="badge">Material 3</span>
      <span class="badge">Zero Dependencies</span>
    </div>
    <div id="health-badge" class="badge" style="background:#1b4d2e; color:#a6cc70;">System Online</div>
  </header>

  <div class="grid">
    <aside class="panel">
      <h2>Research Parameters</h2>
      <div class="form-group">
        <label for="topic-input">Investigation Topic</label>
        <input type="text" id="topic-input" placeholder="e.g., Quantum Computing Fault Tolerance" value="Autonomous AI Agent Architecture">
      </div>
      <div class="form-group">
        <label for="depth-select">Investigation Depth</label>
        <select id="depth-select">
          <option value="quick">Quick (3 Angles &bull; Fast)</option>
          <option value="deep" selected>Deep (5 Angles &bull; Comprehensive)</option>
          <option value="exhaustive">Exhaustive (8 Angles &bull; Maximum)</option>
        </select>
      </div>
      <div class="form-group">
        <label for="format-select">Report Output Format</label>
        <select id="format-select">
          <option value="markdown" selected>Markdown (GitHub Flavored)</option>
          <option value="html">Material 3 HTML</option>
          <option value="json">Structured JSON</option>
        </select>
      </div>
      <button class="btn" id="run-btn" onclick="executeResearch()">Execute Deep Research</button>
      <button class="btn btn-secondary" id="plan-btn" onclick="generatePlan()">Generate Research Plan</button>
      <button class="btn btn-secondary" id="bundle-btn" onclick="downloadBundle()">Download ZIP Bundle</button>
    </aside>

    <main class="panel results-panel">
      <div class="status-bar">
        <span id="status-text">Ready for investigation</span>
        <span id="timing-text"></span>
      </div>
      <pre id="output" class="output-view">Ready. Enter a topic and click 'Execute Deep Research' or 'Generate Research Plan'.</pre>
    </main>
  </div>

  <script>
    let currentReport = null;

    async function executeResearch() {
      const topic = document.getElementById('topic-input').value.trim();
      const depth = document.getElementById('depth-select').value;
      const format = document.getElementById('format-select').value;
      if (!topic) return alert('Please enter a research topic.');

      document.getElementById('status-text').innerText = 'Synthesizing multi-angle deep research...';
      document.getElementById('output').innerText = 'Investigating and corroborating across angles...';
      const t0 = performance.now();

      try {
        const resp = await fetch('/api/research', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic, depth, format })
        });
        const data = await resp.json();
        currentReport = data.report_data || data;
        const elapsed = ((performance.now() - t0) / 1000).toFixed(2);
        document.getElementById('status-text').innerText = 'Research synthesis complete';
        document.getElementById('timing-text').innerText = `Completed in ${elapsed}s`;
        
        if (data.rendered) {
          document.getElementById('output').innerText = data.rendered;
        } else {
          document.getElementById('output').innerText = JSON.stringify(data, null, 2);
        }
      } catch (err) {
        document.getElementById('status-text').innerText = 'Error executing research';
        document.getElementById('output').innerText = 'Error: ' + err.message;
      }
    }

    async function generatePlan() {
      const topic = document.getElementById('topic-input').value.trim();
      const depth = document.getElementById('depth-select').value;
      if (!topic) return alert('Please enter a topic for planning.');

      document.getElementById('status-text').innerText = 'Generating investigative angles...';
      try {
        const resp = await fetch('/api/plan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic, depth })
        });
        const data = await resp.json();
        document.getElementById('status-text').innerText = 'Plan generated';
        document.getElementById('output').innerText = JSON.stringify(data, null, 2);
      } catch (err) {
        document.getElementById('output').innerText = 'Error: ' + err.message;
      }
    }

    async function downloadBundle() {
      if (!currentReport) {
        // Run quick research first if none exists
        await executeResearch();
      }
      const topic = document.getElementById('topic-input').value.trim() || 'research-bundle';
      try {
        const resp = await fetch('/api/export-bundle', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ report: currentReport, topic })
        });
        const blob = await resp.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `deepsearch-${topic.toLowerCase().replace(/\\s+/g, '-')}-bundle.zip`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      } catch (err) {
        alert('Bundle export failed: ' + err.message);
      }
    }
  </script>
</body>
</html>"""


# =====================================================================
# DeepSearch HTTP Request Handler
# =====================================================================

class DeepSearchRequestHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for DeepSearch Studio and REST APIs."""

    server_version = f"{SERVER_NAME}/{SERVER_VERSION}"

    def _set_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def _send_json(self, data: Any, status: int = 200) -> None:
        payload = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def _send_error_json(self, message: str, status: int = 400) -> None:
        self._send_json({"error": message, "status": status}, status=status)

    def _read_json_body(self) -> Optional[Dict[str, Any]]:
        content_length_header = self.headers.get("Content-Length")
        if not content_length_header:
            return {}
        try:
            length = int(content_length_header)
            raw_data = self.rfile.read(length).decode("utf-8")
            if not raw_data.strip():
                return {}
            return json.loads(raw_data)
        except Exception as e:
            logger.warning(f"Error parsing JSON request body: {e}")
            return None

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests."""
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        """Route GET requests for static assets and REST API endpoints."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)

        # REST API Routes
        if path == "/api/health":
            self._send_json({
                "status": "ok",
                "name": SERVER_NAME,
                "version": SERVER_VERSION,
                "uptime_seconds": round(time.time() - SERVER_START_TIME, 2),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })
            return

        elif path == "/api/diagnostics":
            check_net = query_params.get("network", ["true"])[0].lower() == "true"
            diag = deepsearch_get_diagnostics(include_network_check=check_net)
            self._send_json(diag)
            return

        elif path == "/api/mcp/config":
            client_name = query_params.get("client", ["claude_desktop"])[0]
            py_path = query_params.get("python", [sys.executable or "python3"])[0]
            cfg = generate_mcp_client_config(client_name=client_name, python_path=py_path)
            self._send_json({
                "client": client_name,
                "config": cfg,
            })
            return

        # Static File Routing
        self._serve_static_or_ui(path)

    def do_POST(self) -> None:
        """Route POST requests for research, planning, fetching, and exporting."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_json_body()

        if body is None:
            self._send_error_json("Invalid JSON payload in request body", status=400)
            return

        try:
            if path == "/api/plan":
                topic = body.get("topic", "")
                depth = body.get("depth", "deep")
                focus_areas = body.get("focus_areas")
                if not topic:
                    self._send_error_json("Field 'topic' is required", status=400)
                    return
                res = deepsearch_plan(topic=topic, depth=depth, focus_areas=focus_areas)
                self._send_json(res)

            elif path == "/api/research":
                topic = body.get("topic", "")
                depth = body.get("depth", "deep")
                out_format = body.get("format", "markdown")
                max_sources = int(body.get("max_sources", 5))
                if not topic:
                    self._send_error_json("Field 'topic' is required", status=400)
                    return
                res = deepsearch_execute(topic=topic, depth=depth, format=out_format, max_sources=max_sources)
                self._send_json(res)

            elif path == "/api/fetch":
                url = body.get("url", "")
                raw = bool(body.get("raw", False))
                timeout = int(body.get("timeout", 10))
                if not url:
                    self._send_error_json("Field 'url' is required", status=400)
                    return
                res = deepsearch_fetch(url=url, raw=raw, timeout=timeout)
                self._send_json(res)

            elif path == "/api/corroborate":
                sources = body.get("sources", [])
                claim = body.get("claim")
                topic = body.get("topic")
                if not sources:
                    self._send_error_json("Field 'sources' must contain at least one item", status=400)
                    return
                res = deepsearch_corroborate(sources=sources, claim=claim, topic=topic)
                self._send_json(res)

            elif path == "/api/export":
                report_data = body.get("report", body.get("report_data", {}))
                out_format = body.get("format", "markdown")
                output_path = body.get("output_path")
                if not report_data:
                    self._send_error_json("Field 'report' is required", status=400)
                    return
                res = deepsearch_export_report(report_data=report_data, format=out_format, output_path=output_path)
                self._send_json(res)

            elif path == "/api/export-bundle":
                report_data = body.get("report", body.get("report_data", {}))
                topic = body.get("topic", report_data.get("topic", "research-dossier"))
                if not report_data:
                    # Auto-generate if only topic provided
                    report_data = deepsearch_execute(topic=topic, depth="deep", format="json")

                # Generate ZIP bundle in memory
                zip_bytes = self._create_bundle_zip(report_data, topic)
                safe_filename = f"deepsearch-{topic.lower().replace(' ', '-')}-bundle.zip"

                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Disposition", f'attachment; filename="{safe_filename}"')
                self.send_header("Content-Length", str(len(zip_bytes)))
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(zip_bytes)

            else:
                self._send_error_json(f"Endpoint '{path}' not found", status=404)

        except Exception as e:
            logger.error(f"Error handling POST {path}: {e}", exc_info=True)
            self._send_error_json(f"Internal server error: {str(e)}", status=500)

    def _create_bundle_zip(self, report_data: Dict[str, Any], topic: str) -> bytes:
        """Create a complete research export ZIP bundle."""
        md_export = deepsearch_export_report(report_data, format="markdown")
        html_export = deepsearch_export_report(report_data, format="html")
        json_export = json.dumps(report_data, indent=2, ensure_ascii=False)

        sources_json = json.dumps(report_data.get("sources", []), indent=2, ensure_ascii=False)
        metrics_json = json.dumps(report_data.get("metrics", {}), indent=2, ensure_ascii=False)
        corroboration_json = json.dumps(report_data.get("corroboration_matrix", {}), indent=2, ensure_ascii=False)

        readme_content = f"""# DeepSearch Research Dossier: {topic}

Autonomous Multi-Perspective Deep Research & Verification Export Bundle.
Generated: {report_data.get('generated_at', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))}

## Bundle Contents:
1. `report.md` - Full research report in GitHub-flavored Markdown
2. `report.html` - Interactive Material 3 standalone report with styling
3. `report.json` - Complete raw research dossier in structured JSON
4. `sources.json` - Normalized references and citation excerpts
5. `metrics.json` - Analytical verification metrics, consensus rating, duration
6. `corroboration.json` - Multi-source cross-validation matrix
"""

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("README.md", readme_content)
            zf.writestr("report.md", md_export["content"])
            zf.writestr("report.html", html_export["content"])
            zf.writestr("report.json", json_export)
            zf.writestr("sources.json", sources_json)
            zf.writestr("metrics.json", metrics_json)
            zf.writestr("corroboration.json", corroboration_json)

        buffer.seek(0)
        return buffer.getvalue()

    def _serve_static_or_ui(self, path: str) -> None:
        """Serve files from public/ directory or fallback to embedded Material 3 UI."""
        # Locate public directory relative to repo root or package
        possible_public_dirs = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "public")),
            os.path.abspath(os.path.join(os.getcwd(), "public")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "public")),
        ]

        public_dir = None
        for p in possible_public_dirs:
            if os.path.isdir(p):
                public_dir = p
                break

        if path in ("/", "/index.html", ""):
            index_path = os.path.join(public_dir, "index.html") if public_dir else None
            if index_path and os.path.isfile(index_path):
                self._serve_file(index_path)
                return
            else:
                # Serve embedded Google Material 3 UI
                body = EMBEDDED_STUDIO_HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(body)
                return

        # Serve static asset from public directory
        if public_dir:
            clean_rel_path = path.lstrip("/")
            file_path = os.path.abspath(os.path.join(public_dir, clean_rel_path))
            # Security check: directory traversal protection
            if file_path.startswith(public_dir) and os.path.isfile(file_path):
                self._serve_file(file_path)
                return

        self._send_error_json(f"File '{path}' not found", status=404)

    def _serve_file(self, filepath: str) -> None:
        """Serve a filesystem file with appropriate MIME type."""
        try:
            mime_type, _ = mimetypes.guess_type(filepath)
            if mime_type is None:
                mime_type = "application/octet-stream"

            with open(filepath, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8" if "text" in mime_type or "json" in mime_type or "javascript" in mime_type else mime_type)
            self.send_header("Content-Length", str(len(content)))
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self._send_error_json(f"Error serving file: {str(e)}", status=500)

    def log_message(self, format: str, *args: Any) -> None:
        """Custom clean logging format."""
        logger.info(f"{self.address_string()} - - [{self.log_date_time_string()}] {format % args}")


# =====================================================================
# Server Launcher
# =====================================================================

def run_ui_server(
    host: str = "0.0.0.0",
    port: int = 8096,
    open_browser: bool = False
) -> ThreadingHTTPServer:
    """Start and run the DeepSearch Threading HTTPServer."""
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, DeepSearchRequestHandler)

    url = f"http://{'localhost' if host in ('0.0.0.0', '127.0.0.1') else host}:{port}"
    print(f"\n=======================================================")
    print(f" DeepSearch Research Studio (Material 3 UI)")
    print(f" URL:  {url}")
    print(f" Port: {port} | Host: {host}")
    print(f" Mode: Pure Python Stdlib (Zero External Dependencies)")
    print(f"=======================================================\n")

    if open_browser:
        import webbrowser
        try:
            webbrowser.open(url)
        except Exception:
            pass

    return httpd


if __name__ == "__main__":
    port_num = int(sys.argv[1]) if len(sys.argv) > 1 else 8096
    server = run_ui_server(port=port_num)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down DeepSearch Research Studio server...")
        server.shutdown()
