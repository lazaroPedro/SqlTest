"""
main.py
-------
Ponto de entrada da aplicação.
Configura o FastAPI, registra os routers (ORM e SQL) e inicializa
o instrumentador Prometheus para coleta automática de métricas HTTP.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from database import engine
from models import Base
from routers.orm_router import router as orm_router
from routers.sql_router import router as sql_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria as tabelas caso não existam (seguro com init.sql já executado)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="ORM vs SQL Benchmark",
    description="API de benchmark comparando SQLAlchemy ORM vs SQL Nativo (psycopg2).",
    version="1.0.0",
    lifespan=lifespan,
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(orm_router, prefix="/api")
app.include_router(sql_router, prefix="/api")

# ── Prometheus ────────────────────────────────────────────────────────────────
# Expõe /metrics com latência, throughput e status de cada endpoint
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
