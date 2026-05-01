"""
models.py
---------
Mapeamento ORM das tabelas do banco (SQLAlchemy 2.x).
As relações são LAZY por padrão para demonstrar o problema N+1.
"""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger, ForeignKey, Integer, Numeric,
    String, DateTime, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Category(Base):
    __tablename__ = "categories"

    id:   Mapped[int]  = mapped_column(Integer, primary_key=True)
    name: Mapped[str]  = mapped_column(String(100), nullable=False, unique=True)

    products: Mapped[list["Product"]] = relationship(back_populates="category", lazy="select")


class User(Base):
    __tablename__ = "users"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True)
    name:       Mapped[str]      = mapped_column(String(150), nullable=False)
    email:      Mapped[str]      = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    orders: Mapped[list["Order"]] = relationship(back_populates="user", lazy="select")


class Product(Base):
    __tablename__ = "products"

    id:          Mapped[int]     = mapped_column(Integer, primary_key=True)
    name:        Mapped[str]     = mapped_column(String(200), nullable=False)
    price:       Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock:       Mapped[int]     = mapped_column(Integer, nullable=False, default=0)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    created_at:  Mapped[datetime]   = mapped_column(DateTime, server_default=func.now())

    category:    Mapped["Category | None"] = relationship(back_populates="products", lazy="select")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product", lazy="select")


class Order(Base):
    __tablename__ = "orders"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True)
    user_id:    Mapped[int]      = mapped_column(ForeignKey("users.id"), nullable=False)
    total:      Mapped[Decimal]  = mapped_column(Numeric(12, 2), nullable=False, default=0)
    status:     Mapped[str]      = mapped_column(String(50), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # LAZY → provoca N+1 quando acessado sem joinedload
    user:  Mapped["User"]           = relationship(back_populates="orders",      lazy="select")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order",
                                                    cascade="all, delete-orphan", lazy="select")


class OrderItem(Base):
    __tablename__ = "order_items"

    id:         Mapped[int]     = mapped_column(Integer, primary_key=True)
    order_id:   Mapped[int]     = mapped_column(ForeignKey("orders.id"),   nullable=False)
    product_id: Mapped[int]     = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity:   Mapped[int]     = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order:   Mapped["Order"]   = relationship(back_populates="items",        lazy="select")
    product: Mapped["Product"] = relationship(back_populates="order_items",  lazy="select")
