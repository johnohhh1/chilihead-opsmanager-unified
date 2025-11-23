"""
Test RAP Mobile dashboard image extraction and vision analysis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from models import EmailAttachment

# Load environment
load_dotenv()

def check_rap_mobile_images():
    """Check if RAP Mobile images are properly stored with data"""

    # Connect to database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/chilihead_ops')
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("="*60)
    print("RAP MOBILE IMAGE ANALYSIS CHECK")
    print("="*60)

    # Find RAP Mobile attachments
    rap_attachments = db.query(EmailAttachment).filter(
        EmailAttachment.filename.like('%tableau%')
    ).all()

    if not rap_attachments:
        rap_attachments = db.query(EmailAttachment).filter(
            EmailAttachment.content_id.like('%tableau%')
        ).all()

    print(f"\nFound {len(rap_attachments)} RAP Mobile/Tableau attachments")

    for att in rap_attachments:
        print(f"\n--- Attachment Details ---")
        print(f"ID: {att.id}")
        print(f"Thread: {att.thread_id}")
        print(f"Filename: {att.filename}")
        print(f"Content-ID: {att.content_id}")
        print(f"MIME Type: {att.mime_type}")
        print(f"Size: {att.size_bytes} bytes")
        print(f"Is Inline: {att.is_inline}")
        print(f"Has Data: {'YES' if att.data else 'NO'}")

        if att.data:
            print(f"Data Length: {len(att.data)} chars")
            print(f"Data Preview: {att.data[:100]}...")
        else:
            print("WARNING: No base64 data stored for this image!")
            print("Vision analysis will fail without the image data!")

    # Check a recent thread with images
    print("\n" + "="*60)
    print("CHECKING RECENT IMAGE THREADS")
    print("="*60)

    recent_images = db.query(EmailAttachment).filter(
        EmailAttachment.mime_type.like('image/%')
    ).limit(5).all()

    for img in recent_images:
        status = "OK" if img.data else "MISSING DATA"
        print(f"[{status}] {img.filename} - Thread: {img.thread_id[:10]}...")

    db.close()

    print("\n" + "="*60)
    print("RECOMMENDATIONS:")
    print("="*60)
    print("1. If images have no data, re-sync the email to fetch attachment data")
    print("2. Check email_sync.py lines 429-437 - attachment fetching logic")
    print("3. Ensure Gmail API has proper scope for attachment access")
    print("4. For vision to work, the 'data' field MUST contain base64 image data")

if __name__ == "__main__":
    check_rap_mobile_images()