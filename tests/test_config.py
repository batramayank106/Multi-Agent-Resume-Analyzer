import os
import pytest
from config import Settings, settings

class TestSettings:
    def test_default_values_after_env_override(self):
        """Defaults not overridden by .env should match."""
        s = Settings()
        assert s.app_name == "CV Chacha 😎"
        assert s.app_version == "1.0.0"
        assert s.debug is True
        assert s.hf_default_model == "Qwen/Qwen2.5-7B-Instruct"
        assert s.database_url == "sqlite+aiosqlite:///./cv_chacha.db"
        assert s.chroma_persist_dir == "./chroma_db"
        assert s.embedding_model == "BAAI/bge-small-en-v1.5"
        # Sensitive fields default to None when .env is not configured
        assert s.hf_api_key is None
        assert s.groq_api_key is None
        assert s.jwt_secret is None
        assert s.encryption_key is None

    def test_singleton_settings(self):
        assert settings.app_name == "CV Chacha 😎"
        assert settings.app_version == "1.0.0"

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("APP_NAME", "Test App")
        monkeypatch.setenv("DEBUG", "false")
        s = Settings()
        assert s.app_name == "Test App"
        assert s.debug is False
