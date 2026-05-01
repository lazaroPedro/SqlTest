"""
schemas.py
----------
Schemas Pydantic para validação de entrada e serialização de saída.
"""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


# ── Usuário ───────────────────────────────────────────────────────────────────
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:         int
    name:       str
    email:      str
    created_at: datetime | None = None


# ── Produto ───────────────────────────────────────────────────────────────────
class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:    int
    name:  str
    price: Decimal
    stock: int


# ── Item de pedido ─────────────────────────────────────────────────────────────
class OrderItemIn(BaseModel):
    product_id: int
    quantity:   int
    unit_price: Decimal


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:         int
    product_id: int
    quantity:   int
    unit_price: Decimal


# ── Pedido ─────────────────────────────────────────────────────────────────────
class OrderIn(BaseModel):
    user_id: int
    items:   list[OrderItemIn]


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:         int
    user_id:    int
    total:      Decimal
    status:     str
    created_at: datetime | None = None
    items:      list[OrderItemOut] = []


# Para respostas de SQL nativo (dict puro)
RawRow = dict[str, Any]
