import json
import logging
import re
from typing import Any, Optional

from services.llm_manager import llm_manager
from services.prompt_manager import prompt_manager
from config import settings

logger = logging.getLogger(__name__)


class BaseAgent:

    def __init__(self, name: str):
        self.name = name

    def run(self, state: dict) -> dict:
        raise NotImplementedError

    def _llm_chat(self, messages: list[dict], temperature: float = 0.3) -> dict:
        return llm_manager.chat(
            messages=messages,
            temperature=temperature,
        )

    def _safe_llm_call(self, messages: list[dict], temperature: float = 0.3) -> Optional[dict]:
        result = self._llm_chat(messages, temperature=temperature)
        if "error" in result and result.get("error"):
            logger.warning(f"Agent '{self.name}' LLM error: {result['error']}")
            return None
        if "content" not in result or not result.get("content"):
            logger.warning(f"Agent '{self.name}' LLM returned empty content")
            return None
        return result

    @staticmethod
    def _extract_json(text: str) -> Optional[dict]:
        text = re.sub(r'```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```', '', text)
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if not json_match:
            return None
        raw = json_match.group()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        try:
            import json5 as _json5
            return _json5.loads(raw)
        except Exception:
            pass
        try:
            cleaned = re.sub(r',(\s*[}\]])', r'\1', raw)
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        cleaned = re.sub(r"(?<!\\)'(.*?)(?<!\\)'", r'"\1"', raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        cleaned = re.sub(r'(?<!")(\b\w+\b)(?=\s*:)', r'"\1"', cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        return None

    @staticmethod
    def _extract_json_array(text: str) -> Optional[list]:
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if not match:
            return None
        raw = match.group()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        try:
            import json5
            return json5.loads(raw)
        except Exception:
            pass
        cleaned = re.sub(r',\s*\]', ']', raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        return None

    def _log_start(self, **kwargs):
        logger.info(f"Agent '{self.name}' starting with: {kwargs}")

    def _log_end(self, result: Any):
        logger.info(f"Agent '{self.name}' completed")

    def _log_error(self, error: Exception):
        logger.error(f"Agent '{self.name}' error: {error}")
