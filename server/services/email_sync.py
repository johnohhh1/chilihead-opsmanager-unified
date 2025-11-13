"""
Email syncing and caching service
Manages the Gmail mirror and analysis cache
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import base64
from models import EmailCache, EmailAnalysisCache, WatchConfig
from services.model_quality import (
    get_model_tier,
    get_default_trust_score,
    should_auto_reanalyze,
    update_trust_score
)
from services.gmail import get_service, get_user_threads


class EmailSyncService:
    """Manages email caching and analysis synchronization"""

    @staticmethod
    def cache_email(
        db: Session,
        thread_id: str,
        gmail_message_id: str,
        subject: str,
        sender: str,
        recipients: Dict,
        body_text: str,
        body_html: str,
        attachments: List[Dict],
        labels: List[str],
        received_at: datetime,
        has_images: bool = False
    ) -> EmailCache:
        """
        Store or update email in cache
        This is the "Gmail mirror" - stores raw email data
        """
        # Check if email already exists
        existing = db.query(EmailCache).filter_by(thread_id=thread_id).first()

        if existing:
            # Update existing
            existing.gmail_message_id = gmail_message_id
            existing.subject = subject
            existing.sender = sender
            existing.recipients = recipients
            existing.body_text = body_text
            existing.body_html = body_html
            existing.attachments_json = attachments
            existing.labels = labels
            existing.received_at = received_at
            existing.gmail_synced_at = datetime.utcnow()
            existing.has_images = has_images
            existing.is_read = "UNREAD" not in labels
            db.commit()
            return existing
        else:
            # Create new
            email = EmailCache(
                thread_id=thread_id,
                gmail_message_id=gmail_message_id,
                subject=subject,
                sender=sender,
                recipients=recipients,
                body_text=body_text,
                body_html=body_html,
                attachments_json=attachments,
                labels=labels,
                received_at=received_at,
                has_images=has_images,
                is_read="UNREAD" not in labels
            )
            db.add(email)
            db.commit()
            return email

    @staticmethod
    def get_cached_email(db: Session, thread_id: str) -> Optional[EmailCache]:
        """Retrieve email from cache"""
        return db.query(EmailCache).filter_by(thread_id=thread_id).first()

    @staticmethod
    def get_cached_emails_by_date(
        db: Session,
        start_date: datetime,
        end_date: datetime = None
    ) -> List[EmailCache]:
        """Get emails within date range from cache"""
        query = db.query(EmailCache).filter(EmailCache.received_at >= start_date)

        if end_date:
            query = query.filter(EmailCache.received_at <= end_date)

        return query.order_by(desc(EmailCache.received_at)).all()

    @staticmethod
    def cache_analysis(
        db: Session,
        thread_id: str,
        analysis_json: Dict,
        model_used: str,
        priority_score: int = 50,
        category: str = "routine",
        key_entities: Dict = None,
        suggested_tasks: List[Dict] = None,
        sentiment: str = "neutral",
        tokens_used: int = 0
    ) -> EmailAnalysisCache:
        """
        Store or update AI analysis in cache
        Automatically assigns model tier and trust score
        """
        # Determine model quality
        tier = get_model_tier(model_used)
        trust_score = get_default_trust_score(model_used)

        # Check if analysis already exists
        existing = db.query(EmailAnalysisCache).filter_by(thread_id=thread_id).first()

        if existing:
            # Save previous analysis for comparison
            existing.previous_analysis = existing.analysis_json

            # Update with new analysis
            existing.analysis_json = analysis_json
            existing.model_used = model_used
            existing.model_tier = tier
            existing.trust_score = trust_score
            existing.priority_score = priority_score
            existing.category = category
            existing.key_entities = key_entities or {}
            existing.suggested_tasks = suggested_tasks or []
            existing.sentiment = sentiment
            existing.tokens_used = tokens_used
            existing.analyzed_at = datetime.utcnow()
            existing.analysis_version += 1
            existing.needs_reanalysis = False
            existing.reanalysis_reason = None

            db.commit()
            return existing
        else:
            # Create new analysis
            analysis = EmailAnalysisCache(
                thread_id=thread_id,
                analysis_json=analysis_json,
                model_used=model_used,
                model_tier=tier,
                trust_score=trust_score,
                priority_score=priority_score,
                category=category,
                key_entities=key_entities or {},
                suggested_tasks=suggested_tasks or [],
                sentiment=sentiment,
                tokens_used=tokens_used
            )
            db.add(analysis)
            db.commit()
            return analysis

    @staticmethod
    def get_cached_analysis(db: Session, thread_id: str) -> Optional[EmailAnalysisCache]:
        """Retrieve analysis from cache"""
        return db.query(EmailAnalysisCache).filter_by(thread_id=thread_id).first()

    @staticmethod
    def needs_analysis(db: Session, thread_id: str, preferred_model: str = None) -> Dict[str, any]:
        """
        Check if email needs (re)analysis
        Returns {needs_analysis: bool, reason: str, suggested_model: str}

        Args:
            thread_id: Gmail thread ID
            preferred_model: User's preferred model (optional)
        """
        analysis = EmailSyncService.get_cached_analysis(db, thread_id)

        # No cached analysis = definitely needs analysis
        if not analysis:
            email = EmailSyncService.get_cached_email(db, thread_id)
            has_images = email.has_images if email else False
            from services.model_quality import get_recommended_model
            suggested = get_recommended_model(
                priority_score=70,  # Assume medium-high for new emails
                has_images=has_images,
                preferred_model=preferred_model
            )
            return {
                "needs_analysis": True,
                "reason": "no_cached_analysis",
                "suggested_model": suggested
            }

        # User flagged for reanalysis
        if analysis.needs_reanalysis:
            return {
                "needs_analysis": True,
                "reason": analysis.reanalysis_reason or "user_requested",
                "suggested_model": preferred_model or "gpt-4o"  # Use user preference or safe default
            }

        # Check if model quality is insufficient
        days_old = (datetime.utcnow() - analysis.analyzed_at).days
        auto_check = should_auto_reanalyze(
            model_tier=analysis.model_tier,
            trust_score=analysis.trust_score,
            priority_score=analysis.priority_score,
            days_old=days_old
        )

        if auto_check["should_reanalyze"]:
            return {
                "needs_analysis": True,
                "reason": auto_check["reason"],
                "suggested_model": auto_check.get("suggested_model", "gpt-oss-120b")
            }

        # Cached analysis is good
        return {
            "needs_analysis": False,
            "reason": "cached_analysis_valid",
            "suggested_model": None
        }

    @staticmethod
    def flag_for_reanalysis(
        db: Session,
        thread_id: str,
        reason: str = "user_requested"
    ) -> EmailAnalysisCache:
        """Mark an email analysis for re-analysis"""
        analysis = db.query(EmailAnalysisCache).filter_by(thread_id=thread_id).first()

        if analysis:
            analysis.needs_reanalysis = True
            analysis.reanalysis_reason = reason
            db.commit()

        return analysis

    @staticmethod
    def submit_feedback(
        db: Session,
        thread_id: str,
        feedback: str
    ) -> EmailAnalysisCache:
        """
        Update trust score based on user feedback
        feedback: 'accurate', 'missed_details', 'hallucinated', 'wrong_priority'
        """
        analysis = db.query(EmailAnalysisCache).filter_by(thread_id=thread_id).first()

        if analysis:
            # Update trust score
            new_score = update_trust_score(analysis.trust_score, feedback)
            analysis.trust_score = new_score
            analysis.user_feedback = feedback

            # If hallucinated, flag for immediate reanalysis
            if feedback == "hallucinated":
                analysis.needs_reanalysis = True
                analysis.reanalysis_reason = "model_hallucinated"

            db.commit()

        return analysis

    @staticmethod
    def get_emails_needing_reanalysis(db: Session, limit: int = 50) -> List[str]:
        """Get list of thread IDs that need reanalysis"""
        analyses = db.query(EmailAnalysisCache).filter_by(
            needs_reanalysis=True
        ).limit(limit).all()

        return [a.thread_id for a in analyses]

    @staticmethod
    def get_cache_stats(db: Session) -> Dict:
        """Get statistics about email cache"""
        total_emails = db.query(EmailCache).count()
        total_analyses = db.query(EmailAnalysisCache).count()

        # Count by tier
        trusted = db.query(EmailAnalysisCache).filter_by(model_tier="trusted").count()
        experimental = db.query(EmailAnalysisCache).filter_by(model_tier="experimental").count()
        unreliable = db.query(EmailAnalysisCache).filter_by(model_tier="unreliable").count()

        # Count needing reanalysis
        needs_reanalysis = db.query(EmailAnalysisCache).filter_by(needs_reanalysis=True).count()

        return {
            "total_emails_cached": total_emails,
            "total_analyses_cached": total_analyses,
            "analyses_by_tier": {
                "trusted": trusted,
                "experimental": experimental,
                "unreliable": unreliable
            },
            "needs_reanalysis": needs_reanalysis,
            "cache_hit_rate": f"{(total_analyses / max(total_emails, 1)) * 100:.1f}%"
        }

    # ============= INBOX FEATURE METHODS =============

    @staticmethod
    def build_domain_query(domains: List[str]) -> str:
        """Build Gmail query string to filter by domains"""
        if not domains:
            return ""
        # Create query like: "from:*@brinker.com OR from:*@hotschedules.com"
        domain_filters = [f"from:*@{domain}" for domain in domains]
        return " OR ".join(domain_filters)

    @staticmethod
    def parse_email_body(payload: dict) -> tuple:
        """Extract body_text and body_html from Gmail message payload"""
        body_text = None
        body_html = None

        def decode_body(data: str) -> str:
            """Decode base64url encoded body"""
            if not data:
                return ""
            # Gmail uses URL-safe base64
            data = data.replace('-', '+').replace('_', '/')
            # Add padding if needed
            missing_padding = len(data) % 4
            if missing_padding:
                data += '=' * (4 - missing_padding)
            try:
                return base64.b64decode(data).decode('utf-8', errors='ignore')
            except:
                return ""

        def extract_parts(payload: dict):
            """Recursively extract text and html parts"""
            nonlocal body_text, body_html

            mime_type = payload.get('mimeType', '')

            # Single part message
            if 'body' in payload and 'data' in payload['body']:
                data = payload['body']['data']
                decoded = decode_body(data)

                if mime_type == 'text/plain':
                    body_text = decoded
                elif mime_type == 'text/html':
                    body_html = decoded

            # Multipart message
            if 'parts' in payload:
                for part in payload['parts']:
                    part_mime = part.get('mimeType', '')

                    if part_mime == 'text/plain' and 'body' in part and 'data' in part['body']:
                        body_text = decode_body(part['body']['data'])
                    elif part_mime == 'text/html' and 'body' in part and 'data' in part['body']:
                        body_html = decode_body(part['body']['data'])
                    elif part_mime.startswith('multipart/'):
                        extract_parts(part)

        extract_parts(payload)
        return body_text, body_html

    @staticmethod
    def extract_email_metadata(message: dict) -> dict:
        """Extract metadata from Gmail message"""
        headers = {h['name'].lower(): h['value']
                  for h in message.get('payload', {}).get('headers', [])}

        # Parse recipients
        recipients = {
            'to': headers.get('to', '').split(',') if headers.get('to') else [],
            'cc': headers.get('cc', '').split(',') if headers.get('cc') else [],
            'bcc': []  # Gmail API doesn't expose BCC
        }

        # Clean recipient lists
        for key in recipients:
            recipients[key] = [r.strip() for r in recipients[key] if r.strip()]

        # Parse date
        date_str = headers.get('date', '')
        try:
            from email.utils import parsedate_to_datetime
            received_at = parsedate_to_datetime(date_str)
        except:
            received_at = datetime.now()

        # Check for images
        has_images = False
        payload = message.get('payload', {})
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType', '').startswith('image/'):
                    has_images = True
                    break

        # Get labels
        labels = message.get('labelIds', [])
        is_read = 'UNREAD' not in labels

        return {
            'subject': headers.get('subject', '(No Subject)'),
            'sender': headers.get('from', 'Unknown'),
            'recipients': recipients,
            'received_at': received_at,
            'labels': labels,
            'is_read': is_read,
            'has_images': has_images
        }

    @staticmethod
    def sync_emails(db: Session, max_results: int = 50) -> dict:
        """
        Sync emails from Gmail to local cache
        Fetches from priority domains + priority senders (for forwarded work emails)
        """
        try:
            # Get watched domains and senders from config
            config = db.query(WatchConfig).filter(WatchConfig.id == 1).first()
            if not config:
                return {"success": False, "error": "No watch config", "synced": 0}

            domains = config.priority_domains or []
            senders = config.priority_senders or []

            # Build query: domains OR specific senders (like your work forwarding email)
            query_parts = []

            for domain in domains:
                query_parts.append(f"from:*@{domain}")

            for sender in senders:
                query_parts.append(f"from:{sender}")

            if not query_parts:
                return {"success": False, "error": "No domains/senders configured", "synced": 0}

            query = " OR ".join(query_parts)
            print(f"[Email Sync] Query: {query}")

            threads = get_user_threads(max_results=max_results, query=query)

            synced_count = 0
            updated_count = 0

            for thread in threads:
                messages = thread.get('messages', [])
                if not messages:
                    continue

                # Use the first message in thread for metadata
                first_msg = messages[0]
                thread_id = thread.get('id')
                gmail_message_id = first_msg.get('id')

                # Check if already cached
                existing = db.query(EmailCache).filter(
                    EmailCache.thread_id == thread_id
                ).first()

                # Extract metadata
                metadata = EmailSyncService.extract_email_metadata(first_msg)
                body_text, body_html = EmailSyncService.parse_email_body(
                    first_msg.get('payload', {})
                )

                if existing:
                    # Update existing cache entry
                    existing.gmail_synced_at = datetime.now()
                    existing.labels = metadata['labels']
                    existing.is_read = metadata['is_read']
                    updated_count += 1
                else:
                    # Create new cache entry
                    email_cache = EmailCache(
                        thread_id=thread_id,
                        gmail_message_id=gmail_message_id,
                        subject=metadata['subject'],
                        sender=metadata['sender'],
                        recipients=metadata['recipients'],
                        body_text=body_text,
                        body_html=body_html,
                        attachments_json=[],  # TODO: Extract attachments if needed
                        labels=metadata['labels'],
                        received_at=metadata['received_at'],
                        is_read=metadata['is_read'],
                        has_images=metadata['has_images']
                    )
                    db.add(email_cache)
                    synced_count += 1

            db.commit()

            return {
                "success": True,
                "synced": synced_count,
                "updated": updated_count,
                "total": synced_count + updated_count,
                "domains": domains,
                "query": query
            }

        except Exception as e:
            db.rollback()
            print(f"[Email Sync Error] {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "synced": 0
            }

    @staticmethod
    def get_inbox_emails(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
        domain: Optional[str] = None
    ) -> List[dict]:
        """Get emails from local cache with optional filters"""
        query = db.query(EmailCache).filter(EmailCache.is_archived == False)

        # Filter by read status
        if unread_only:
            query = query.filter(EmailCache.is_read == False)

        # Filter by domain
        if domain:
            query = query.filter(EmailCache.sender.like(f"%@{domain}%"))

        # Order by received date (newest first)
        query = query.order_by(desc(EmailCache.received_at))

        # Apply pagination
        query = query.offset(offset).limit(limit)

        emails = query.all()

        # Convert to dict format
        result = []
        for email in emails:
            result.append({
                "thread_id": email.thread_id,
                "gmail_message_id": email.gmail_message_id,
                "subject": email.subject,
                "sender": email.sender,
                "recipients": email.recipients,
                "body_text": email.body_text[:500] if email.body_text else None,  # Preview only
                "received_at": email.received_at.isoformat(),
                "is_read": email.is_read,
                "is_archived": email.is_archived,
                "has_images": email.has_images,
                "labels": email.labels
            })

        return result

    @staticmethod
    def get_email_by_thread(db: Session, thread_id: str) -> Optional[dict]:
        """Get full email content by thread_id"""
        email = db.query(EmailCache).filter(EmailCache.thread_id == thread_id).first()

        if not email:
            return None

        # Check if we have cached analysis
        analysis = db.query(EmailAnalysisCache).filter(
            EmailAnalysisCache.thread_id == thread_id
        ).first()

        return {
            "thread_id": email.thread_id,
            "gmail_message_id": email.gmail_message_id,
            "subject": email.subject,
            "sender": email.sender,
            "recipients": email.recipients,
            "body_text": email.body_text,
            "body_html": email.body_html,
            "attachments": email.attachments_json,
            "received_at": email.received_at.isoformat(),
            "is_read": email.is_read,
            "is_archived": email.is_archived,
            "has_images": email.has_images,
            "labels": email.labels,
            "analysis": {
                "priority_score": analysis.priority_score,
                "category": analysis.category,
                "sentiment": analysis.sentiment,
                "key_entities": analysis.key_entities,
                "suggested_tasks": analysis.suggested_tasks
            } if analysis else None
        }

    @staticmethod
    def mark_read(db: Session, thread_id: str, is_read: bool) -> bool:
        """Mark email as read/unread in local cache"""
        email = db.query(EmailCache).filter(EmailCache.thread_id == thread_id).first()

        if not email:
            return False

        email.is_read = is_read
        db.commit()

        return True

    @staticmethod
    def get_watched_domains(db: Session) -> List[str]:
        """Get list of watched domains from WatchConfig"""
        config = db.query(WatchConfig).filter(WatchConfig.id == 1).first()

        if not config:
            return []

        return config.priority_domains or []

    @staticmethod
    def add_watched_domain(db: Session, domain: str) -> dict:
        """Add a domain to watch list"""
        config = db.query(WatchConfig).filter(WatchConfig.id == 1).first()

        if not config:
            # Create config if doesn't exist
            config = WatchConfig(
                id=1,
                priority_domains=[domain],
                priority_senders=[],
                priority_keywords=[],
                excluded_subjects=[]
            )
            db.add(config)
        else:
            # Ensure priority_domains is a list
            if config.priority_domains is None:
                config.priority_domains = []

            # Add domain if not already present
            if domain not in config.priority_domains:
                config.priority_domains = config.priority_domains + [domain]

        db.commit()
        db.refresh(config)

        return {
            "success": True,
            "domains": config.priority_domains or []
        }

    @staticmethod
    def remove_watched_domain(db: Session, domain: str) -> dict:
        """Remove a domain from watch list"""
        config = db.query(WatchConfig).filter(WatchConfig.id == 1).first()

        if not config:
            return {"success": False, "error": "Config not found"}

        if domain in config.priority_domains:
            config.priority_domains.remove(domain)
            db.commit()

        return {
            "success": True,
            "domains": config.priority_domains
        }
