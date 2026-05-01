"""
routers/orm_router.py
---------------------
Endpoints que usam SQLAlchemy ORM (Hibernate equivalente em Python).

Rotas:
  GET  /orm/users/{id}                  → Leitura simples
  POST /orm/orders                      → Escrita (INSERT com cascade)
  GET  /orm/orders/{id}/details         → Leitura complexa N+1 (sem otimização)
  GET  /orm/orders/{id}/details/optimized → Leitura complexa com joinedload
"""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Order, OrderItem, User
from schemas import OrderIn, OrderOut, UserOut

router = APIRouter(prefix="/orm", tags=["ORM"])


# ── 1. Leitura Simples ─────────────────────────────────────────────────────────
@router.get("/users/{user_id}", response_model=UserOut)
def get_user_orm(user_id: int, db: Session = Depends(get_db)):
    """SELECT simples por PK — ORM gera: SELECT * FROM users WHERE id = :id"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ── 2. Escrita ─────────────────────────────────────────────────────────────────
@router.post("/orders", response_model=OrderOut)
def create_order_orm(payload: OrderIn, db: Session = Depends(get_db)):
    """
    INSERT de pedido + itens via ORM (cascade).
    O ORM emite um INSERT por linha (sem batch nativo por padrão).
    """
    total = sum(
        item.unit_price * item.quantity for item in payload.items
    )
    order = Order(
        user_id=payload.user_id,
        total=total,
        status="pending",
    )
    for i in payload.items:
        order.items.append(
            OrderItem(
                product_id=i.product_id,
                quantity=i.quantity,
                unit_price=i.unit_price,
            )
        )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


# ── 3a. Leitura Complexa — N+1 (sem otimização) ────────────────────────────────
@router.get("/orders/{order_id}/details", response_model=OrderOut)
def get_order_n1(order_id: int, db: Session = Depends(get_db)):
    """
    Problema N+1:
      - 1 query para o pedido
      - 1 query para o usuário
      - N queries para os itens
      - N queries para produto de cada item
      - N queries para categoria de cada produto
    Total: pode passar de 50 queries para um pedido com 10 itens.
    """
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Força o carregamento lazy (dispara as queries N+1)
    _ = order.user.name
    for item in order.items:
        _ = item.product.name
        _ = item.product.category.name if item.product.category else ""

    return order


# ── 3b. Leitura Complexa — Otimizada com joinedload ────────────────────────────
@router.get("/orders/{order_id}/details/optimized", response_model=OrderOut)
def get_order_optimized(order_id: int, db: Session = Depends(get_db)):
    """
    ORM otimizado com joinedload:
      1 única query com LEFT OUTER JOINs — equivalente ao JOIN FETCH do Hibernate.
    """
    order = (
        db.query(Order)
        .options(
            joinedload(Order.user),
            joinedload(Order.items).joinedload(OrderItem.product),
        )
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
