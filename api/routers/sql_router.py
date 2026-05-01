"""
routers/sql_router.py
---------------------
Endpoints que usam SQL nativo via psycopg2 (JdbcTemplate equivalente).

Rotas:
  GET  /sql/users/{id}           → Leitura simples
  POST /sql/orders               → Escrita (INSERT em batch)
  GET  /sql/orders/{id}/details  → Leitura complexa com JOINs (1 query)
"""
from decimal import Decimal

import psycopg2.extras
from fastapi import APIRouter, Depends, HTTPException

from database import get_raw_conn
from schemas import OrderIn, RawRow

router = APIRouter(prefix="/sql", tags=["SQL Nativo"])


# ── 1. Leitura Simples ─────────────────────────────────────────────────────────
@router.get("/users/{user_id}")
def get_user_sql(user_id: int, conn=Depends(get_raw_conn)) -> RawRow:
    """SELECT simples por PK — SQL escrito à mão, sem abstração."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = %s",
            (user_id,),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)


# ── 2. Escrita ─────────────────────────────────────────────────────────────────
@router.post("/orders")
def create_order_sql(payload: OrderIn, conn=Depends(get_raw_conn)) -> dict:
    """
    INSERT de pedido + itens via SQL nativo.
    Usa executemany (batch) para os itens — mais eficiente que o ORM padrão.
    """
    total = sum(i.unit_price * i.quantity for i in payload.items)

    with conn.cursor() as cur:
        # Inserir o pedido
        cur.execute(
            """
            INSERT INTO orders (user_id, total, status)
            VALUES (%s, %s, 'pending')
            RETURNING id
            """,
            (payload.user_id, total),
        )
        order_id = cur.fetchone()[0]

        # Inserir itens em batch
        psycopg2.extras.execute_batch(
            cur,
            """
            INSERT INTO order_items (order_id, product_id, quantity, unit_price)
            VALUES (%s, %s, %s, %s)
            """,
            [
                (order_id, i.product_id, i.quantity, float(i.unit_price))
                for i in payload.items
            ],
            page_size=100,
        )
    conn.commit()
    return {"order_id": order_id, "total": float(total), "status": "pending"}


# ── 3. Leitura Complexa — 1 query com todos os JOINs ──────────────────────────
@router.get("/orders/{order_id}/details")
def get_order_details_sql(order_id: int, conn=Depends(get_raw_conn)) -> list[RawRow]:
    """
    Uma única query com 4 JOINs.
    Sem N+1, sem abstração, resultado previsível e controlado.
    """
    sql = """
        SELECT
            o.id           AS order_id,
            o.status,
            o.total,
            o.created_at,
            u.id           AS user_id,
            u.name         AS user_name,
            u.email        AS user_email,
            oi.id          AS item_id,
            oi.quantity,
            oi.unit_price,
            p.id           AS product_id,
            p.name         AS product_name,
            p.price        AS product_price,
            c.name         AS category_name
        FROM  orders       o
        JOIN  users        u  ON u.id  = o.user_id
        JOIN  order_items  oi ON oi.order_id   = o.id
        JOIN  products     p  ON p.id  = oi.product_id
        LEFT  JOIN categories c ON c.id = p.category_id
        WHERE o.id = %s
        ORDER BY oi.id
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (order_id,))
        rows = cur.fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="Order not found")
    return [dict(r) for r in rows]
