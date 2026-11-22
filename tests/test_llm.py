import pytest
from src.llm.chunker import TextChunker
from src.llm.orchestrator import LLMOrchestrator

def test_text_chunker_basic():
    text = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
    chunks = TextChunker.chunk_text(text, chunk_size=50, chunk_overlap=10)
    assert len(chunks) >= 1
    assert "Paragraph 1" in chunks[0]

def test_text_chunker_large_text():
    large_text = "\n\n".join([f"This is section {i} describing AI technology developments." for i in range(50)])
    chunks = TextChunker.chunk_text(large_text, chunk_size=200, chunk_overlap=30)
    assert len(chunks) > 1

def test_llm_orchestrator_initialization():
    orchestrator = LLMOrchestrator()
    # Check priority order
    provider_names = [p.name for p in orchestrator.providers]
    assert provider_names == ["Gemini", "Groq", "DeepSeek"]

