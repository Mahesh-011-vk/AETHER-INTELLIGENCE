import pytest
from datetime import datetime, timezone
from src.models.schemas import (
    StartupRecord,
    ProductRecord,
    ResearchPaperRecord,
    JobRecord,
    NewsRecord,
    EntityMappingRecord,
)

def test_startup_schema_valid():
    startup = StartupRecord(
        name="Mistral AI",
        website="https://mistral.ai",
        headquarters="Paris, France",
        funding_stage="Series B",
        total_funding_usd=1100000000.0,
        focus_areas=["Open Weights", "LLMs"],
        source_name="Test Source",
        source_url="https://source.example.com",
        collected_at=datetime.now(timezone.utc)
    )
    assert startup.name == "Mistral AI"
    assert startup.total_funding_usd == 1100000000.0
    assert startup.website == "https://mistral.ai"
    assert startup.collected_at.tzinfo == timezone.utc

def test_product_schema_valid():
    product = ProductRecord(
        name="Llama-3-70b",
        company_name="Meta",
        product_url="https://huggingface.co/meta-llama/Llama-3-70b",
        category="Text Generation",
        pricing_model="Open Source",
        github_stars=50000,
        source_name="Hugging Face",
        source_url="https://huggingface.co/api/models",
        collected_at=datetime.now(timezone.utc)
    )
    assert product.name == "Llama-3-70b"
    assert product.pricing_model == "Open Source"
    assert product.github_stars == 50000

def test_research_paper_schema_valid():
    paper = ResearchPaperRecord(
        title="Attention Is All You Need",
        authors=["Vaswani et al."],
        arxiv_id="1706.03762",
        paper_url="https://arxiv.org/abs/1706.03762",
        published_date=datetime(2017, 6, 12, tzinfo=timezone.utc),
        primary_category="cs.CL",
        categories=["cs.CL", "cs.AI"],
        source_name="ArXiv",
        source_url="http://export.arxiv.org/api/query",
        collected_at=datetime.now(timezone.utc)
    )
    assert paper.title == "Attention Is All You Need"
    assert paper.primary_category == "cs.CL"
    assert paper.published_date.tzinfo == timezone.utc

def test_job_schema_valid():
    job = JobRecord(
        job_title="Senior AI Research Engineer",
        company_name="Anthropic",
        location="San Francisco, CA",
        remote_eligibility="Hybrid",
        job_url="https://anthropic.com/careers/ai-engineer",
        published_at=datetime.now(timezone.utc),
        source_name="Company Site",
        source_url="https://anthropic.com/careers",
        collected_at=datetime.now(timezone.utc)
    )
    assert job.job_title == "Senior AI Research Engineer"
    assert job.company_name == "Anthropic"

def test_news_schema_valid():
    news = NewsRecord(
        title="DeepMind Unveils New Multimodal Breakthrough",
        source_name="Tech Publication",
        article_url="https://tech.example.com/deepmind-breakthrough",
        published_at=datetime.now(timezone.utc),
        summary="DeepMind announced a major advance in reasoning.",
        key_entities=["DeepMind", "Reasoning"],
        sentiment_category="Breakthrough",
        source_name_val="Test",
        source_url="https://tech.example.com",
        collected_at=datetime.now(timezone.utc)
    )
    assert news.title == "DeepMind Unveils New Multimodal Breakthrough"
    assert news.article_url == "https://tech.example.com/deepmind-breakthrough"

def test_entity_mapping_schema():
    mapping = EntityMappingRecord(
        raw_name="OpenAI Inc.",
        canonical_name="OpenAI",
        entity_type="Startup",
        source="Curated Directory",
        confidence_score=95.0,
        resolution_method="RuleNormalized",
        timestamp=datetime.now(timezone.utc)
    )
    assert mapping.raw_name == "OpenAI Inc."
    assert mapping.canonical_name == "OpenAI"
    assert mapping.confidence_score == 95.0

