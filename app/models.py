from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Merchant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    merchant_id: int = Field(foreign_key="merchant.id")
    name: str
    description: str
    price_cents: int


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    merchant_id: int = Field(foreign_key="merchant.id")
    status: str = Field(default="created")
    total_cents: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id")
    product_id: int = Field(foreign_key="product.id")
    quantity: int
    unit_price_cents: int
