"""
Migration script to create the dismissed_items table
Run this once: python migrate_dismissed_items.py
"""

from database import engine
from models import Base, DismissedItem

def migrate():
    print("Creating dismissed_items table...")
    try:
        DismissedItem.__table__.create(engine, checkfirst=True)
        print("✅ dismissed_items table created successfully!")
        print("\nYou can now dismiss items from the Daily Brief.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    migrate()
