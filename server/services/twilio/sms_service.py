"""
Gmail SMS Service - Send texts via email-to-SMS gateways
Uses your existing Gmail integration - no extra APIs needed!
"""
import logging
from typing import List, Dict
from services.gmail import get_service
from email.mime.text import MIMEText
import base64

logger = logging.getLogger(__name__)

class SMSService:
    def __init__(self):
        # Manager contacts with MMS gateway addresses
        # MMS gateways support both SMS and MMS
        self.managers = {
            "john": {
                "name": "John (MP)",
                "phone": "+18327565450",
                "carrier": "Metro PCS",
                "sms_email": "8327565450@mymetropcs.com"
            },
            "jason": {
                "name": "Jason",
                "phone": "+12489158176",
                "carrier": "Verizon",
                "sms_email": "2489158176@vzwpix.com"
            },
            "twright": {
                "name": "T Wright",
                "phone": "+15867224594",
                "carrier": "Verizon",
                "sms_email": "5867224594@vzwpix.com"
            },
            "tiffany": {
                "name": "Tiffany Larkins",
                "phone": "+13139125662",
                "carrier": "AT&T",
                "sms_email": "3139125662@mms.att.net"
            }
        }

        # Check if Gmail is available
        try:
            get_service()
            self.is_configured = True
            logger.info("Gmail SMS service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gmail service: {str(e)}")
            self.is_configured = False

    def send_email_sms(self, to_email: str, message: str, manager_name: str) -> Dict:
        """Send SMS via email-to-SMS gateway"""
        if not self.is_configured:
            return {
                "success": False,
                "error": "Gmail not configured. Please authenticate with Gmail.",
                "to": to_email
            }

        try:
            service = get_service()

            # Create email message (plain text only for SMS gateways)
            msg = MIMEText(message)
            msg['to'] = to_email
            msg['subject'] = ''  # Empty subject - SMS gateways ignore it

            # Encode the message
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')

            # Send via Gmail API
            send_result = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            logger.info(f"SMS sent successfully to {manager_name} ({to_email}). Message ID: {send_result['id']}")
            return {
                "success": True,
                "message_id": send_result['id'],
                "to": to_email,
                "manager_name": manager_name
            }
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_email}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "to": to_email
            }

    def send_sms(self, to_number: str, message: str) -> Dict:
        """
        Legacy method for compatibility
        Note: to_number is not used - we use manager_id instead
        """
        return {
            "success": False,
            "error": "Use send_to_managers() with manager IDs instead",
            "to": to_number
        }

    def send_to_managers(self, message: str, manager_ids: List[str] = None) -> List[Dict]:
        """Send SMS to multiple managers via email-to-SMS gateways"""
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

            # Send via email-to-SMS gateway
            result = self.send_email_sms(
                to_email=manager["sms_email"],
                message=message,
                manager_name=manager["name"]
            )
            result["manager_id"] = manager_id
            result["manager_name"] = manager["name"]
            results.append(result)

        return results

    def get_managers_list(self) -> List[Dict]:
        """Get list of all managers with carrier info"""
        return [
            {
                "id": key,
                "name": value["name"],
                "phone": value["phone"],
                "carrier": value["carrier"],
                "sms_email": value["sms_email"]
            }
            for key, value in self.managers.items()
        ]

    def get_status(self) -> Dict:
        """Get SMS service status"""
        return {
            "configured": self.is_configured,
            "method": "Email-to-SMS Gateway",
            "service": "Gmail",
            "manager_count": len(self.managers),
            "note": "Sends SMS via carrier email gateways (free!)"
        }


# Singleton instance
_sms_service = None

def get_sms_service() -> SMSService:
    """Get or create SMS service singleton"""
    global _sms_service
    if _sms_service is None:
        _sms_service = SMSService()
    return _sms_service
