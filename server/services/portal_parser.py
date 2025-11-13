"""
Portal Results Parser - Extract metrics from daily BI email images
Watches for emails from c00605mgr@chilis.com with portal results
"""

import re
import base64
from io import BytesIO
from typing import Optional, Dict
from datetime import datetime
import pytz

try:
    from PIL import Image
    import pytesseract
    import os

    # Windows default installation path
    if os.name == 'nt' and os.path.exists(r'C:\Program Files\Tesseract-OCR\tesseract.exe'):
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("Warning: Tesseract OCR not available. Install tesseract-ocr and pytesseract.")


class PortalResultsParser:
    """Parse portal metrics from Business Intelligence email images"""

    BI_EMAIL_SENDER = "c00605mgr@chilis.com"

    @staticmethod
    def is_bi_email(sender: str, subject: str = "") -> bool:
        """
        Detect if this is the daily BI portal results email (RAP Mobile)

        Args:
            sender: Email sender address
            subject: Email subject (optional)

        Returns:
            True if this is a BI portal results email
        """
        sender_lower = sender.lower()
        subject_lower = subject.lower() if subject else ""

        # Primary detection: RAP Mobile email forwarded from your account
        if PortalResultsParser.BI_EMAIL_SENDER.lower() in sender_lower and 'rap mobile' in subject_lower:
            return True

        # Also match original sender from Brinker BI
        if 'business.intelligence@brinker.com' in sender_lower and 'rap mobile' in subject_lower:
            return True

        # Fallback: subject contains RAP/portal keywords
        if subject:
            keywords = ['rap mobile', 'restaurant analytics portal', 'portal mobile']
            if any(keyword in subject_lower for keyword in keywords):
                return True

        return False

    @staticmethod
    def extract_text_from_image(image_data: str, mime_type: str = "image/png") -> Optional[str]:
        """
        Use OCR to extract text from base64-encoded image

        Args:
            image_data: Base64-encoded image data
            mime_type: MIME type of the image

        Returns:
            Extracted text or None if OCR fails
        """
        if not TESSERACT_AVAILABLE:
            print("Error: Tesseract OCR not available")
            return None

        try:
            # Decode base64 image
            image_bytes = base64.urlsafe_b64decode(image_data)
            image = Image.open(BytesIO(image_bytes))

            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Perform OCR
            text = pytesseract.image_to_string(image)

            return text

        except Exception as e:
            print(f"Error extracting text from image: {e}")
            return None

    @staticmethod
    def parse_portal_metrics(text: str) -> Dict:
        """
        Parse portal metrics from OCR text

        Expected metrics:
        - Sales (dollar amount)
        - Labor % (percentage)
        - Guest Satisfaction (score or percentage)
        - Food Cost % (percentage)
        - Speed of Service (time or score)

        Args:
            text: OCR-extracted text from portal image

        Returns:
            Dictionary of parsed metrics
        """
        metrics = {}

        # Clean up text
        text = text.replace('\n', ' ').replace('  ', ' ')

        # Parse Sales (look for dollar amounts)
        sales_patterns = [
            r'sales?\s*[:\-]?\s*\$?\s*([\d,]+\.?\d*)',
            r'\$\s*([\d,]+\.?\d*)\s*sales?',
            r'net\s+sales?\s*[:\-]?\s*\$?\s*([\d,]+\.?\d*)'
        ]
        for pattern in sales_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                sales_str = match.group(1).replace(',', '')
                try:
                    metrics['sales'] = float(sales_str)
                    break
                except ValueError:
                    pass

        # Parse Labor % (look for percentages after "labor")
        labor_patterns = [
            r'labor\s*%?\s*[:\-]?\s*([\d.]+)\s*%?',
            r'labor\s+cost\s*[:\-]?\s*([\d.]+)\s*%?'
        ]
        for pattern in labor_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    metrics['labor_percent'] = float(match.group(1))
                    break
                except ValueError:
                    pass

        # Parse Guest Satisfaction
        guest_sat_patterns = [
            r'guest\s+sat(?:isfaction)?\s*[:\-]?\s*([\d.]+)\s*%?',
            r'satisfaction\s*[:\-]?\s*([\d.]+)\s*%?',
            r'guest\s+score\s*[:\-]?\s*([\d.]+)'
        ]
        for pattern in guest_sat_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    metrics['guest_satisfaction'] = float(match.group(1))
                    break
                except ValueError:
                    pass

        # Parse Food Cost %
        food_cost_patterns = [
            r'food\s+cost\s*%?\s*[:\-]?\s*([\d.]+)\s*%?',
            r'food\s*%\s*[:\-]?\s*([\d.]+)'
        ]
        for pattern in food_cost_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    metrics['food_cost_percent'] = float(match.group(1))
                    break
                except ValueError:
                    pass

        # Parse Speed of Service (could be in seconds or score)
        speed_patterns = [
            r'speed\s+of\s+service\s*[:\-]?\s*([\d.]+)',
            r'sos\s*[:\-]?\s*([\d.]+)',
            r'service\s+time\s*[:\-]?\s*([\d.]+)'
        ]
        for pattern in speed_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    metrics['speed_of_service'] = float(match.group(1))
                    break
                except ValueError:
                    pass

        # Add metadata
        metrics['parsed_at'] = datetime.now(pytz.timezone('America/New_York')).isoformat()
        metrics['raw_text'] = text[:500]  # Store first 500 chars for debugging

        return metrics

    @staticmethod
    def format_metrics_for_digest(metrics: Dict) -> str:
        """
        Format parsed metrics for inclusion in daily digest

        Args:
            metrics: Parsed metrics dictionary

        Returns:
            Formatted string for daily brief
        """
        if not metrics or len(metrics) <= 2:  # Only metadata, no actual metrics
            return "📊 **Portal Results**: Could not parse metrics from image"

        lines = ["📊 **Yesterday's Portal Results** (from BI email):"]

        if 'sales' in metrics:
            lines.append(f"   • Sales: ${metrics['sales']:,.2f}")

        if 'labor_percent' in metrics:
            lines.append(f"   • Labor: {metrics['labor_percent']:.1f}%")

        if 'guest_satisfaction' in metrics:
            lines.append(f"   • Guest Satisfaction: {metrics['guest_satisfaction']:.1f}")

        if 'food_cost_percent' in metrics:
            lines.append(f"   • Food Cost: {metrics['food_cost_percent']:.1f}%")

        if 'speed_of_service' in metrics:
            lines.append(f"   • Speed of Service: {metrics['speed_of_service']:.1f}")

        return "\n".join(lines)

    @staticmethod
    def _download_attachment(message_id: str, attachment_id: str) -> Optional[str]:
        """Download Gmail attachment and return base64 data"""
        try:
            from services.gmail import get_service
            service = get_service()
            attachment = service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()
            return attachment.get('data')
        except Exception as e:
            print(f"Error downloading attachment: {e}")
            return None

    @staticmethod
    def process_bi_email(messages: list, db = None) -> Optional[Dict]:
        """
        Process a BI email and extract portal metrics

        Args:
            messages: Gmail message list from thread
            db: Database session (optional, for storing results)

        Returns:
            Parsed metrics dictionary or None if parsing fails
        """
        from services.ai_triage import extract_attachments_with_images

        if not messages:
            return None

        # Get the most recent message
        latest_msg = messages[-1]
        message_id = latest_msg.get('id')

        # Extract headers
        headers = {h["name"].lower(): h["value"]
                  for h in latest_msg.get("payload", {}).get("headers", [])}

        sender = headers.get("from", "")
        subject = headers.get("subject", "")

        # Verify this is a BI email
        if not PortalResultsParser.is_bi_email(sender, subject):
            return None

        # Extract images from email
        body_text, images = extract_attachments_with_images(latest_msg.get("payload", {}))

        if not images:
            print("Warning: BI email has no images attached")
            return None

        # Try to parse each image (skip first signature image, parse dashboard)
        for idx, image_info in enumerate(images):
            # Skip the first image (it's the restaurant signature/header)
            if idx == 0 and len(images) > 1:
                print(f"Skipping signature image: {image_info.get('filename')}")
                continue

            image_data = image_info.get("data")

            # If no inline data, download attachment
            if not image_data and image_info.get("attachment_id"):
                print(f"Downloading attachment: {image_info.get('filename')}")
                image_data = PortalResultsParser._download_attachment(
                    message_id,
                    image_info.get("attachment_id")
                )

            if not image_data:
                continue

            # Extract text via OCR
            extracted_text = PortalResultsParser.extract_text_from_image(
                image_data,
                image_info.get("mime_type", "image/png")
            )

            if not extracted_text:
                continue

            print(f"OCR extracted {len(extracted_text)} chars from image {idx+1}")

            # Parse metrics from text
            metrics = PortalResultsParser.parse_portal_metrics(extracted_text)

            if metrics and len(metrics) > 2:  # Has actual metrics beyond metadata
                # Store in database if provided
                if db:
                    try:
                        PortalResultsParser._store_metrics_in_db(db, metrics, sender, subject)
                    except Exception as e:
                        print(f"Warning: Failed to store portal metrics in DB: {e}")

                return metrics

        return None

    @staticmethod
    def _store_metrics_in_db(db, metrics: Dict, sender: str, subject: str):
        """Store parsed portal metrics in database"""
        from models import PortalMetrics
        from datetime import datetime
        import pytz

        eastern = pytz.timezone('America/New_York')

        # Create new portal metrics record
        portal_record = PortalMetrics(
            report_date=datetime.now(eastern).date(),
            sales=metrics.get('sales'),
            labor_percent=metrics.get('labor_percent'),
            guest_satisfaction=metrics.get('guest_satisfaction'),
            food_cost_percent=metrics.get('food_cost_percent'),
            speed_of_service=metrics.get('speed_of_service'),
            raw_ocr_text=metrics.get('raw_text', ''),
            email_sender=sender,
            email_subject=subject
        )

        db.add(portal_record)
        db.commit()
        db.refresh(portal_record)

        print(f"✅ Stored portal metrics for {portal_record.report_date}")
