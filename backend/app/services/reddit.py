from sqlalchemy.orm import Session
from ..models import Mention
from datetime import datetime
import httpx

UA = {"User-Agent": "social-listening/0.1"}
BASE = "https://www.reddit.com"


def _store_post(db: Session, post: dict) -> int:
    data = post.get("data", {})
    url = BASE + data.get("permalink", "")
    title = data.get("title")
    author = data.get("author")
    created = data.get("created_utc")
    published = datetime.utcfromtimestamp(created) if created else None
    try:
        m = Mention(
            title=title,
            summary=data.get("selftext"),
            url=url,
            source="reddit",
            author=author,
            published_at=published,
            external_id=data.get("id"),
            thread_external_id=data.get("id"),
            parent_external_id=None,
            reply_depth=0,
        )
        db.add(m)
        db.commit()
        db.refresh(m)
        return 1
    except Exception:
        db.rollback()
        return 0


def _store_comment(db: Session, c: dict, thread_id: str, depth: int) -> int:
    data = c.get("data", {})
    body = data.get("body")
    if not body:
        return 0
    url = BASE + data.get("permalink", "") if data.get("permalink") else f"https://reddit.com/comments/{thread_id}"
    author = data.get("author")
    created = data.get("created_utc")
    published = datetime.utcfromtimestamp(created) if created else None
    try:
        m = Mention(
            title=None,
            summary=body,
            url=url,
            source="reddit",
            author=author,
            published_at=published,
            external_id=data.get("id"),
            thread_external_id=thread_id,
            parent_external_id=data.get("parent_id"),
            reply_depth=depth,
        )
        db.add(m)
        db.commit()
        db.refresh(m)
        return 1
    except Exception:
        db.rollback()
        return 0


def _walk_comments(db: Session, node: dict, thread_id: str, depth: int) -> int:
    added = 0
    if node.get("kind") == "t1":
        added += _store_comment(db, node, thread_id, depth)
    data = node.get("data", {})
    replies = data.get("replies")
    if isinstance(replies, dict):
        children = replies.get("data", {}).get("children", [])
        for ch in children:
            added += _walk_comments(db, ch, thread_id, depth + 1)
    return added


def ingest_reddit_search(db: Session, query: str, subreddit: str | None, limit: int = 25) -> int:
    added = 0
    params = {"q": query, "limit": str(limit), "sort": "new", "restrict_sr": "on" if subreddit else "off"}
    path = f"/r/{subreddit}/search.json" if subreddit else "/search.json"
    with httpx.Client(timeout=15.0, headers=UA, follow_redirects=True) as client:
        r = client.get(BASE + path, params=params)
        r.raise_for_status()
        listing = r.json()
        for child in listing.get("data", {}).get("children", []):
            if child.get("kind") != "t3":
                continue
            added += _store_post(db, child)
            thread_id = child.get("data", {}).get("id")
            # Fetch full comment tree
            try:
                cr = client.get(BASE + f"/comments/{thread_id}.json", params={"limit": 500})
                cr.raise_for_status()
                tree = cr.json()
                if isinstance(tree, list) and len(tree) > 1:
                    comments_listing = tree[1]
                    for c in comments_listing.get("data", {}).get("children", []):
                        added += _walk_comments(db, c, thread_id, 1)
            except Exception:
                pass
    return added
