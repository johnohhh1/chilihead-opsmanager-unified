"""
Quick test script to verify attachment system
Run after syncing emails to check if attachments are stored
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database import SessionLocal
from models import EmailAttachment, EmailCache

def test_attachments():
    """Check stored attachments"""
    db = SessionLocal()

    try:
        # Count total attachments
        total = db.query(EmailAttachment).count()
        print(f"\n=== Attachment System Test ===")
        print(f"Total attachments stored: {total}")

        if total == 0:
            print("\n[INFO] No attachments found. Sync emails first.")
            print("Go to Smart Inbox and click 'Sync Emails'")
            return

        # Count by type
        images = db.query(EmailAttachment).filter(
            EmailAttachment.mime_type.like('image/%')
        ).count()
        print(f"Image attachments: {images}")

        # Count inline vs regular
        inline = db.query(EmailAttachment).filter(
            EmailAttachment.is_inline == True
        ).count()
        print(f"Inline images: {inline}")
        print(f"Regular attachments: {total - inline}")

        # Show recent attachments
        print("\n=== Recent Attachments ===")
        recent = db.query(EmailAttachment).order_by(
            EmailAttachment.created_at.desc()
        ).limit(5).all()

        for att in recent:
            # Get email subject
            email = db.query(EmailCache).filter(
                EmailCache.thread_id == att.thread_id
            ).first()
            subject = email.subject[:50] if email else "Unknown"

            print(f"\n- {att.filename}")
            print(f"  Type: {att.mime_type}")
            print(f"  Size: {att.size_bytes:,} bytes")
            print(f"  Inline: {att.is_inline}")
            print(f"  Content-ID: {att.content_id or 'N/A'}")
            print(f"  Email: {subject}...")
            print(f"  URL: /api/attachments/{att.id}")
            if att.content_id:
                print(f"  CID URL: /api/attachments/by-cid/{att.thread_id}/{att.content_id}")

        print("\n=== Test Complete ===")
        print("\nNext steps:")
        print("1. View an email with images in Smart Inbox")
        print("2. Verify images display correctly")
        print("3. Run AI analysis on RAP Mobile email")

    finally:
        db.close()

if __name__ == "__main__":
    test_attachments()
