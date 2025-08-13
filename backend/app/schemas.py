from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


class MentionOut(BaseModel):
    id: int
    title: Optional[str] = None
    summary: Optional[str] = None
    url: str
    source: str
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    fetched_at: datetime
    sentiment: Optional[float] = None

    class Config:
        from_attributes = True


class RSSIngestRequest(BaseModel):
    url: HttpUrl


class HNSearchRequest(BaseModel):
    query: str
    hits_per_page: Optional[int] = 50


class MastoSearchRequest(BaseModel):
    instance: str  # e.g., "mastodon.social"
    query: str
    limit: Optional[int] = 40


class TwitterIngestRequest(BaseModel):
    bearer_token: str
    tweet_id: str
    include_replies: Optional[bool] = False


class RedditSearchRequest(BaseModel):
    query: str
    subreddit: Optional[str] = None
    limit: Optional[int] = 25
