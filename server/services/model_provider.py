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
    async def list_ollama_models() -> Dict:
        """
        List all available Ollama models with connection status
        Returns dict with 'models' list and 'status' string
        """
        try:
            config = ModelProvider.get_ollama_config()
            async with httpx.AsyncClient(timeout=5) as client:
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

                return {
                    "models": models,
                    "status": "connected",
                    "message": f"Found {len(models)} Ollama models"
                }
        except httpx.ConnectError as e:
            print(f"Ollama connection error (is ollama serve running?): {e}")
            return {
                "models": [],
                "status": "disconnected",
                "message": "Ollama is not running. Start with 'ollama serve'"
            }
        except httpx.TimeoutException as e:
            print(f"Ollama timeout: {e}")
            return {
                "models": [],
                "status": "timeout",
                "message": "Ollama connection timed out"
            }
        except Exception as e:
            print(f"Failed to list Ollama models: {e}")
            return {
                "models": [],
                "status": "error",
                "message": str(e)
            }

    @staticmethod
    def chat_completion_sync(
        messages: List[Dict],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        timeout: int = 60
    ) -> str:
        """
        SYNC Unified chat completion interface
        Automatically routes to OpenAI or Ollama based on model name

        Args:
            timeout: Timeout in seconds (default 60s)
        """

        print(f"[ModelProvider] Routing model '{model}' to provider (timeout={timeout}s)...")

        # Determine provider based on model name
        # OpenAI models: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo, etc.
        # BUT NOT: gpt-oss, gpt-neox, etc. (these are local Ollama models)
        openai_models = ["gpt-5", "gpt-5-mini", "gpt-5-nano", "o1", "o1-preview", "gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-3.5", "gpt-4-turbo"]

        # Check if it's an actual OpenAI model
        is_openai = any(model.startswith(prefix) for prefix in openai_models)

        # Special case: gpt-oss and gpt-neox are Ollama models
        if "gpt-oss" in model or "gpt-neox" in model:
            is_openai = False

        if is_openai:
            print(f"[ModelProvider] Sending '{model}' to OpenAI")
            return ModelProvider._openai_completion_sync(messages, model, temperature, max_tokens, timeout)
        else:
            print(f"[ModelProvider] Sending '{model}' to Ollama")
            return ModelProvider._ollama_completion_sync(messages, model, temperature, max_tokens, timeout)

    @staticmethod
    async def chat_completion(
        messages: List[Dict],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        ASYNC Unified chat completion interface
        Automatically routes to OpenAI or Ollama based on model name
        """
        
        print(f"[ModelProvider] Async routing model '{model}' to provider...")

        # Determine provider based on model name
        # OpenAI models: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo, etc.
        # BUT NOT: gpt-oss, gpt-neox, etc. (these are local Ollama models)
        openai_models = ["gpt-5", "gpt-5-mini", "gpt-5-nano", "o1", "o1-preview", "gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-3.5", "gpt-4-turbo"]
        
        # Check if it's an actual OpenAI model
        is_openai = any(model.startswith(prefix) for prefix in openai_models)
        
        # Special case: gpt-oss and gpt-neox are Ollama models
        if "gpt-oss" in model or "gpt-neox" in model:
            is_openai = False
        
        if is_openai:
            print(f"[ModelProvider] Async sending '{model}' to OpenAI")
            return await ModelProvider._openai_completion(messages, model, temperature, max_tokens)
        else:
            print(f"[ModelProvider] Async sending '{model}' to Ollama")
            return await ModelProvider._ollama_completion(messages, model, temperature, max_tokens)

    @staticmethod
    def _openai_completion_sync(
        messages: List[Dict],
        model: str,
        temperature: float,
        max_tokens: int,
        timeout: int = 60
    ) -> str:
        """OpenAI completion (SYNC) - GPT-5 and GPT-4 both use chat/completions"""
        config = ModelProvider.get_openai_config()

        if not config["api_key"]:
            raise ValueError("OpenAI API key not configured")

        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
        }

        if config["project_id"]:
            headers["OpenAI-Project"] = config["project_id"]

        # Both GPT-4 and GPT-5 support /chat/completions
        # Use max_completion_tokens for GPT-5 models
        payload = {
            "model": model,
            "messages": messages,
        }

        # GPT-5 models have specific requirements
        if model.startswith("gpt-5") or model.startswith("o1") or model.startswith("o3"):
            payload["max_completion_tokens"] = max_tokens
            # GPT-5 only supports temperature=1 (default), so omit it
            # If temperature is not 1, we'll just use the default
        else:
            payload["max_tokens"] = max_tokens
            payload["temperature"] = temperature

        with httpx.Client(base_url=config["base_url"], timeout=timeout) as client:
            try:
                response = client.post("/chat/completions", headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as e:
                print(f"[OpenAI API Error] Status: {e.response.status_code}")
                print(f"[OpenAI API Error] Response: {e.response.text}")
                print(f"[OpenAI API Error] Payload sent: {payload}")
                raise

        return data["choices"][0]["message"]["content"].strip()

    @staticmethod
    async def _openai_completion(
        messages: List[Dict],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """OpenAI completion (ASYNC) - GPT-5 and GPT-4 both use chat/completions"""
        config = ModelProvider.get_openai_config()

        if not config["api_key"]:
            raise ValueError("OpenAI API key not configured")

        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
        }

        if config["project_id"]:
            headers["OpenAI-Project"] = config["project_id"]

        # Both GPT-4 and GPT-5 support /chat/completions
        # Use max_completion_tokens for GPT-5 models
        payload = {
            "model": model,
            "messages": messages,
        }
        
        # GPT-5 models have specific requirements
        if model.startswith("gpt-5") or model.startswith("o1") or model.startswith("o3"):
            payload["max_completion_tokens"] = max_tokens
            # GPT-5 only supports temperature=1 (default), so omit it
            # If temperature is not 1, we'll just use the default
        else:
            payload["max_tokens"] = max_tokens
            payload["temperature"] = temperature

        async with httpx.AsyncClient(base_url=config["base_url"], timeout=60) as client:
            try:
                response = await client.post("/chat/completions", headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as e:
                print(f"[OpenAI API Error] Status: {e.response.status_code}")
                print(f"[OpenAI API Error] Response: {e.response.text}")
                print(f"[OpenAI API Error] Payload sent: {payload}")
                raise

        return data["choices"][0]["message"]["content"].strip()

    @staticmethod
    def _ollama_completion_sync(
        messages: List[Dict],
        model: str,
        temperature: float,
        max_tokens: int,
        timeout: int = 120
    ) -> str:
        """Ollama completion (SYNC)"""
        config = ModelProvider.get_ollama_config()

        # Make a copy of messages to avoid modifying the original
        messages = messages.copy()

        # For OSS models that output thinking, add a system message to suppress it
        if "oss" in model.lower() or "gpt-oss" in model.lower():
            # Check if there's already a system message
            has_system = any(msg.get("role") == "system" for msg in messages)

            if has_system:
                # Append to existing system message
                for i, msg in enumerate(messages):
                    if msg.get("role") == "system":
                        messages[i] = {
                            **msg,
                            "content": msg["content"] + "\n\nIMPORTANT: Provide ONLY the final answer without showing your thinking process, internal monologue, or reasoning steps. Be direct and concise."
                        }
                        break
            else:
                # Add new system message at the beginning
                messages.insert(0, {
                    "role": "system",
                    "content": "IMPORTANT: Provide ONLY the final answer without showing your thinking process, internal monologue, or reasoning steps. Be direct and concise."
                })

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }

        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                f"{config['base_url']}/api/chat",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        return data["message"]["content"].strip()

    @staticmethod
    async def _ollama_completion(
        messages: List[Dict],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Ollama completion (ASYNC)"""
        config = ModelProvider.get_ollama_config()

        # For OSS models that output thinking, add a system message to suppress it
        if "oss" in model.lower() or "gpt-oss" in model.lower():
            # Check if there's already a system message
            has_system = any(msg.get("role") == "system" for msg in messages)
            
            if has_system:
                # Append to existing system message
                for msg in messages:
                    if msg.get("role") == "system":
                        msg["content"] = msg["content"] + "\n\nIMPORTANT: Provide ONLY the final answer without showing your thinking process, internal monologue, or reasoning steps. Be direct and concise."
                        break
            else:
                # Add new system message at the beginning
                messages = [
                    {"role": "system", "content": "IMPORTANT: Provide ONLY the final answer without showing your thinking process, internal monologue, or reasoning steps. Be direct and concise."},
                    *messages
                ]

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
