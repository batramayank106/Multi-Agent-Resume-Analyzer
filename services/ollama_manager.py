import json
import logging
import urllib.request
import urllib.error
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)

OLLAMA_MODELS = {
    "qwen2.5:3b": {
        "id": "qwen2.5:3b",
        "context_length": 32768,
    },
    "deepseek-r1:1.5b": {
        "id": "deepseek-r1:1.5b",
        "context_length": 16384,
    },
    "phi-4-mini": {
        "id": "phi-4-mini",
        "context_length": 16384,
    },
    "llama-3.2:3b": {
        "id": "llama-3.2:3b",
        "context_length": 16384,
    },
}


class OllamaManager:
    def __init__(self):
        self.base_url = settings.ollama_base_url or "http://localhost:11434"
        self._available = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                models = [m["name"] for m in data.get("models", [])]
                configured = settings.ollama_model
                if configured and configured not in models:
                    logger.warning(
                        f"Configured Ollama model '{configured}' not found. "
                        f"Available: {models}. Run: ollama pull {configured}"
                    )
                self._available = True
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            self._available = False
        return self._available

    def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Optional[dict]:
        model_name = model or settings.ollama_model or "qwen2.5:3b"

        options = {
            "temperature": temperature,
            "num_predict": max_tokens,
        }
        if settings.ollama_gpu_layers > 0:
            options["num_gpu"] = settings.ollama_gpu_layers

        body = json.dumps({
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": options,
        }).encode()

        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/chat",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode())

            content = result.get("message", {}).get("content", "")
            return {
                "content": content,
                "model": model_name,
                "provider": "ollama",
                "usage": {
                    "total_duration": result.get("total_duration", 0),
                },
            }
        except Exception as e:
            logger.warning(f"Ollama call failed: {e}")
            return None


ollama_manager = OllamaManager()
