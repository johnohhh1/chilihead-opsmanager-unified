"""
Models API - List available AI models from both OpenAI and Ollama
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict
import os
from dotenv import load_dotenv
from services.model_provider import ModelProvider

load_dotenv()

router = APIRouter()

@router.get("/models/list")
async def list_models():
    """
    List all available models from both OpenAI and Ollama
    Returns a unified list with provider information
    """
    try:
        models_response = {
            "models": [],
            "providers": {
                "openai": {"status": "unknown", "message": ""},
                "anthropic": {"status": "unknown", "message": ""},
                "ollama": {"status": "unknown", "message": ""}
            }
        }

        # Add OpenAI models if configured
        if os.getenv("OPENAI_API_KEY"):
            models_response["models"].extend([
                {
                    "id": "gpt-5",
                    "name": "GPT-5",
                    "provider": "openai",
                    "description": "OpenAI's latest flagship model - released August 7, 2025"
                },
                {
                    "id": "gpt-5-mini",
                    "name": "GPT-5 Mini",
                    "provider": "openai",
                    "description": "Balanced speed and cost version of GPT-5"
                },
                {
                    "id": "gpt-5-nano",
                    "name": "GPT-5 Nano",
                    "provider": "openai",
                    "description": "Lightweight, cost-effective GPT-5"
                },
                {
                    "id": "o1",
                    "name": "o1",
                    "provider": "openai",
                    "description": "OpenAI's advanced reasoning model"
                },
                {
                    "id": "o1-preview",
                    "name": "o1-preview",
                    "provider": "openai",
                    "description": "Preview of o1 reasoning capabilities"
                },
                {
                    "id": "gpt-4o",
                    "name": "GPT-4 Optimized (with Vision)",
                    "provider": "openai",
                    "description": "Most capable GPT-4 model with native vision/image analysis support",
                    "supports_vision": True
                },
                {
                    "id": "gpt-4o-mini",
                    "name": "GPT-4o Mini",
                    "provider": "openai",
                    "description": "Fast and efficient for simple tasks"
                },
                {
                    "id": "gpt-4-turbo",
                    "name": "GPT-4 Turbo",
                    "provider": "openai",
                    "description": "Latest GPT-4 model with vision capabilities",
                    "supports_vision": True
                },
                {
                    "id": "gpt-3.5-turbo",
                    "name": "GPT-3.5 Turbo",
                    "provider": "openai",
                    "description": "Fast, good for most tasks"
                }
            ])
            models_response["providers"]["openai"] = {
                "status": "connected",
                "message": "OpenAI API configured"
            }
        else:
            models_response["providers"]["openai"] = {
                "status": "not_configured",
                "message": "OpenAI API key not found"
            }

        # Add Anthropic Claude models if configured
        if os.getenv("ANTHROPIC_API_KEY"):
            models_response["models"].extend([
                {
                    "id": "claude-sonnet-4-5-20250929",
                    "name": "Claude Sonnet 4.5",
                    "provider": "anthropic",
                    "description": "Best coding model in the world - released Sept 2025"
                },
                {
                    "id": "claude-3-5-sonnet-20241022",
                    "name": "Claude 3.5 Sonnet",
                    "provider": "anthropic",
                    "description": "Previous generation Sonnet model"
                },
                {
                    "id": "claude-3-opus-20240229",
                    "name": "Claude 3 Opus",
                    "provider": "anthropic",
                    "description": "Most powerful Claude 3 model for complex tasks"
                },
                {
                    "id": "claude-3-haiku-20240307",
                    "name": "Claude 3 Haiku",
                    "provider": "anthropic",
                    "description": "Fast and efficient for simple tasks"
                }
            ])
            models_response["providers"]["anthropic"] = {
                "status": "connected",
                "message": "Anthropic API configured"
            }
        else:
            models_response["providers"]["anthropic"] = {
                "status": "not_configured",
                "message": "Anthropic API key not found (set ANTHROPIC_API_KEY in .env)"
            }

        # Get Ollama models
        ollama_result = await ModelProvider.list_ollama_models()
        
        if ollama_result["status"] == "connected":
            models_response["models"].extend(ollama_result["models"])
            models_response["providers"]["ollama"] = {
                "status": "connected",
                "message": ollama_result["message"]
            }
        else:
            models_response["providers"]["ollama"] = {
                "status": ollama_result["status"],
                "message": ollama_result["message"]
            }

        # Add total count
        models_response["total"] = len(models_response["models"])
        
        return models_response

    except Exception as e:
        print(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/status")
async def check_model_status():
    """
    Check the status of model providers
    """
    try:
        status = {
            "openai": {
                "configured": bool(os.getenv("OPENAI_API_KEY")),
                "api_key_present": bool(os.getenv("OPENAI_API_KEY")),
                "model": os.getenv("OPENAI_MODEL", "gpt-4o")
            },
            "ollama": {}
        }
        
        # Check Ollama
        ollama_result = await ModelProvider.list_ollama_models()
        status["ollama"] = {
            "running": ollama_result["status"] == "connected",
            "models_count": len(ollama_result["models"]),
            "message": ollama_result["message"]
        }
        
        return status
        
    except Exception as e:
        print(f"Error checking model status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
