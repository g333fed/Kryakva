from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class OllamaProvider:
    """Thin Ollama Chat API client."""

    def __init__(self, base_url: str, model: str, temperature: float = 0.6, max_tokens: int = 512) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def ping(self, timeout: int = 3) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=timeout)
            logger.info("Ollama ping status=%s", response.status_code)
            return response.status_code == 200
        except Exception:
            logger.exception("Ollama ping failed")
            return False

    def list_models(self, timeout: int = 5) -> list[str]:
        response = requests.get(f"{self.base_url}/api/tags", timeout=timeout)
        response.raise_for_status()
        data = response.json() or {}
        return [m.get("name") for m in (data.get("models") or []) if m.get("name")]

    def chat(self, messages: list[dict[str, str]], timeout: int = 120) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.temperature, "num_predict": self.max_tokens},
        }
        logger.info("LLM request model=%s", self.model)
        response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return (data.get("message") or {}).get("content", "")
