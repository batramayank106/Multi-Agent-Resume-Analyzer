import logging
import time
from datetime import datetime
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)


MODEL_REGISTRY = {
    "Qwen2.5 Instruct": {
        "id": "Qwen/Qwen2.5-7B-Instruct",
        "provider": "huggingface",
        "context_length": 32768,
        "cost_per_1k_input": 0.0001,
        "cost_per_1k_output": 0.0002,
    },
    "Qwen2.5 Coder": {
        "id": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "provider": "huggingface",
        "context_length": 16384,
        "cost_per_1k_input": 0.0001,
        "cost_per_1k_output": 0.0002,
    },
    "DeepSeek-R1 Distill": {
        "id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        "provider": "huggingface",
        "context_length": 16384,
        "cost_per_1k_input": 0.0001,
        "cost_per_1k_output": 0.0002,
    },
    "Llama 3.1 Instruct": {
        "id": "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "provider": "huggingface",
        "context_length": 32768,
        "cost_per_1k_input": 0.0001,
        "cost_per_1k_output": 0.0002,
    },
    "Qwen2.5 72B": {
        "id": "Qwen/Qwen2.5-72B-Instruct",
        "provider": "huggingface",
        "context_length": 32768,
        "cost_per_1k_input": 0.0002,
        "cost_per_1k_output": 0.0004,
    },
}

DEFAULT_MODEL = "Qwen2.5 Instruct"
FALLBACK_MODEL = "Llama 3.1 Instruct"
MAX_RETRIES = 3
BASE_RETRY_DELAY = 2.0


class LLMManager:
    _instance: Optional["LLMManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if settings.groq_api_key:
            self.current_model = f"Groq ({settings.groq_default_model})"
        else:
            self.current_model = DEFAULT_MODEL
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cost = 0.0
        self._api_calls = 0
        self._failed_calls = 0
        self._last_used: Optional[datetime] = None
        self._client = None
        self._ollama_manager = None

    @property
    def available_models(self) -> list[str]:
        return list(MODEL_REGISTRY.keys())

    @property
    def model_info(self) -> dict:
        return MODEL_REGISTRY.get(self.current_model, {})

    def switch_model(self, model_name: str) -> bool:
        if model_name in MODEL_REGISTRY:
            self.current_model = model_name
            logger.info(f"Switched to model: {model_name}")
            return True
        logger.warning(f"Unknown model: {model_name}")
        return False

    def get_model_id(self, model_name: Optional[str] = None) -> str:
        name = model_name or self.current_model
        info = MODEL_REGISTRY.get(name, {})
        return info.get("id", MODEL_REGISTRY[DEFAULT_MODEL]["id"])

    def _get_client(self):
        if self._client is None:
            from huggingface_hub import InferenceClient
            self._client = InferenceClient(api_key=settings.hf_api_key)
        return self._client

    def _get_ollama_manager(self):
        if self._ollama_manager is None:
            from services.ollama_manager import ollama_manager as om
            self._ollama_manager = om
        return self._ollama_manager

    def _try_groq(self, messages, temperature, max_tokens) -> dict:
        try:
            import httpx
            groq_model = settings.groq_default_model
            logger.info(f"Trying Groq with model {groq_model}")
            response = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": groq_model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()
            output_text = data["choices"][0]["message"]["content"] or ""

            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", self._estimate_tokens(" ".join(m["content"] for m in messages if isinstance(m.get("content"), str))))
            output_tokens = usage.get("completion_tokens", self._estimate_tokens(output_text))

            self._total_input_tokens += input_tokens
            self._total_output_tokens += output_tokens
            self._api_calls += 1
            self._last_used = datetime.now()
            self.current_model = f"Groq ({groq_model})"

            return {
                "content": output_text,
                "model": f"groq/{groq_model}",
                "model_id": groq_model,
                "provider": "groq",
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                    "estimated_cost": 0.0,
                },
            }
        except Exception as e:
            logger.warning(f"Groq API error: {e}")
            return {"provider": None, "error": str(e)}

    def _is_quota_error(self, error_str: str) -> bool:
        return "402" in error_str or "Payment Required" in error_str or "credits" in error_str.lower()

    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def chat(
        self,
        messages: list[dict],
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> dict:
        # 1. Try Groq first if API key is set
        if settings.groq_api_key:
            groq_result = self._try_groq(messages, temperature, max_tokens)
            if groq_result and groq_result.get("provider") == "groq":
                return groq_result

        # 2. Try Hugging Face Inference API
        if settings.hf_api_key:
            model_id = self.get_model_id(model_name)
            last_error = None

            for attempt in range(MAX_RETRIES):
                try:
                    client = self._get_client()
                    result = client.chat.completions.create(
                        model=model_id,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )

                    output_text = result.choices[0].message.content or ""
                    input_text = " ".join(m["content"] for m in messages)
                    input_tokens = self._estimate_tokens(input_text)
                    output_tokens = self._estimate_tokens(output_text)

                    self._total_input_tokens += input_tokens
                    self._total_output_tokens += output_tokens
                    self._api_calls += 1
                    self._last_used = datetime.now()

                    model_info = MODEL_REGISTRY.get(model_name or self.current_model, {})
                    cost = (
                        input_tokens / 1000 * model_info.get("cost_per_1k_input", 0)
                        + output_tokens / 1000 * model_info.get("cost_per_1k_output", 0)
                    )
                    self._total_cost += cost

                    return {
                        "content": output_text,
                        "model": model_name or self.current_model,
                        "model_id": model_id,
                        "usage": {
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "total_tokens": input_tokens + output_tokens,
                            "estimated_cost": round(cost, 6),
                        },
                    }

                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"HF API error (attempt {attempt + 1}): {e}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(BASE_RETRY_DELAY * (2 ** attempt))

            self._failed_calls += 1

            if model_name != FALLBACK_MODEL:
                logger.warning(f"Primary model failed, trying fallback: {FALLBACK_MODEL}")
                return self.chat(messages, model_name=FALLBACK_MODEL, temperature=temperature, max_tokens=max_tokens)

        # 3. Try Ollama as last resort (only if prefer_ollama is true)
        if settings.prefer_ollama:
            ollama_result = self._try_ollama(messages, temperature, max_tokens,
                                             fallback_reason=last_error if settings.hf_api_key else "Groq + HF unavailable")
            if ollama_result.get("provider") == "ollama":
                return ollama_result

        return {
            "error": last_error or "Groq + HF unavailable",
            "content": f"LLM call failed. Set GROQ_API_KEY or HF_API_KEY for cloud inference, or install Ollama for local inference.",
            "model": model_name or self.current_model,
            "usage": {},
        }

    def _try_ollama(self, messages, temperature, max_tokens, fallback_reason=None) -> dict:
        if not settings.prefer_ollama:
            return {"error": "Ollama disabled (prefer_ollama=false)", "model": "fallback", "usage": {}}
        om = self._get_ollama_manager()
        if om.is_available():
            logger.info("Trying Ollama fallback")
            result = om.chat(messages, temperature=temperature, max_tokens=max_tokens)
            if result:
                self._api_calls += 1
                self._last_used = datetime.now()
                return result

        return {
            "error": fallback_reason or "LLM unavailable",
            "content": f"LLM call failed. {'HF quota exhausted. ' if fallback_reason else ''}"
                        "Set HF_API_KEY for cloud inference or install Ollama for local inference.",
            "model": "fallback",
            "usage": {},
        }

    def get_stats(self) -> dict:
        return {
            "current_model": self.current_model,
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_tokens": self._total_input_tokens + self._total_output_tokens,
            "total_cost": round(self._total_cost, 6),
            "api_calls": self._api_calls,
            "failed_calls": self._failed_calls,
            "last_used": self._last_used.isoformat() if self._last_used else None,
        }


llm_manager = LLMManager()
