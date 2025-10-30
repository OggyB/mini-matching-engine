from pydantic import BaseModel
from common.enums.order import OrderSide, Symbol


class Trade(BaseModel):
    ts: int
    seq: int
    symbol: Symbol
    buy_order_id: str
    sell_order_id: str
    qty: int
    price: int
    maker_order_id: str
    taker_side: OrderSide