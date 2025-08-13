from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas import RSSIngestRequest, HNSearchRequest, MastoSearchRequest, TwitterIngestRequest, RedditSearchRequest
from ..services.rss import ingest_rss
from ..services.hn import search_hn_and_store
from ..services.masto import search_and_store_threads
from ..services.twitter import ingest_tweet_by_id
from ..services.reddit import ingest_reddit_search


router = APIRouter()


@router.post("/rss")
def ingest_rss_endpoint(payload: RSSIngestRequest, db: Session = Depends(get_db)):
    try:
        added = ingest_rss(db, payload.url)
        return {"status": "ok", "added": added}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/hn-search")
def ingest_hn_search(payload: HNSearchRequest, db: Session = Depends(get_db)):
    try:
        added = search_hn_and_store(db, payload.query, payload.hits_per_page or 50)
        return {"status": "ok", "added": added}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/masto-search")
def ingest_masto_search(payload: MastoSearchRequest, db: Session = Depends(get_db)):
    try:
        added = search_and_store_threads(db, payload.instance, payload.query, payload.limit or 40)
        return {"status": "ok", "added": added}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/twitter/tweet")
def ingest_twitter_tweet(payload: TwitterIngestRequest, db: Session = Depends(get_db)):
    try:
        added = ingest_tweet_by_id(db, payload.bearer_token, payload.tweet_id, payload.include_replies or False)
        return {"status": "ok", "added": added}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/reddit/search")
def ingest_reddit(payload: RedditSearchRequest, db: Session = Depends(get_db)):
    try:
        added = ingest_reddit_search(db, payload.query, payload.subreddit, payload.limit or 25)
        return {"status": "ok", "added": added}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
