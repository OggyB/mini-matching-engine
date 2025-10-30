from enum import StrEnum

class Symbol(StrEnum):
    ABC = 'ABC'
    XYZ = 'XYZ'
    DEF = 'DEF'

class OrderType(StrEnum):
    AMEND = 'amend'
    CREATE = 'create'
    CANCEL = 'cancel'

class OrderSide(StrEnum):
    BUY = 'B'
    SELL = 'S'