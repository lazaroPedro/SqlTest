"""
database.py
-----------
Configura dois mecanismos de acesso ao banco:
  1. SQLAlchemy (ORM)  — pool gerenciado pelo próprio SQLAlchemy
  2. psycopg2 Pool     — pool bruto para SQL nativo
"""
import os
from psycopg2 import pool as pg_pool
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# ── Variáveis de ambiente ──────────────────────────────────────────────────────
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "benchmark")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ── 1. SQLAlchemy (ORM) ────────────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    echo=False,   # True → imprime o SQL gerado pelo ORM no terminal
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency FastAPI: sessão ORM (fecha automaticamente ao final)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── 2. psycopg2 Pool (SQL Nativo) ──────────────────────────────────────────────
_pg_pool: pg_pool.ThreadedConnectionPool | None = None


def get_pg_pool() -> pg_pool.ThreadedConnectionPool:
    global _pg_pool
    if _pg_pool is None:
        _pg_pool = pg_pool.ThreadedConnectionPool(
            minconn=5,
            maxconn=60,
            host=DB_HOST,
            port=int(DB_PORT),
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
        )
    return _pg_pool


def get_raw_conn():
    """Dependency FastAPI: conexão bruta do pool psycopg2."""
    pool = get_pg_pool()
    conn = pool.getconn()
    try:
        yield conn
    finally:
        conn.rollback()   # garante estado limpo antes de devolver
        pool.putconn(conn)
