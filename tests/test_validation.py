import pytest
from datetime import datetime, timezone, timedelta
from src.validators.validator import DataValidator

def test_validate_startup_success():
    validator = DataValidator()
    data = {
        "name": "Perplexity",
        "website": "https://perplexity.ai",
        "source_name": "Test",
        "source_url": "https://test.com",
        "collected_at": datetime.now(timezone.utc)
    }
    record, err = validator.validate_startup(data)
    assert err is None
    assert record is not None
    assert record.name == "Perplexity"

def test_validate_duplicate_rejection():
    validator = DataValidator()
    data = {
        "name": "Scale AI",
        "website": "https://scale.com",
        "source_name": "Test",
        "source_url": "https://test.com",
        "collected_at": datetime.now(timezone.utc)
    }
    rec1, err1 = validator.validate_startup(data)
    assert rec1 is not None

    # Second submission is duplicate
    rec2, err2 = validator.validate_startup(data)
    assert rec2 is None
    assert "Duplicate" in err2

def test_freshness_rolling_window_24h_accepted():
    validator = DataValidator(rolling_window_hours=24)
    # Published 2 hours ago
    pub_dt = datetime.now(timezone.utc) - timedelta(hours=2)
    job_data = {
        "job_title": "Machine Learning Engineer",
        "company_name": "OpenAI",
        "job_url": "https://openai.com/jobs/1",
        "published_at": pub_dt.isoformat(),
        "source_name": "Careers",
        "source_url": "https://openai.com/careers",
        "collected_at": datetime.now(timezone.utc)
    }
    record, err = validator.validate_job(job_data, enforce_freshness=True)
    assert err is None
    assert record is not None

def test_freshness_rolling_window_24h_rejected():
    validator = DataValidator(rolling_window_hours=24)
    # Published 48 hours ago
    stale_dt = datetime.now(timezone.utc) - timedelta(hours=48)
    news_data = {
        "title": "Old News Announcement",
        "article_url": "https://news.com/old",
        "published_at": stale_dt.isoformat(),
        "source_name": "News Site",
        "source_url": "https://news.com",
        "collected_at": datetime.now(timezone.utc)
    }
    record, err = validator.validate_news(news_data, enforce_freshness=True)
    assert record is None
    assert "exceeds" in err and "freshness window" in err

