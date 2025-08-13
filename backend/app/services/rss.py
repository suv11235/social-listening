import feedparser
from sqlalchemy.orm import Session
from datetime import datetime
from ..models import Mention
from hashlib import md5
import httpx


def _heuristic_sentiment(text: str) -> float:
    if not text:
        return 0.0
    text_l = text.lower()
    score = 0
    for w in ["good", "great", "excellent", "love", "positive", "up"]:
        if w in text_l:
            score += 1
    for w in ["bad", "terrible", "hate", "negative", "down"]:
        if w in text_l:
            score -= 1
    return max(min(score / 3.0, 1.0), -1.0)


def ingest_rss(db: Session, feed_url: str, source_name: str = "rss") -> int:
    feed_url = str(feed_url)
    feed = None
    try:
        headers = {
            "User-Agent": "social-listening/0.1 (+https://localhost)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, */*;q=0.8",
        }
        with httpx.Client(timeout=10.0, follow_redirects=True, headers=headers) as client:
            resp = client.get(feed_url)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
    except Exception:
        # Fallback to feedparser fetching by URL
        feed = feedparser.parse(feed_url)
    added = 0
    for entry in getattr(feed, "entries", []) or []:
        url = getattr(entry, "link", None) or getattr(entry, "id", None)
        if not url:
            # fallback unique-ish URL
            key = (getattr(entry, "title", "") + str(getattr(entry, "published", ""))).encode("utf-8")
            url = f"urn:rss:{md5(key).hexdigest()}"
        title = getattr(entry, "title", None)
        summary = getattr(entry, "summary", None) or getattr(entry, "description", None)
        author = getattr(entry, "author", None)
        published = None
        if getattr(entry, "published_parsed", None):
            try:
                published = datetime(*entry.published_parsed[:6])
            except Exception:
                published = None
        mention = Mention(
            title=title,
            summary=summary,
            url=url,
            source=source_name,
            author=author,
            published_at=published,
            sentiment=_heuristic_sentiment(f"{title or ''} {summary or ''}")
        )
        try:
            db.add(mention)
            db.commit()
            db.refresh(mention)
            added += 1
        except Exception:
            db.rollback()
            # likely a unique conflict on URL
            continue
    return added
