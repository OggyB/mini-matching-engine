from pydantic import BaseModel

from common.enums.order import OrderSide


class BookModel(BaseModel):
    price: int
    ts: int
    seq: int
    order_id: str
    qty: int
    side: OrderSide