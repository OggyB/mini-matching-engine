from enum import StrEnum


class NatsSubject(StrEnum):
    ORDERS_IN = "orders.in"
    TRADES_OUT = "trades.out"