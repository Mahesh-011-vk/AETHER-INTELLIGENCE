import pytest
from datetime import datetime, timezone
from src.extractors.html_extractor import HTMLExtractor
from src.extractors.date_extractor import DateExtractor

def test_html_extractor_text_cleaning():
    raw_html = """
    <html>
        <head><title>AI Research Lab</title></head>
        <body>
            <nav><a href="/home">Home</a></nav>
            <h1>Artificial Intelligence</h1>
            <p>We are advancing machine learning research.</p>
            <script>console.log("ignore me");</script>
            <footer>Copyright 2026</footer>
        </body>
    </html>
    """
    clean = HTMLExtractor.extract_clean_text(raw_html)
    assert "Artificial Intelligence" in clean
    assert "We are advancing machine learning research" in clean
    assert "ignore me" not in clean
    assert "Copyright" not in clean

def test_html_extractor_metadata():
    raw_html = """
    <html>
        <head>
            <title>State of AI Report</title>
            <meta name="description" content="Annual overview of AI ecosystem." />
            <meta property="og:title" content="State of AI" />
        </head>
        <body></body>
    </html>
    """
    meta = HTMLExtractor.extract_metadata(raw_html)
    assert meta["title"] == "State of AI Report"
    assert meta["description"] == "Annual overview of AI ecosystem."
    assert meta["og_title"] == "State of AI"

def test_date_extractor_various_formats():
    # RFC 2822
    dt1 = DateExtractor.parse_datetime("Sun, 22 Nov 2026 14:00:00 GMT")
    assert dt1 is not None
    assert dt1.tzinfo == timezone.utc

    # ISO 8601
    dt2 = DateExtractor.parse_datetime("2026-11-22T10:30:00Z")
    assert dt2 is not None
    assert dt2.hour == 10

    # Relative date
    dt3 = DateExtractor.parse_datetime("3 hours ago")
    assert dt3 is not None
    assert DateExtractor.is_within_rolling_window(dt3, hours=24)

