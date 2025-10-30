from collections import deque
from typing import Deque, Dict, Optional

from common.enums.order import Symbol, OrderSide
from sortedcontainers import SortedDict
from common.models.booker import BookModel
from common.models.orders import CreateOrder, AmendOrder


class OrderBook:
    """OrderBook is a simple book keeper"""
    def __init__(self, symbol: Symbol):
        self.symbol = symbol

        # active order books (buy = bids, sell = asks)
        self.bids: SortedDict[int, Deque[BookModel]] = SortedDict()
        self.asks: SortedDict[int, Deque[BookModel]] = SortedDict()

        # lookup table for fast access by order_id
        self.lookup: Dict[str, BookModel] = {}

    def add_order(self, order: CreateOrder):
        # build book model from order data
        book_data = BookModel(
            price=order.price,
            seq=order.seq,
            ts=order.ts,
            order_id=order.order_id,
            qty=order.qty,
            side=order.side
        )

        # select correct book (buy or sell)
        books = self.__get_books(side=order.side)

        # create new price level if missing
        if order.price not in books:
            books[order.price] = deque()

        dq = books[order.price]

        inserted = False

        # keep FIFO ordering by timestamp and sequence
        for i, existing in enumerate(dq):
            if (book_data.ts, book_data.seq) < (existing.ts, existing.seq):
                dq.insert(i, book_data)
                inserted = True
                break

        # if not inserted earlier, append to the end
        if not inserted:
            dq.append(book_data)

        # store reference for quick lookup
        self.lookup[order.order_id] = book_data

    def cancel_order(self, order_id: str):
        """Cancel an existing order by ID."""
        book_data = self.lookup.pop(order_id, None)
        if not book_data:
            return

        # get correct book (bids or asks)
        books = self.__get_books(side=book_data.side)
        if not books:
            return None

        dq = books.get(book_data.price)
        if not dq:
            return

        # remove order from deque
        for order in dq:
            if order.order_id == order_id:
                dq.remove(order)
                break

        # if no more orders at this price, remove price level
        if not dq:
            del books[book_data.price]

    def amend_order(self, amend: AmendOrder) -> Optional[BookModel]:
        """Amend an existing order (price or quantity)."""
        book_data = self.lookup.get(amend.order_id)
        if not book_data:
            return None

        # qty = 0 → treat as cancel
        if amend.qty is not None and amend.qty == 0:
            self.cancel_order(amend.order_id)
            return None

        side = amend.side or book_data.side
        books = self.__get_books(side)

        # handle price change (move between price levels)
        if amend.price is not None and amend.price != book_data.price:
            old_price = book_data.price
            dq_old = books.get(old_price)
            if dq_old:
                dq_old.remove(book_data)
                if not dq_old:
                    del books[old_price]

            # update price and reinsert to correct level
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

        # update quantity if given
        if amend.qty is not None:
            book_data.qty = amend.qty

        return book_data

    def get_best_bid(self) -> BookModel | None:
        """Get the highest buy (bid) order."""
        if not self.bids:
            return None

        # peek last item (max price)
        price, dq = self.bids.peekitem(-1)
        if dq:
            return dq[0]

        return None

    def get_best_ask(self) -> BookModel | None:
        """Get the lowest sell (ask) order."""
        if not self.asks:
            return None

        # peek first item (min price)
        price, dq = self.asks.peekitem(0)
        if dq:
            return dq[0]
        return None

    def is_active(self, order_id: str) -> bool:
        """Check if an order is still active."""
        return order_id in self.lookup

    def reduce_qty(self, order_id: str, qty: int):
        """Reduce quantity of an active order."""
        book_data = self.lookup.get(order_id)
        if not book_data:
            return

        # reduce remaining quantity
        book_data.qty -= qty

        # remove if fully filled
        if book_data.qty <= 0:
            self.cancel_order(order_id)

    def __get_books(self, side: OrderSide) -> SortedDict[int, Deque[BookModel]]:
        """Get the correct book (bids or asks) by side."""
        return self.bids if side == OrderSide.BUY else self.asks

