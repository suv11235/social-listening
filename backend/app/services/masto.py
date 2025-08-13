from sqlalchemy.orm import Session
from ..models import Mention
from datetime import datetime
import httpx
import re
from html import unescape


def _masto_base(instance: str) -> str:
    instance = instance.strip().rstrip('/')
    if not instance.startswith('http'):
        instance = 'https://' + instance
    return instance


def _parse_datetime(dt_str: str | None):
    if not dt_str:
        return None
    try:
        # Example: 2025-08-12T15:04:05.000Z
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except Exception:
        return None


def _strip_html(html: str | None) -> str:
    if not html:
        return ''
    # Remove tags and unescape entities
    text = re.sub(r'<[^>]+>', ' ', html)
    text = unescape(text)
    return re.sub(r'\s+', ' ', text).strip()


def _store_status(db: Session, base: str, status: dict, thread_root_id: str | None, depth: int) -> int:
    sid = status.get("id")
    url = status.get("url") or f"{base}/@{status.get('account',{}).get('acct','')}/{sid}"
    content = status.get("content")
    author = status.get("account", {}).get("acct")
    published = _parse_datetime(status.get("created_at"))
    try:
        mention = Mention(
            title=None,
            summary=content,
            url=url,
            source="mastodon",
            author=author,
            published_at=published,
            external_id=sid,
            parent_external_id=status.get("in_reply_to_id"),
            thread_external_id=thread_root_id or (status.get("in_reply_to_id") or sid),
            reply_depth=depth,
        )
        db.add(mention)
        db.commit()
        db.refresh(mention)
        return 1
    except Exception:
        db.rollback()
        return 0


def _fetch_context(client: httpx.Client, base: str, status_id: str) -> dict:
    try:
        return client.get(f"{base}/api/v1/statuses/{status_id}/context").json()
    except Exception:
        return {"ancestors": [], "descendants": []}


def _fetch_hashtag(client: httpx.Client, base: str, tag: str, limit: int = 40) -> list[dict]:
    tag = tag.lstrip('#')
    try:
        resp = client.get(f"{base}/api/v1/timelines/tag/{tag}", params={"limit": limit})
        resp.raise_for_status()
        return resp.json() or []
    except Exception:
        return []


def _fetch_public(client: httpx.Client, base: str, limit: int = 40, local: bool | None = None) -> list[dict]:
    params = {"limit": limit}
    if local is not None:
        params["local"] = str(local).lower()
    try:
        resp = client.get(f"{base}/api/v1/timelines/public", params=params)
        resp.raise_for_status()
        return resp.json() or []
    except Exception:
        return []


def _match_any(text: str, tokens: list[str]) -> bool:
    lt = text.lower()
    return any(tok.lower() in lt for tok in tokens if tok)


def search_and_store_threads(db: Session, instance: str, query: str, limit: int = 40) -> int:
    base = _masto_base(instance)
    added = 0
    headers = {"User-Agent": "social-listening/0.1"}
    # Prepare tokens and hashtags from query
    raw_tokens = [t for t in re.split(r"\s+OR\s+|\s+", query) if t]
    hashtags = [t for t in raw_tokens if t.startswith('#')]
    tokens = [t.lstrip('#').strip('"') for t in raw_tokens if t and t not in hashtags]

    with httpx.Client(timeout=15.0, headers=headers, follow_redirects=True) as client:
        # 1) Try full-text search (may return empty without auth)
        try:
            resp = client.get(f"{base}/api/v2/search", params={"q": query, "type": "statuses", "limit": limit})
            resp.raise_for_status()
            statuses = resp.json().get("statuses", [])
        except Exception:
            statuses = []

        for s in statuses:
            status_id = s.get("id")
            added += _store_status(db, base, s, thread_root_id=None, depth=0)
            # Fetch and store thread context
            ctx = _fetch_context(client, base, status_id)
            for depth_group, key in enumerate(["ancestors", "descendants"], start=1):
                for r in ctx.get(key, []) or []:
                    added += _store_status(db, base, r, thread_root_id=status_id, depth=depth_group)

        # 2) Fallback: hashtag timelines
        if added == 0 and hashtags:
            for h in hashtags:
                tag_statuses = _fetch_hashtag(client, base, h, limit)
                for st in tag_statuses:
                    text = _strip_html(st.get("content"))
                    if tokens and not _match_any(text, tokens):
                        continue
                    sid = st.get("id")
                    added += _store_status(db, base, st, thread_root_id=None, depth=0)
                    ctx = _fetch_context(client, base, sid)
                    for depth_group, key in enumerate(["ancestors", "descendants"], start=1):
                        for r in ctx.get(key, []) or []:
                            added += _store_status(db, base, r, thread_root_id=sid, depth=depth_group)

        # 3) Fallback: public timeline + filter by tokens (if any tokens provided)
        if added == 0 and (tokens or hashtags):
            for local_flag in (True, False):
                pub = _fetch_public(client, base, limit, local=local_flag)
                for st in pub:
                    text = _strip_html(st.get("content"))
                    if hashtags:
                        # If hashtags given, require at least one hashtag match in content
                        if not any(f"#{h.lstrip('#').lower()}" in text.lower() for h in hashtags):
                            continue
                    if tokens and not _match_any(text, tokens):
                        continue
                    sid = st.get("id")
                    added += _store_status(db, base, st, thread_root_id=None, depth=0)
                    ctx = _fetch_context(client, base, sid)
                    for depth_group, key in enumerate(["ancestors", "descendants"], start=1):
                        for r in ctx.get(key, []) or []:
                            added += _store_status(db, base, r, thread_root_id=sid, depth=depth_group)

    return added
