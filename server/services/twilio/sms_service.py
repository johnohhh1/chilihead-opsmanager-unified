"""
Twilio SMS Service for sending texts to managers
"""
import os
from twilio.rest import Client
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class SMSService:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        if not all([self.account_sid, self.auth_token, self.from_number]):
            raise ValueError("Missing Twilio credentials in environment variables")
        
        self.client = Client(self.account_sid, self.auth_token)
        
        # Manager contacts
        self.managers = {
            "john": {
                "name": "John (MP)",
                "phone": "+18327565450"
            },
            "jason": {
                "name": "Jason",
                "phone": "+12489158176"
            },
            "twright": {
                "name": "T Wright",
                "phone": "+15867224594"
            },
            "tiffany": {
                "name": "Tiffany Larkins",
                "phone": "+13139125662"
            }
        }
    
    def send_sms(self, to_number: str, message: str) -> Dict:
        """Send an SMS to a single number"""
        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            
            logger.info(f"SMS sent successfully to {to_number}. SID: {message_obj.sid}")
            return {
                "success": True,
                "message_sid": message_obj.sid,
                "to": to_number,
                "status": message_obj.status
            }
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_number}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "to": to_number
            }
    
    def send_to_managers(self, message: str, manager_ids: List[str] = None) -> List[Dict]:
        """Send SMS to multiple managers"""
        if manager_ids is None:
            manager_ids = list(self.managers.keys())
        
        results = []
        for manager_id in manager_ids:
            manager = self.managers.get(manager_id.lower())
            if not manager:
                results.append({
                    "success": False,
                    "error": f"Unknown manager ID: {manager_id}",
                    "manager_id": manager_id
                })
                continue
            
            result = self.send_sms(manager["phone"], message)
            result["manager_id"] = manager_id
            result["manager_name"] = manager["name"]
            results.append(result)
        
        return results
    
    def get_managers_list(self) -> List[Dict]:
        """Get list of all managers"""
        return [
            {
                "id": key,
                "name": value["name"],
                "phone": value["phone"]
            }
            for key, value in self.managers.items()
        ]


# Singleton instance
_sms_service = None

def get_sms_service() -> SMSService:
    """Get or create SMS service singleton"""
    global _sms_service
    if _sms_service is None:
        _sms_service = SMSService()
    return _sms_service
