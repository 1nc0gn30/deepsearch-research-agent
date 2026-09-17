"""
test_crawler.py - Unit tests for crawler.py (HTMLTextExtractor, Credibility, WebCrawler).
"""

from unittest.mock import MagicMock, patch
import urllib.error
import pytest

from deepsearch_research_agent.crawler import (
    CrawlResult,
    ExtractedDocument,
    HTMLTextExtractor,
    MockSearchEngine,
    WebCrawler,
    compute_credibility_score,
)


def test_html_text_extractor_stripping_and_formatting():
    """Verify HTMLTextExtractor strips noise tags and preserves semantic markdown."""
    raw_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page Title</title>
        <meta name="description" content="A comprehensive analysis of system performance.">
        <meta name="author" content="Dr. Jane Doe">
        <link rel="canonical" href="https://example.com/test-page">
        <style>body { font-size: 14px; }</style>
        <script>console.log("ignore me");</script>
    </head>
    <body>
        <header><nav><a href="/home">Home</a></nav></header>
        <aside><p>Sidebar Advertisement</p></aside>
        <main>
            <h1>Main Title</h1>
            <p>This is the first introductory paragraph discussing core concepts.</p>
            <h2>Architectural Features</h2>
            <ul>
                <li>High throughput pipelining</li>
                <li>Zero-copy buffer allocation</li>
            </ul>
            <blockquote>Pipelining minimizes CPU stall cycles.</blockquote>
            <pre><code>def compute(x): return x * 2</code></pre>
        </main>
        <footer><p>Copyright 2026</p></footer>
    </body>
    </html>
    """

    extractor = HTMLTextExtractor()
    doc = extractor.extract(raw_html)

    assert isinstance(doc, ExtractedDocument)
    assert doc.title == "Test Page Title"
    assert doc.metadata.get("description") == "A comprehensive analysis of system performance."
    assert doc.metadata.get("author") == "Dr. Jane Doe"
    assert doc.metadata.get("canonical") == "https://example.com/test-page"
    assert "ignore me" not in doc.text
    assert "Sidebar Advertisement" not in doc.text
    assert "Copyright 2026" not in doc.text
    assert "Main Title" in doc.headings
    assert "Architectural Features" in doc.headings
    assert "# Main Title" in doc.markdown
    assert "## Architectural Features" in doc.markdown
    assert "* High throughput pipelining" in doc.markdown
    assert "> Pipelining minimizes CPU stall cycles." in doc.markdown
    assert "```" in doc.markdown
    assert doc.word_count > 10
    assert doc.reading_time_min > 0.0
    assert 0.0 <= doc.content_density_ratio <= 1.0


def test_credibility_score_calculation():
    """Verify credibility scoring for various domains, TLDs, and protocols."""
    # High authority whitelist
    assert compute_credibility_score("https://arxiv.org/abs/2301.00000") >= 95.0
    assert compute_credibility_score("https://nature.com/articles/123") >= 95.0
    assert compute_credibility_score("https://docs.python.org/3/library/") >= 95.0
    assert compute_credibility_score("https://en.wikipedia.org/wiki/Python") >= 85.0

    # TLD heuristics
    assert compute_credibility_score("https://agency.gov/report") >= 85.0
    assert compute_credibility_score("https://university.edu/paper") >= 80.0
    assert compute_credibility_score("https://cambridge.ac.uk/research") >= 80.0
    assert compute_credibility_score("https://open-foundation.org/spec") >= 65.0

    # Suspicious / spam TLDs
    assert compute_credibility_score("http://free-crypto-spambot.xyz") <= 45.0

    # Bounded range checks
    for test_url in ["", "https://sub.domain.deep.nested.foo.bar.baz.com", "http://insecure.net"]:
        score = compute_credibility_score(test_url)
        assert 10.0 <= score <= 99.0


def test_mock_search_engine():
    """Verify MockSearchEngine produces structured results and simulated content."""
    results = MockSearchEngine.generate_mock_results("Vector Database Indexing HNSW vs IVF", num_results=4)
    assert len(results) == 4
    for r in results:
        assert "url" in r
        assert "title" in r
        assert "snippet" in r
        assert "source_type" in r
        assert "mock_html" in r
        assert "arxiv.org" in r["url"] or "docs.python.org" in r["url"] or "github.com" in r["url"] or "nature.com" in r["url"]


def test_web_crawler_search_and_crawl_mock():
    """Verify WebCrawler executes search and parses results using mock engine."""
    crawler = WebCrawler()
    crawl_results = crawler.search_and_crawl("Distributed Stream Processing", max_results=3, use_mock=True)

    assert len(crawl_results) == 3
    for cr in crawl_results:
        assert isinstance(cr, CrawlResult)
        assert cr.status_code == 200
        assert cr.title
        assert cr.text
        assert cr.markdown
        assert cr.credibility_score >= 50.0
        assert cr.word_count > 20
        assert cr.reading_time_min > 0.0


def test_web_crawler_cache():
    """Verify in-memory caching avoids re-crawling duplicate URLs."""
    crawler = WebCrawler()
    mock_res = MockSearchEngine.generate_mock_results("Caching Test", num_results=1)[0]
    
    # Pre-populate cache
    fake_result = CrawlResult(
        url="https://cached-example.com",
        status_code=200,
        title="Cached Page",
        text="Cached body",
        markdown="# Cached Page",
        headings=["Cached Page"],
        metadata={},
        links=[],
        credibility_score=80.0,
        word_count=2,
        reading_time_min=0.01,
    )
    crawler._cache["https://cached-example.com"] = fake_result

    # Fetch should return cached directly
    res = crawler.fetch("https://cached-example.com")
    assert res.title == "Cached Page"
    assert res.text == "Cached body"


def test_web_crawler_error_handling():
    """Verify WebCrawler handles HTTP errors and network failures gracefully."""
    crawler = WebCrawler(timeout=2)

    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError("http://example.com/404", 404, "Not Found", {}, None)):
        res = crawler.fetch("http://example.com/404")
        assert res.status_code == 404
        assert res.error is not None
        assert "HTTP 404" in res.error

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
        res_conn = crawler.fetch("http://unreachable-host.local")
        assert res_conn.status_code == 0
        assert res_conn.error is not None
        assert "Connection refused" in res_conn.error


def test_web_crawler_fetch_all_concurrency():
    """Verify fetch_all handles multiple URLs concurrently."""
    crawler = WebCrawler()
    urls = [
        "https://arxiv.org/test1",
        "https://docs.python.org/test2",
        "https://nature.com/test3",
    ]
    
    # Mock fetch method for deterministic unit test
    def mock_fetch(url, timeout=None):
        return CrawlResult(
            url=url,
            status_code=200,
            title=f"Title for {url}",
            text=f"Content for {url}",
            markdown=f"# {url}",
            headings=[url],
            metadata={},
            links=[],
            credibility_score=85.0,
            word_count=3,
            reading_time_min=0.01,
        )

    with patch.object(crawler, "fetch", side_effect=mock_fetch):
        results = crawler.fetch_all(urls, max_workers=3)
        assert len(results) == 3
        returned_urls = {r.url for r in results}
        assert returned_urls == set(urls)
