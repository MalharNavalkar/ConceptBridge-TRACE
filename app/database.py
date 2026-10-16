from __future__ import annotations
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config
from app.models import Base

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "conceptbridge_accounts.sqlite3"

def database_url() -> str:
    url = os.environ.get("DATABASE_URL", f"sqlite:///{DEFAULT_DB}")
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url.removeprefix("postgres://")
    elif url.startswith("postgresql://") and "+" not in url.split(":", 1)[0]:
        url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url

def make_engine(url: str | None = None) -> Engine:
    url = url or database_url()
    options = {"pool_pre_ping": True}
    if url.startswith("sqlite:"):
        options["connect_args"] = {"check_same_thread": False, "timeout": 20}
    else:
        options.update(pool_recycle=300, pool_size=2, max_overflow=2)
    return create_engine(url, **options)

engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def configure_engine(new_engine: Engine):
    global engine, SessionLocal
    engine.dispose()
    engine = new_engine
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def init_db():
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", database_url().replace("%", "%%"))
    command.upgrade(cfg, "head")
