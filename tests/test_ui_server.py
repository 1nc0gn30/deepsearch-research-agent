#!/usr/bin/env python3
"""Comprehensive Unit Tests for UI Server & REST API Endpoints."""

import io
import json
import threading
import time
import unittest
import urllib.error
import urllib.request
import zipfile
from http.server import ThreadingHTTPServer
from unittest.mock import MagicMock, patch

from deepsearch_research_agent.mcp_server import SERVER_NAME, SERVER_VERSION
from deepsearch_research_agent.ui_server import DeepSearchRequestHandler


class TestUIServer(unittest.TestCase):
    """Test REST API endpoints, CORS, static file serving, and ZIP bundle exports."""

    @classmethod
    def setUpClass(cls):
        # Start ThreadingHTTPServer on an ephemeral port (port 0)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), DeepSearchRequestHandler)
        cls.port = cls.server.server_port
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: dict = None,
        headers: dict = None,
    ) -> tuple[int, dict, bytes]:
        url = f"{self.base_url}{endpoint}"
        req_headers = headers or {}
        body_bytes = None

        if data is not None:
            body_bytes = json.dumps(data).encode("utf-8")
            req_headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.getcode()
                resp_headers = dict(resp.headers)
                resp_body = resp.read()
                return status, resp_headers, resp_body
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read()

    def test_cors_preflight_options(self):
        status, headers, _ = self._make_request("/api/research", method="OPTIONS")
        self.assertEqual(status, 204)
        self.assertEqual(headers.get("Access-Control-Allow-Origin"), "*")
        self.assertIn("POST", headers.get("Access-Control-Allow-Methods", ""))

    def test_get_health(self):
        status, headers, body = self._make_request("/api/health")
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["name"], SERVER_NAME)
        self.assertEqual(data["version"], SERVER_VERSION)
        self.assertIn("uptime_seconds", data)

    def test_get_diagnostics(self):
        status, _, body = self._make_request("/api/diagnostics?network=false")
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertEqual(data["agent"]["name"], SERVER_NAME)
        self.assertIn("system", data)
        self.assertIn("capabilities", data)

    def test_get_mcp_config(self):
        status, _, body = self._make_request("/api/mcp/config?client=cursor")
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertEqual(data["client"], "cursor")
        self.assertIn("mcpServers", data["config"])

    def test_post_plan(self):
        status, _, body = self._make_request(
            "/api/plan",
            method="POST",
            data={"topic": "Neuromorphic Computing", "depth": "quick"},
        )
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertEqual(data["topic"], "Neuromorphic Computing")
        self.assertEqual(len(data["angles"]), 3)

    def test_post_plan_missing_topic(self):
        status, _, body = self._make_request(
            "/api/plan",
            method="POST",
            data={"topic": ""},
        )
        self.assertEqual(status, 400)
        data = json.loads(body.decode("utf-8"))
        self.assertIn("error", data)

    def test_post_research(self):
        status, _, body = self._make_request(
            "/api/research",
            method="POST",
            data={"topic": "Retrieval Augmented Generation", "depth": "quick", "format": "json"},
        )
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertEqual(data["topic"], "Retrieval Augmented Generation")
        self.assertIn("executive_summary", data)
        self.assertIn("metrics", data)

    def test_post_fetch(self):
        with patch("deepsearch_research_agent.ui_server.deepsearch_fetch") as mock_fetch:
            mock_fetch.return_value = {
                "status": 200,
                "title": "Fetch Test",
                "content": "Fetched paragraph content",
                "raw": False,
                "url": "https://example.com/page",
            }
            status, _, body = self._make_request(
                "/api/fetch",
                method="POST",
                data={"url": "https://example.com/page", "raw": False},
            )
            self.assertEqual(status, 200)
            data = json.loads(body.decode("utf-8"))
            self.assertEqual(data["status"], 200)
            self.assertEqual(data["title"], "Fetch Test")
            self.assertIn("Fetched paragraph", data["content"])

    def test_post_corroborate(self):
        sources = [
            "Source A: Benchmark score is 94.2%.",
            "Source B: Independent benchmark confirms 94.2% score.",
        ]
        status, _, body = self._make_request(
            "/api/corroborate",
            method="POST",
            data={"sources": sources, "claim": "Benchmark score"},
        )
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertEqual(data["total_sources_evaluated"], 2)
        self.assertGreaterEqual(data["consensus_score"], 0.8)

    def test_post_export(self):
        report_data = {
            "topic": "Edge AI",
            "executive_summary": "Edge AI is growing rapidly.",
            "key_findings": ["Low latency", "Privacy preservation"],
            "perspectives": [],
            "corroboration_matrix": {},
            "metrics": {},
            "sources": [],
            "actionable_takeaways": [],
        }
        status, _, body = self._make_request(
            "/api/export",
            method="POST",
            data={"report": report_data, "format": "html"},
        )
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertEqual(data["format"], "html")
        self.assertIn("<!DOCTYPE html>", data["content"])

    def test_post_export_bundle_zip(self):
        report_data = {
            "topic": "Synthetic Biology",
            "executive_summary": "Synthetic Biology overview.",
            "key_findings": ["CRISPR tools advanced"],
            "perspectives": [],
            "corroboration_matrix": {},
            "metrics": {},
            "sources": [],
            "actionable_takeaways": [],
        }
        status, headers, body = self._make_request(
            "/api/export-bundle",
            method="POST",
            data={"report": report_data, "topic": "Synthetic Biology"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("Content-Type"), "application/zip")
        self.assertIn("deepsearch-synthetic-biology-bundle.zip", headers.get("Content-Disposition", ""))

        # Verify ZIP archive structure
        zip_buf = io.BytesIO(body)
        with zipfile.ZipFile(zip_buf, "r") as zf:
            file_list = zf.namelist()
            self.assertIn("README.md", file_list)
            self.assertIn("report.md", file_list)
            self.assertIn("report.html", file_list)
            self.assertIn("report.json", file_list)
            self.assertIn("sources.json", file_list)
            self.assertIn("metrics.json", file_list)
            self.assertIn("corroboration.json", file_list)

            # Check that markdown report is readable
            md_content = zf.read("report.md").decode("utf-8")
            self.assertIn("Synthetic Biology", md_content)

    def test_serve_embedded_studio_html(self):
        status, headers, body = self._make_request("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers.get("Content-Type", ""))
        html_str = body.decode("utf-8")
        self.assertTrue("DeepResearch" in html_str or "Deep Research" in html_str or "DeepSearch" in html_str)

    def test_endpoint_not_found(self):
        status, _, body = self._make_request("/api/nonexistent_route")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
