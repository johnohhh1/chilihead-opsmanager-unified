"""
Model provider abstraction layer
Supports both OpenAI and Ollama with unified interface
"""

import os
import httpx
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class ModelProvider:
    """Unified interface for different AI model providers"""

    @staticmethod
    def get_openai_config():
        """Get OpenAI configuration"""
        return {
            "provider": "openai",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "model": "gpt-4o",
            "project_id": os.getenv("OPENAI_PROJECT_ID")
        }

    @staticmethod
    def get_ollama_config():
        """Get Ollama configuration"""
        return {
            "provider": "ollama",
            "base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            "api_key": None  # Ollama doesn't need API key
        }

    @staticmethod
    async def list_ollama_models() -> List[Dict]:
        """List all available Ollama models"""
        try:
            config = ModelProvider.get_ollama_config()
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{config['base_url']}/api/tags")
                response.raise_for_status()
                data = response.json()

                # Format models for frontend
                models = []
                for model in data.get("models", []):
                    models.append({
                        "id": model["name"],
                        "name": model["name"],
                        "size": model.get("size", 0),
                        "modified": model.get("modified_at", ""),
                        "provider": "ollama"
                    })

                return models
        except Exception as e:
            print(f"Failed to list Ollama models: {e}")
            return []

    @staticmethod
    async def chat_completion(
        messages: List[Dict],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Unified chat completion interface
        Automatically routes to OpenAI or Ollama based on model name
        """

        # Determine provider based on model name
        if model.startswith("gpt-") or model == "gpt-4o":
            return await ModelProvider._openai_completion(messages, model, temperature, max_tokens)
        else:
            return await ModelProvider._ollama_completion(messages, model, temperature, max_tokens)

    @staticmethod
    async def _openai_completion(
        messages: List[Dict],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """OpenAI completion"""
        config = ModelProvider.get_openai_config()

        if not config["api_key"]:
            raise ValueError("OpenAI API key not configured")

        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
        }

        if config["project_id"]:
            headers["OpenAI-Project"] = config["project_id"]

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        async with httpx.AsyncClient(base_url=config["base_url"], timeout=60) as client:
            response = await client.post("/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        return data["choices"][0]["message"]["content"].strip()

    @staticmethod
    async def _ollama_completion(
        messages: List[Dict],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Ollama completion"""
        config = ModelProvider.get_ollama_config()

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{config['base_url']}/api/chat",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        return data["message"]["content"].strip()
