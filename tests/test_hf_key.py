"""Proper pytest: verify HF API key loads and LLM manager can make a call."""

import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from config import settings
from services.llm_manager import llm_manager


pytestmark = pytest.mark.skipif(
    not settings.hf_api_key,
    reason="HF_API_KEY not configured",
)


def test_hf_key_loaded():
    assert settings.hf_api_key is not None
    assert len(settings.hf_api_key) > 0


def test_llm_manager_initialized():
    assert llm_manager is not None
    assert llm_manager.current_model is not None


def test_hf_chat_returns_valid_response():
    result = llm_manager.chat(
        [{"role": "user", "content": "Reply with just: OK"}],
        max_tokens=10,
    )
    assert "error" not in result, result.get("error")
    assert "content" in result
    assert "model" in result
