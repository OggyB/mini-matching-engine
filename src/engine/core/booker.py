from collections import deque
from typing import Deque, Dict, Optional

from common.enums.order import Symbol, OrderSide
from sortedcontainers import SortedDict
from common.models.booker import BookModel
from common.models.orders import CreateOrder, AmendOrder


class OrderBook:
    def __init__(self, symbol: Symbol):
        self.symbol = symbol

        # defining active books ( Sell and Buy )
        self.bids: SortedDict[int, Deque[BookModel]] = SortedDict()
        self.asks: SortedDict[int, Deque[BookModel]] = SortedDict()

        # order_id lookup
        self.lookup: Dict[str, BookModel] = {}

    def add_order(self, order: CreateOrder):
        book_data = BookModel(
            price=order.price,
            seq=order.seq,
            ts=order.ts,
            order_id=order.order_id,
            qty=order.qty,
            side=order.side
        )

        books = self.__get_books(side=order.side)

        if order.price not in books:
            books[order.price] = deque()

        dq = books[order.price]

        inserted = False
        for i, existing in enumerate(dq):
            if (book_data.ts, book_data.seq) < (existing.ts, existing.seq):
                dq.insert(i, book_data)
                inserted = True
                break

        if not inserted:
            dq.append(book_data)

        self.lookup[order.order_id] = book_data

    def cancel_order(self, order_id: str):
        book_data = self.lookup.pop(order_id, None)
        if not book_data:
            return

        books = self.__get_books(side=book_data.side)
        if not books:
            return None

        dq = books.get(book_data.price)
        if not dq:
            return

        for order in dq:
            if order.order_id == order_id:
                dq.remove(order)
                break

        if not dq:
            del books[book_data.price]

    def amend_order(self, amend: AmendOrder) -> Optional[BookModel]:
        book_data = self.lookup.get(amend.order_id)
        if not book_data:
            return None

        if amend.qty is not None and amend.qty == 0:
            self.cancel_order(amend.order_id)
            return None

        side = amend.side or book_data.side
        books = self.__get_books(side)

        if amend.price is not None and amend.price != book_data.price:
            old_price = book_data.price
            dq_old = books.get(old_price)
            if dq_old:
                dq_old.remove(book_data)
                if not dq_old:
                    del books[old_price]

            book_data.price = amend.price
            dq_new = books.setdefault(amend.price, deque())

            inserted = False
            for i, existing in enumerate(dq_new):
                if (book_data.ts, book_data.seq) < (existing.ts, existing.seq):
                    dq_new.insert(i, book_data)
                    inserted = True
                    break
            if not inserted:
                dq_new.append(book_data)

        if amend.qty is not None:
            book_data.qty = amend.qty

        return book_data

    def get_best_bid(self) -> BookModel | None:
        if not self.bids:
            return None

        price, dq = self.bids.peekitem(-1)
        if dq:
            return dq[0]

        return None

    def get_best_ask(self) -> BookModel | None:
        if not self.asks:
            return None

        price, dq = self.asks.peekitem(0)
        if dq:
            return dq[0]
        return None

    def is_active(self, order_id: str) -> bool:
        return order_id in self.lookup

    def reduce_qty(self, order_id: str, qty: int):
        book_data = self.lookup.get(order_id)
        if not book_data:
            return

        book_data.qty -= qty
        if book_data.qty <= 0:
            self.cancel_order(order_id)

    def __get_books(self, side: OrderSide) -> SortedDict[int, Deque[BookModel]]:
        return self.bids if side == OrderSide.BUY else self.asks

