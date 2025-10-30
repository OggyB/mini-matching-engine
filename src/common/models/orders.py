from pydantic import BaseModel
from typing import Optional

from common.enums.order import OrderType, Symbol, OrderSide

class BaseOrder(BaseModel):
    type: OrderType
    ts: int
    seq: int
    symbol: Symbol
    order_id: str

class CreateOrder(BaseOrder):
    side: OrderSide
    price: int
    qty: int

class AmendOrder(BaseOrder):
    qty: Optional[int] = None
    price: Optional[int] = None
    side: Optional[OrderSide] = None
