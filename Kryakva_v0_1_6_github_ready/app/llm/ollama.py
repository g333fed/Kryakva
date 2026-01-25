
from __future__ import annotations
import requests
from typing import List, Dict, Any

class OllamaProvider:
    def __init__(self, base_url: str, model: str, temperature: float = 0.6, max_tokens: int = 512):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def ping(self, timeout: int = 3) -> bool:
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=timeout)
            return r.status_code == 200
        except Exception:
            return False

    def list_models(self, timeout: int = 5) -> list[str]:
        r = requests.get(f"{self.base_url}/api/tags", timeout=timeout)
        r.raise_for_status()
        data = r.json() or {}
        models = []
        for m in data.get("models", []) or []:
            name = m.get("name")
            if name:
                models.append(name)
        return models

    def chat(self, messages: List[Dict[str, str]], timeout: int = 120) -> str:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.temperature, "num_predict": self.max_tokens}
        }
        r = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        return (data.get("message", {}) or {}).get("content", "")
