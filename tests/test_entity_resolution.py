import pytest
from src.entity_resolution.resolver import EntityResolver

def test_normalize_removes_legal_suffixes():
    resolver = EntityResolver()
    assert resolver.normalize("OpenAI, Inc.") == "openai"
    assert resolver.normalize("Anthropic PBC") == "anthropic"
    assert resolver.normalize("Google LLC") == "google"
    assert resolver.normalize("Microsoft Corporation") == "microsoft"
    assert resolver.normalize("Stability AI Ltd.") == "stability ai"

def test_resolve_exact_predefined():
    resolver = EntityResolver()
    canonical, record = resolver.resolve("Google LLC", "Company", "Test")
    assert canonical == "Google"
    assert record.confidence_score >= 95.0

def test_resolve_fuzzy_matching():
    resolver = EntityResolver(threshold=80.0)
    canonical, record = resolver.resolve("Anthropic AI Labs", "Company", "Test")
    # Should match Anthropic
    assert "Anthropic" in canonical

def test_audit_log_fields():
    resolver = EntityResolver()
    _, record = resolver.resolve("Cohere Inc", "Startup", "GitHub")
    assert record.raw_name == "Cohere Inc"
    assert record.canonical_name == "Cohere"
    assert record.entity_type == "Startup"
    assert record.source == "GitHub"
    assert 0.0 <= record.confidence_score <= 100.0
    assert record.resolution_method in ["ExactRegistry", "RuleNormalized", "RapidFuzzMatch", "NewCanonical"]

