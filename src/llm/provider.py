import json
import re
import aiohttp
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from src.utils.logging import logger
from src.utils.retry import async_retry

class LLMProvider(ABC):
    name: str

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the provider has credentials configured."""
        pass

    @abstractmethod
    async def extract_structured(self, prompt: str, system_prompt: str) -> Optional[Dict[str, Any]]:
        """Extracts structured JSON data from text using the LLM."""
        pass

class GeminiProvider(LLMProvider):
    name = "Gemini"

    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key
        self.endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    @async_retry(max_retries=2, base_delay=1.5, backoff_factor=2.0)
    async def extract_structured(self, prompt: str, system_prompt: str) -> Optional[Dict[str, Any]]:
        if not self.is_available():
            return None

        url = f"{self.endpoint}?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{prompt}"}]}
            ],
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json"
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=25)) as resp:
                if resp.status == 429:
                    logger.warning("Gemini API rate limit (429) hit.")
                    raise aiohttp.ClientResponseError(resp.request_info, resp.history, status=429, message="Rate limited")
                if resp.status != 200:
                    text = await resp.text()
                    logger.warning(f"Gemini API returned status {resp.status}: {text[:200]}")
                    return None

                data = await resp.json()
                try:
                    candidates = data.get("candidates", [])
                    if not candidates:
                        return None
                    content_text = candidates[0]["content"]["parts"][0]["text"]
                    return json.loads(content_text)
                except Exception as e:
                    logger.debug(f"Gemini JSON parse failed: {e}")
                    return None

class GroqProvider(LLMProvider):
    name = "Groq"

    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    @async_retry(max_retries=2, base_delay=1.5, backoff_factor=2.0)
    async def extract_structured(self, prompt: str, system_prompt: str) -> Optional[Dict[str, Any]]:
        if not self.is_available():
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
            "max_tokens": 1000
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.endpoint, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=25)) as resp:
                if resp.status == 429:
                    logger.warning("Groq API rate limit (429) hit.")
                    raise aiohttp.ClientResponseError(resp.request_info, resp.history, status=429, message="Rate limited")
                if resp.status != 200:
                    text = await resp.text()
                    logger.warning(f"Groq API returned status {resp.status}: {text[:200]}")
                    return None

                data = await resp.json()
                try:
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
                except Exception as e:
                    logger.debug(f"Groq JSON parse failed: {e}")
                    return None

class DeepSeekProvider(LLMProvider):
    name = "DeepSeek"

    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key
        self.endpoint = "https://api.deepseek.com/chat/completions"

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    @async_retry(max_retries=2, base_delay=1.5, backoff_factor=2.0)
    async def extract_structured(self, prompt: str, system_prompt: str) -> Optional[Dict[str, Any]]:
        if not self.is_available():
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
            "max_tokens": 1000
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.endpoint, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=25)) as resp:
                if resp.status == 429:
                    logger.warning("DeepSeek API rate limit (429) hit.")
                    raise aiohttp.ClientResponseError(resp.request_info, resp.history, status=429, message="Rate limited")
                if resp.status != 200:
                    text = await resp.text()
                    logger.warning(f"DeepSeek API returned status {resp.status}: {text[:200]}")
                    return None

                data = await resp.json()
                try:
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
                except Exception as e:
                    logger.debug(f"DeepSeek JSON parse failed: {e}")
                    return None

