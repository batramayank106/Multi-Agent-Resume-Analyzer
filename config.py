from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

from dotenv import load_dotenv

# Load .env file explicitly with absolute path (not relative to CWD)
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path, override=True)


class Settings(BaseSettings):
    app_name: str = "CV Chacha 😎"
    app_version: str = "1.0.0"
    debug: bool = True
    log_level: str = "INFO"

    hf_api_key: Optional[str] = None
    hf_default_model: str = "Qwen/Qwen2.5-7B-Instruct"

    groq_api_key: Optional[str] = None
    groq_default_model: str = "llama-3.3-70b-versatile"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"
    ollama_gpu_layers: int = 999
    prefer_ollama: bool = True

    database_url: str = "sqlite+aiosqlite:///./cv_chacha.db"

    chroma_persist_dir: str = "./chroma_db"

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_fallback_model: str = "all-MiniLM-L6-v2"

    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 30
    jwt_refresh_expire_days: int = 7

    super_admin_email: str = "admin@example.com"
    super_admin_password: str = "ChangeMe123!"

    encryption_key: Optional[str] = None

    class Config:
        env_file_encoding = "utf-8"


settings = Settings()
