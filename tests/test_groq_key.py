"""Proper pytest: verify Groq API key loads and Groq fallback works."""

import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from config import settings
from services.llm_manager import LLMManager


pytestmark = pytest.mark.skipif(
    not settings.groq_api_key,
    reason="GROQ_API_KEY not configured",
)


def test_groq_key_loaded():
    assert settings.groq_api_key is not None
    assert len(settings.groq_api_key) > 0


def test_groq_chat_via_llm_manager():
    m = LLMManager()
    result = m._try_groq(
        [{"role": "user", "content": "Reply with just: OK"}],
        temperature=0.7,
        max_tokens=10,
    )
    assert "error" not in result, result.get("error")
    assert result.get("provider") == "groq"
    assert "content" in result
