import asyncio
from typing import Dict, Optional, List

from common.enums.order import Symbol, OrderSide, OrderType
from common.models.orders import CreateOrder, BaseOrder, AmendOrder
from common.models.trade import Trade
from engine.core.booker import OrderBook


class Matcher:
    """
        Matcher processes incoming orders and matches them within
        their respective order books.
    """
    def __init__(self):
        # store order books and symbol-specific locks
        self.books: Dict[Symbol, OrderBook] = {}
        self.locks: Dict[Symbol, asyncio.Lock] = {}

    def _get_book(self, symbol: Symbol) -> OrderBook:
        """Get or create an order book for the given symbol."""
        # create book and lock if not exist
        book = self.books.setdefault(symbol, OrderBook(symbol))
        self.locks.setdefault(symbol, asyncio.Lock())
        return book

    async def _with_lock(self, symbol: Symbol, func, *args, **kwargs):
        """Run a function safely under async lock per symbol."""
        lock = self.locks[symbol]
        async with lock:
            return await func(*args, **kwargs)

    async def handle_event(self, order: BaseOrder) -> Optional[List[Trade]]:
        """Handle an incoming order event (CREATE, AMEND, CANCEL)."""
        # ensure book exists for given symbol
        book = self._get_book(order.symbol)

        # process by order type
        if order.type == OrderType.CREATE:
            assert isinstance(order, CreateOrder)
            return await self._with_lock(symbol=book.symbol, func=self._handle_create, book=book, order=order)

        elif order.type == OrderType.AMEND:
            assert isinstance(order, AmendOrder)
            await self._with_lock(symbol=order.symbol, func=self._handle_amend, book=book, order=order)

        elif order.type == OrderType.CANCEL:
            await self._with_lock(symbol=order.symbol, func=self._handle_cancel, book=book, order=order)

        return []


    @staticmethod
    async def _handle_create(book: OrderBook, order: CreateOrder):
        """
                Process a new order and try to match it with the opposite side.
        """
        trades: List[Trade] = []

        # skip if order already exists
        if book.is_active(order_id=order.order_id):
            return trades

        # BUY side logic
        if order.side == OrderSide.BUY:
            while True:
                best_ask = book.get_best_ask()

                # stop if no match or price too high
                if not best_ask or best_ask.price > order.price or order.qty <= 0:
                    break

                # execute trade at best ask price
                trade_qty = min(order.qty, best_ask.qty)
                trade = Trade(
                    ts=order.ts,
                    seq=order.seq,
                    symbol=order.symbol,
                    buy_order_id=order.order_id,
                    sell_order_id=best_ask.order_id,
                    qty=trade_qty,
                    price=best_ask.price,
                    maker_order_id=best_ask.order_id,
                    taker_side=OrderSide.BUY
                )

                trades.append(trade)

                # reduce remaining qty for both sides
                order.qty -= trade_qty
                book.reduce_qty(order_id=best_ask.order_id, qty=trade_qty)

        # SELL side logic
        elif order.side == OrderSide.SELL:
            while True:
                best_bid = book.get_best_bid()

                # stop if no match or price too low
                if not best_bid or best_bid.price < order.price or order.qty <= 0:
                    break

                # execute trade at best bid price
                trade_qty = min(order.qty, best_bid.qty)
                trade = Trade(
                    ts=order.ts,
                    seq=order.seq,
                    symbol=order.symbol,
                    buy_order_id=best_bid.order_id,
                    sell_order_id=order.order_id,
                    qty=trade_qty,
                    price=best_bid.price,
                    maker_order_id=best_bid.order_id,
                    taker_side=OrderSide.SELL
                )

                trades.append(trade)

                # reduce remaining qty for both sides
                order.qty -= trade_qty
                book.reduce_qty(order_id=best_bid.order_id, qty=trade_qty)

        # if not fully matched, add remaining qty to book
        if order.qty > 0:
            book.add_order(order=order)

        return trades

    @staticmethod
    async def _handle_amend(book: OrderBook, order: AmendOrder) -> None:
        """Handle amendment (price or qty change)."""
        # directly forward to order book
        book.amend_order(order)

    @staticmethod
    async def _handle_cancel(book: OrderBook, order: BaseOrder) -> None:
        """Handle cancel event."""
        # remove order from order book
        book.cancel_order(order.order_id)