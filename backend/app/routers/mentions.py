from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..db import get_db
from ..models import Mention
from ..schemas import MentionOut


router = APIRouter()


@router.get("/mentions", response_model=List[MentionOut])
def list_mentions(
    db: Session = Depends(get_db),
    query: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    if query in ("undefined", "null", ""):  # tolerate bad client params
        query = None
    if source in ("undefined", "null", ""):
        source = None
    q = db.query(Mention)
    if query:
        like = f"%{query}%"
        q = q.filter((Mention.title.ilike(like)) | (Mention.summary.ilike(like)))
    if source:
        q = q.filter(Mention.source == source)
    q = q.order_by(Mention.published_at.desc().nullslast(), Mention.fetched_at.desc())
    return q.offset(offset).limit(limit).all()
