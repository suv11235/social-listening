from sqlalchemy.orm import Session
from ..models import Mention
from datetime import datetime
import httpx

ALGOLIA_API = "https://hn.algolia.com/api/v1/search"


def search_hn_and_store(db: Session, query: str, hits_per_page: int = 50) -> int:
    params = {"query": query, "tags": "(story,comment)", "hitsPerPage": hits_per_page}
    added = 0
    with httpx.Client(timeout=10.0, follow_redirects=True, headers={"User-Agent": "social-listening/0.1"}) as client:
        resp = client.get(ALGOLIA_API, params=params)
        resp.raise_for_status()
        data = resp.json()
        for hit in data.get("hits", []):
            url = hit.get("url") or (f"https://news.ycombinator.com/item?id={hit.get('objectID')}")
            title = hit.get("title") or hit.get("story_title") or None
            summary = hit.get("comment_text") or hit.get("story_text") or hit.get("_highlightResult", {}).get("comment_text", {}).get("value") or None
            author = hit.get("author")
            created_i = hit.get("created_at_i")
            published = datetime.utcfromtimestamp(created_i) if created_i else None
            try:
                mention = Mention(
                    title=title,
                    summary=summary,
                    url=url,
                    source="hackernews",
                    author=author,
                    published_at=published,
                )
                db.add(mention)
                db.commit()
                db.refresh(mention)
                added += 1
            except Exception:
                db.rollback()
                continue
    return added
