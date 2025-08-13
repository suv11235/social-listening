from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./social_listening.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def _ensure_sqlite_columns():
    if engine.dialect.name != "sqlite":
        return
    with engine.connect() as conn:
        # Check mentions table columns
        cols = set()
        res = conn.exec_driver_sql("PRAGMA table_info('mentions')")
        for row in res:
            # row: (cid, name, type, notnull, dflt_value, pk)
            cols.add(row[1])
        to_add = []
        if "external_id" not in cols:
            to_add.append("external_id VARCHAR(200)")
        if "parent_external_id" not in cols:
            to_add.append("parent_external_id VARCHAR(200)")
        if "thread_external_id" not in cols:
            to_add.append("thread_external_id VARCHAR(200)")
        if "reply_depth" not in cols:
            to_add.append("reply_depth INTEGER")
        for coldef in to_add:
            conn.exec_driver_sql(f"ALTER TABLE mentions ADD COLUMN {coldef}")

def init_db():
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    try:
        _ensure_sqlite_columns()
    except Exception:
        # Best-effort; in dev you can delete social_listening.db to rebuild
        pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
