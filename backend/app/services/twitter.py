from sqlalchemy.orm import Session
from ..models import Mention
from datetime import datetime
import httpx

BASE = "https://api.x.com/2"


def _store_tweet(db: Session, tw: dict) -> int:
    tweet_id = tw.get("id")
    text = tw.get("text")
    author = None
    if "author_id" in tw:
        author = tw.get("author_id")
    created_at = None
    if "created_at" in tw:
        try:
            created_at = datetime.fromisoformat(tw["created_at"].replace("Z", "+00:00"))
        except Exception:
            created_at = None
    url = f"https://twitter.com/i/web/status/{tweet_id}"
    try:
        m = Mention(
            title=None,
            summary=text,
            url=url,
            source="twitter",
            author=author,
            published_at=created_at,
            external_id=tweet_id,
            thread_external_id=tw.get("conversation_id") or tweet_id,
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


def ingest_tweet_by_id(db: Session, bearer_token: str, tweet_id: str, include_replies: bool = False) -> int:
    headers = {"Authorization": f"Bearer {bearer_token}", "User-Agent": "social-listening/0.1"}
    params = {"expansions": "author_id", "tweet.fields": "created_at,conversation_id"}
    added = 0
    with httpx.Client(timeout=15.0, headers=headers, follow_redirects=True) as client:
        r = client.get(f"{BASE}/tweets/{tweet_id}", params=params)
        r.raise_for_status()
        data = r.json()
        tw = data.get("data") or {}
        added += _store_tweet(db, tw)

        if include_replies:
            # Free tier likely won't allow search; attempt recent search by conversation_id
            try:
                conv = tw.get("conversation_id") or tweet_id
                sr = client.get(
                    f"{BASE}/tweets/search/recent",
                    params={
                        "query": f"conversation_id:{conv}",
                        "max_results": 50,
                        "tweet.fields": "created_at,conversation_id,author_id,referenced_tweets",
                    },
                )
                if sr.status_code == 200:
                    sdata = sr.json()
                    for t in sdata.get("data", []) or []:
                        # Mark replies with depth 1 (simplified; real depth would inspect referenced_tweets)
                        try:
                            t_id = t.get("id")
                            text = t.get("text")
                            created_at = None
                            if "created_at" in t:
                                created_at = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
                            url = f"https://twitter.com/i/web/status/{t_id}"
                            m = Mention(
                                title=None,
                                summary=text,
                                url=url,
                                source="twitter",
                                author=t.get("author_id"),
                                published_at=created_at,
                                external_id=t_id,
                                thread_external_id=conv,
                                parent_external_id=None,
                                reply_depth=1,
                            )
                            db.add(m)
                            db.commit()
                            db.refresh(m)
                            added += 1
                        except Exception:
                            db.rollback()
            except Exception:
                pass
    return added
