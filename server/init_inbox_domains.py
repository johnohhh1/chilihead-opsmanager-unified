"""
Initialize WatchConfig with default priority domains for Inbox feature
Run this once to set up default domains
"""
from database import SessionLocal
from models import WatchConfig

def init_domains():
    db = SessionLocal()

    try:
        # Check if config exists
        config = db.query(WatchConfig).filter(WatchConfig.id == 1).first()

        # Default domains for restaurant operations
        default_domains = [
            "brinker.com",
            "hotschedules.com",
            "chilis.com"
        ]

        if not config:
            # Create new config
            config = WatchConfig(
                id=1,
                priority_domains=default_domains,
                priority_senders=[],
                priority_keywords=[],
                excluded_subjects=[]
            )
            db.add(config)
            print("✅ Created new WatchConfig with default domains:")
            for domain in default_domains:
                print(f"   - {domain}")
        else:
            # Update existing config
            existing_domains = set(config.priority_domains or [])
            new_domains = set(default_domains)
            all_domains = list(existing_domains.union(new_domains))

            config.priority_domains = all_domains

            print("✅ Updated WatchConfig with domains:")
            for domain in all_domains:
                print(f"   - {domain}")

        db.commit()
        print("\n✨ Inbox domains configured successfully!")
        print("You can now sync emails from these domains in the Inbox tab.")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_domains()
