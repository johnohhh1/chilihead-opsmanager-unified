"""
SMS/Texting routes for manager communication
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from services.twilio.sms_service import get_sms_service, SMSService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sms", tags=["sms"])


class DraftMessageRequest(BaseModel):
    """Request to draft a message using AI"""
    prompt: str = Field(..., description="What you want to communicate")
    context: Optional[str] = Field(None, description="Additional context for the AI")


class SendMessageRequest(BaseModel):
    """Request to send SMS to managers"""
    message: str = Field(..., description="Message text to send", max_length=1600)
    manager_ids: Optional[List[str]] = Field(
        None, 
        description="Manager IDs to send to (john, jason, twright, tiffany). If empty, sends to all."
    )


class MessageResponse(BaseModel):
    """Response after sending messages"""
    success: bool
    results: List[dict]
    total_sent: int
    total_failed: int


@router.get("/managers")
async def get_managers(sms_service: SMSService = Depends(get_sms_service)):
    """Get list of all managers who can receive texts"""
    try:
        managers = sms_service.get_managers_list()
        return {"managers": managers}
    except Exception as e:
        logger.error(f"Error getting managers list: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/draft")
async def draft_message(
    request: DraftMessageRequest,
    sms_service: SMSService = Depends(get_sms_service)
):
    """
    Use AI to draft a message based on a prompt.
    This will call your Ollama service to generate a professional message.
    """
    try:
        # Import here to avoid circular imports
        import requests
        
        # Craft a prompt for the AI to generate a professional text message
        system_prompt = """You are helping draft professional text messages for a restaurant manager to send to their team. 

Keep messages:
- Clear and concise (under 300 characters if possible)
- Professional but friendly
- Action-oriented with specific details
- Include timing/deadlines when relevant

Do not include greetings like "Hey team" as those will be added automatically.
Just provide the core message content."""

        full_prompt = f"{system_prompt}\n\nDraft a text message for: {request.prompt}"
        if request.context:
            full_prompt += f"\n\nAdditional context: {request.context}"
        
        # Generate the message using Ollama
        try:
            ollama_response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "mistral:latest",
                    "prompt": full_prompt,
                    "stream": False
                },
                timeout=30
            )

            if ollama_response.status_code != 200:
                raise Exception(f"Ollama API returned status {ollama_response.status_code}")

            drafted_message = ollama_response.json().get("response", "").strip()

            return {
                "drafted_message": drafted_message,
                "character_count": len(drafted_message),
                "managers": sms_service.get_managers_list()
            }
        except requests.exceptions.ConnectionError:
            raise HTTPException(
                status_code=503,
                detail="AI service (Ollama) is not running. Please start Ollama or write your message manually."
            )
        except requests.exceptions.Timeout:
            raise HTTPException(
                status_code=504,
                detail="AI service timed out. Please try again or write your message manually."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error drafting message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to draft message: {str(e)}")


@router.post("/send", response_model=MessageResponse)
async def send_message(
    request: SendMessageRequest,
    sms_service: SMSService = Depends(get_sms_service)
):
    """
    Send a text message to selected managers
    """
    try:
        # Validate message length
        if len(request.message) > 1600:
            raise HTTPException(
                status_code=400,
                detail="Message too long. Keep it under 1600 characters."
            )
        
        # Send the messages
        results = sms_service.send_to_managers(
            message=request.message,
            manager_ids=request.manager_ids
        )
        
        # Count successes and failures
        total_sent = sum(1 for r in results if r.get("success"))
        total_failed = sum(1 for r in results if not r.get("success"))
        
        return MessageResponse(
            success=total_failed == 0,
            results=results,
            total_sent=total_sent,
            total_failed=total_failed
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending messages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send messages: {str(e)}")


@router.get("/status")
async def get_status(sms_service: SMSService = Depends(get_sms_service)):
    """
    Get SMS service status - check if Twilio is configured
    """
    return sms_service.get_status()


@router.post("/test")
async def test_send(sms_service: SMSService = Depends(get_sms_service)):
    """
    Send a test message to verify Twilio is working.
    Sends only to John to test the system.
    """
    try:
        if not sms_service.is_configured:
            raise HTTPException(
                status_code=400,
                detail="Twilio is not configured. Please set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER in your .env file."
            )

        test_message = "Test message from ChiliHead OpsManager. Twilio SMS is working! 🎉"
        result = sms_service.send_sms(
            to_number=sms_service.managers["john"]["phone"],
            message=test_message
        )
        return {"test_result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in test send: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
