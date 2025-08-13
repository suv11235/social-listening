from sqlalchemy import Column, Integer, String, Text, DateTime, Float, UniqueConstraint
from .db import Base
from datetime import datetime


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # e.g., 'rss', 'twitter'
    url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Mention(Base):
    __tablename__ = "mentions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)
    url = Column(String(1000), nullable=False, index=True)
    source = Column(String(100), nullable=False)
    author = Column(String(200), nullable=True)
    published_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sentiment = Column(Float, nullable=True)

    # Threading (nullable for backward compatibility)
    external_id = Column(String(200), nullable=True)  # platform-native id
    parent_external_id = Column(String(200), nullable=True)
    thread_external_id = Column(String(200), nullable=True)  # root id of thread
    reply_depth = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint("url", name="uq_mentions_url"),
    )
