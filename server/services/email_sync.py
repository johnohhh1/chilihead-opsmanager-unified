"""
Email syncing and caching service
Manages the Gmail mirror and analysis cache
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from models import EmailCache, EmailAnalysisCache
from services.model_quality import (
    get_model_tier,
    get_default_trust_score,
    should_auto_reanalyze,
    update_trust_score
)


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
