"""Tests for LLM Manager fallback chain — Groq, HF API, Ollama, and graceful degradation."""

import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from config import settings
from services.llm_manager import LLMManager, MODEL_REGISTRY, DEFAULT_MODEL, FALLBACK_MODEL

has_any_key = settings.groq_api_key is not None or settings.hf_api_key is not None


class TestLLMManagerInit:
    def test_singleton(self):
        m1 = LLMManager()
        m2 = LLMManager()
        assert m1 is m2

    def test_initial_stats(self):
        m = LLMManager()
        stats = m.get_stats()
        assert "current_model" in stats
        assert "api_calls" in stats
        assert "failed_calls" in stats
        assert "total_tokens" in stats
        assert stats["api_calls"] >= 0
        assert stats["failed_calls"] >= 0

    def test_available_models(self):
        m = LLMManager()
        models = m.available_models
        assert len(models) > 0
        assert DEFAULT_MODEL in models
        assert FALLBACK_MODEL in models


class TestModelRegistry:
    def test_registry_has_required_keys(self):
        for name, info in MODEL_REGISTRY.items():
            assert "id" in info
            assert "provider" in info
            assert "context_length" in info

    def test_get_model_id_returns_default(self):
        m = LLMManager()
        model_id = m.get_model_id(None)
        assert isinstance(model_id, str)
        assert len(model_id) > 0

    def test_switch_model_valid(self):
        m = LLMManager()
        assert m.switch_model(DEFAULT_MODEL) is True

    def test_switch_model_invalid(self):
        m = LLMManager()
        assert m.switch_model("non-existent-model") is False


class TestFallbackChain:
    def test_chat_returns_dict_on_failure(self):
        m = LLMManager()
        result = m.chat([{"role": "user", "content": "Hello"}])
        assert isinstance(result, dict)
        assert "content" in result
        assert "model" in result
        assert "usage" in result

    @pytest.mark.skipif(has_any_key or settings.prefer_ollama, reason="LLM keys or Ollama enabled")
    def test_fallback_returns_error_without_keys(self):
        m = LLMManager()
        result = m.chat([{"role": "user", "content": "Hello"}])
        assert "error" in result
        assert result.get("error") is not None

    def test_estimate_tokens(self):
        m = LLMManager()
        assert m._estimate_tokens("hello world") == 2
        assert m._estimate_tokens("") == 0
        assert m._estimate_tokens("a" * 100) == 25

    def test_is_quota_error(self):
        m = LLMManager()
        assert m._is_quota_error("402 Payment Required")
        assert m._is_quota_error("credits exhausted")
        assert not m._is_quota_error("rate limit exceeded")


class TestGroqFallback:
    @pytest.mark.skipif(settings.groq_api_key is not None, reason="Groq key is set; test is for missing-key path")
    def test_try_groq_returns_dict_without_key(self):
        m = LLMManager()
        result = m._try_groq(
            [{"role": "user", "content": "Hi"}],
            temperature=0.7,
            max_tokens=50,
        )
        assert isinstance(result, dict)
        assert result.get("provider") is None or "error" in result

    @pytest.mark.skipif(settings.groq_api_key is not None, reason="Groq key is set; test is for missing-key path")
    def test_try_groq_has_correct_structure_on_error(self):
        m = LLMManager()
        result = m._try_groq(
            [{"role": "user", "content": "Hi"}],
            temperature=0.7,
            max_tokens=50,
        )
        assert "provider" in result
        assert "error" in result


class TestOllamaFallback:
    def test_try_ollama_returns_dict(self):
        m = LLMManager()
        result = m._try_ollama(
            [{"role": "user", "content": "Hi"}],
            temperature=0.7,
            max_tokens=50,
            fallback_reason="test",
        )
        assert isinstance(result, dict)
        assert "model" in result
        assert "usage" in result

    def test_try_ollama_disabled_when_prefer_false(self):
        original = settings.prefer_ollama
        try:
            settings.prefer_ollama = False
            m = LLMManager()
            result = m._try_ollama(
                [{"role": "user", "content": "Hi"}],
                temperature=0.7,
                max_tokens=50,
            )
            assert "error" in result
            assert "disabled" in result.get("error", "")
        finally:
            settings.prefer_ollama = original


class TestStats:
    def test_get_stats_returns_all_keys(self):
        m = LLMManager()
        stats = m.get_stats()
        expected_keys = {
            "current_model", "total_input_tokens", "total_output_tokens",
            "total_tokens", "total_cost", "api_calls", "failed_calls",
            "last_used",
        }
        assert expected_keys.issubset(stats.keys())

    def test_stats_values_are_correct_types(self):
        m = LLMManager()
        stats = m.get_stats()
        assert isinstance(stats["current_model"], str)
        assert isinstance(stats["api_calls"], int)
        assert isinstance(stats["failed_calls"], int)
        assert isinstance(stats["total_tokens"], int)
        assert isinstance(stats["total_cost"], float)
