import pytest
from rag.chunking import ChunkingService, chunking_service
from rag.context_builder import ContextBuilder

class TestChunkingService:
    def test_singleton(self):
        c1 = ChunkingService()
        c2 = ChunkingService()
        assert c1 is c2

    def test_chunk_short_text(self):
        chunks = chunking_service.chunk_text("Hello world")
        assert len(chunks) >= 1
        assert "Hello world" in chunks

    def test_chunk_long_text(self):
        text = "word " * 2000
        chunks = chunking_service.chunk_text(text)
        assert len(chunks) >= 2
        assert all(len(c) > 0 for c in chunks)

    def test_chunk_documents(self):
        texts = ["short text", "another short doc"]
        chunks = chunking_service.chunk_documents(texts)
        assert len(chunks) >= 2

    def test_custom_chunk_size(self):
        chunking_service.set_chunk_size(100, 10)
        text = "word " * 500
        chunks = chunking_service.chunk_text(text)
        assert len(chunks) >= 4

class TestContextBuilder:
    def test_empty_docs_returns_empty(self):
        result = ContextBuilder.build_context([])
        assert result == ""

    def test_single_doc(self):
        docs = ["Hello world"]
        result = ContextBuilder.build_context(docs)
        assert result == "Hello world"

    def test_multiple_docs(self):
        docs = ["Doc one", "Doc two"]
        result = ContextBuilder.build_context(docs)
        assert "Doc one" in result
        assert "Doc two" in result
        assert "---" in result

    def test_max_chars_truncation(self):
        docs = ["a" * 3000, "b" * 3000]
        result = ContextBuilder.build_context(docs, max_chars=1000)
        assert len(result) <= 1000 + 100

    def test_build_context_with_scores(self):
        results = [
            {"content": "Doc A", "rerank_score": 0.95, "distance": 0.1, "metadata": {}},
            {"content": "Doc B", "rerank_score": 0.80, "distance": 0.2, "metadata": {}},
        ]
        result = ContextBuilder.build_context_with_scores(results, include_scores=True)
        assert "0.950" in result
        assert "0.800" in result

    def test_build_context_with_scores_no_scores(self):
        results = [
            {"content": "Doc A", "rerank_score": 0.95, "distance": 0.1, "metadata": {}},
        ]
        result = ContextBuilder.build_context_with_scores(results, include_scores=False)
        assert "0.950" not in result

    def test_format_for_prompt(self):
        result = ContextBuilder.format_for_prompt("Some context", "What is this?")
        assert "Some context" in result
        assert "What is this?" in result
        assert "Context:" in result
