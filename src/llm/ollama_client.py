"""LLM Client - Supports both Ollama (local) and Groq (cloud)."""

import requests
from typing import Optional


class OllamaClient:
    """Client for local Ollama LLM."""

    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3.1:8b"):
        self.host = host.rstrip("/")
        self.model = model
        self.api_url = f"{self.host}/api"

    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 temperature: float = 0.7, max_tokens: int = 4096) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(f"{self.api_url}/generate", json=payload, timeout=300)
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Cannot connect to Ollama. Start it with: ollama serve")
        except Exception as e:
            raise Exception(f"Ollama error: {e}")

    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(m.get("name", "").startswith(self.model) for m in models)
            return False
        except Exception:
            return False

    def list_models(self) -> list:
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            response.raise_for_status()
            return [m.get("name", "") for m in response.json().get("models", [])]
        except Exception:
            return []


class GroqClient:
    """Client for Groq cloud API (free tier)."""

    def __init__(self, api_key: str, model: str = "llama-3.1-70b-versatile"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 temperature: float = 0.7, max_tokens: int = 4096) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Cannot connect to Groq API. Check your internet.")
        except Exception as e:
            raise Exception(f"Groq error: {e}")

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=10)
            return response.status_code == 200
        except Exception:
            return False
