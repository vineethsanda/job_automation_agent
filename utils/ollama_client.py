"""Ollama LLM client for local inference with structured output."""

import json
import httpx
from typing import Dict, Any, Optional
from loguru import logger


class OllamaClient:
    """Client for Ollama API with structured JSON output."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama2:latest",
        timeout: float = 300.0,
    ):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        json_format: bool = False,
    ) -> str:
        """Generate text using Ollama (using /api/chat endpoint)."""
        try:
            # Use new /api/chat endpoint (compatible with all Ollama versions)
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system} if system else None,
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "keep_alive": "5m",
            }
            
            # Remove None values
            payload["messages"] = [m for m in payload["messages"] if m is not None]

            if json_format:
                payload["format"] = "json"

            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()

            result = response.json()
            text = result.get("message", {}).get("content", "").strip()
            logger.debug(f"Generated text (length: {len(text)})")
            return text

        except httpx.HTTPError as e:
            logger.error(f"Ollama API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Generation error: {e}")
            raise

    async def generate_structured(
        self,
        prompt: str,
        system: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate structured JSON output from Ollama."""
        text = await self.generate(prompt, system=system, json_format=True)

        try:
            # Try to extract JSON from response
            if "{" in text:
                json_start = text.find("{")
                json_end = text.rfind("}") + 1
                json_str = text[json_start:json_end]
                return json.loads(json_str)
            else:
                logger.warning("No JSON found in response")
                return {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Raw response: {text}")
            return {}

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
