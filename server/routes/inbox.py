"""API routes for Inbox feature"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List

from database import get_db
from services.email_sync import EmailSyncService

router = APIRouter()


class MarkReadRequest(BaseModel):
    is_read: bool


class AddDomainRequest(BaseModel):
    domain: str


class RemoveDomainRequest(BaseModel):
    domain: str


@router.post("/sync-inbox")
async def sync_inbox(max_results: int = 50, db: Session = Depends(get_db)):
    """
    Manually trigger email sync from Gmail
    Fetches emails from priority domains and stores in cache
    """
    try:
        result = EmailSyncService.sync_emails(db, max_results=max_results)
        return result
    except Exception as e:
        raise HTTPException(500, f"Email sync failed: {str(e)}")


@router.get("/inbox")
async def get_inbox(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    domain: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get inbox emails from local cache
    Supports filtering by read status and domain
    """
    try:
        emails = EmailSyncService.get_inbox_emails(
            db=db,
            limit=limit,
            offset=offset,
            unread_only=unread_only,
            domain=domain
        )

        return {
            "success": True,
            "emails": emails,
            "count": len(emails),
            "offset": offset,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch inbox: {str(e)}")


@router.get("/inbox/{thread_id}")
async def get_email_thread(thread_id: str, db: Session = Depends(get_db)):
    """
    Get full email content by thread_id
    Includes body_html, body_text, and AI analysis if available
    """
    try:
        email = EmailSyncService.get_email_by_thread(db, thread_id)

        if not email:
            raise HTTPException(404, "Email not found")

        return {
            "success": True,
            "email": email
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch email: {str(e)}")


@router.patch("/inbox/{thread_id}/mark-read")
async def mark_email_read(
    thread_id: str,
    payload: MarkReadRequest,
    db: Session = Depends(get_db)
):
    """
    Mark email as read/unread in local cache
    """
    try:
        success = EmailSyncService.mark_read(db, thread_id, payload.is_read)

        if not success:
            raise HTTPException(404, "Email not found")

        return {
            "success": True,
            "thread_id": thread_id,
            "is_read": payload.is_read
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to update read status: {str(e)}")


@router.get("/settings/domains")
async def get_watched_domains(db: Session = Depends(get_db)):
    """
    Get list of domains being watched for inbox sync
    """
    try:
        domains = EmailSyncService.get_watched_domains(db)

        return {
            "success": True,
            "domains": domains
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch domains: {str(e)}")


@router.post("/settings/domains")
async def add_watched_domain(
    payload: AddDomainRequest,
    db: Session = Depends(get_db)
):
    """
    Add a domain to the watch list
    Example: "brinker.com", "hotschedules.com"
    """
    try:
        # Basic validation
        domain = payload.domain.strip().lower()
        if not domain or '@' in domain:
            raise HTTPException(400, "Invalid domain format. Use 'example.com' without @ symbol")

        result = EmailSyncService.add_watched_domain(db, domain)

        return {
            **result,
            "message": f"Domain '{domain}' added to watch list"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to add domain: {str(e)}")


@router.delete("/settings/domains")
async def remove_watched_domain(
    payload: RemoveDomainRequest,
    db: Session = Depends(get_db)
):
    """
    Remove a domain from the watch list
    """
    try:
        domain = payload.domain.strip().lower()
        result = EmailSyncService.remove_watched_domain(db, domain)

        return {
            **result,
            "message": f"Domain '{domain}' removed from watch list"
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to remove domain: {str(e)}")


@router.get("/inbox/stats")
async def get_inbox_stats(db: Session = Depends(get_db)):
    """
    Get inbox statistics
    """
    try:
        # Get cache stats
        cache_stats = EmailSyncService.get_cache_stats(db)

        # Get inbox-specific stats
        from models import EmailCache
        total_inbox = db.query(EmailCache).filter(EmailCache.is_archived == False).count()
        unread = db.query(EmailCache).filter(
            EmailCache.is_archived == False,
            EmailCache.is_read == False
        ).count()

        return {
            "success": True,
            "inbox": {
                "total": total_inbox,
                "unread": unread,
                "read": total_inbox - unread
            },
            "cache": cache_stats
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch stats: {str(e)}")
