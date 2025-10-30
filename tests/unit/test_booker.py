import pytest
from common.enums.order import OrderSide, Symbol, OrderType
from common.models.orders import CreateOrder, AmendOrder
from engine.core.booker import OrderBook


@pytest.fixture
def order_book():
    return OrderBook(Symbol.ABC)


@pytest.fixture
def sample_buy_order():
    return CreateOrder(
        type=OrderType.CREATE,
        ts=1000,
        seq=1,
        symbol=Symbol.ABC,
        side=OrderSide.BUY,
        order_id="B1",
        price=100,
        qty=10
    )


@pytest.fixture
def sample_sell_order():
    return CreateOrder(
        type=OrderType.CREATE,
        ts=1001,
        seq=2,
        symbol=Symbol.ABC,
        side=OrderSide.SELL,
        order_id="S1",
        price=101,
        qty=5
    )


def test_add_order_creates_lookup_entry(order_book, sample_buy_order):
    order_book.add_order(sample_buy_order)
    assert order_book.is_active("B1")
    assert order_book.get_best_bid().price == 100
    assert order_book.get_best_bid().qty == 10


def test_best_bid_and_ask(order_book, sample_buy_order, sample_sell_order):
    order_book.add_order(sample_buy_order)
    order_book.add_order(sample_sell_order)
    best_bid = order_book.get_best_bid()
    best_ask = order_book.get_best_ask()

    assert best_bid.price == 100
    assert best_bid.side == OrderSide.BUY
    assert best_ask.price == 101
    assert best_ask.side == OrderSide.SELL


def test_cancel_order_removes_from_lookup(order_book, sample_buy_order):
    order_book.add_order(sample_buy_order)
    order_book.cancel_order("B1")

    assert not order_book.is_active("B1")
    assert order_book.get_best_bid() is None


def test_amend_order_qty(order_book, sample_buy_order):
    order_book.add_order(sample_buy_order)

    amend = AmendOrder(
        type=OrderType.AMEND,
        ts=1002,
        seq=3,
        symbol=Symbol.ABC,
        order_id="B1",
        qty=5
    )

    updated = order_book.amend_order(amend)
    assert updated.qty == 5
    assert order_book.lookup["B1"].qty == 5


def test_amend_order_price(order_book, sample_buy_order):
    order_book.add_order(sample_buy_order)

    amend = AmendOrder(
        type=OrderType.AMEND,
        ts=1003,
        seq=4,
        symbol=Symbol.ABC,
        order_id="B1",
        price=105
    )

    updated = order_book.amend_order(amend)
    assert updated.price == 105
    assert 105 in order_book.bids
    assert 100 not in order_book.bids


def test_reduce_qty_removes_when_zero(order_book, sample_buy_order):
    order_book.add_order(sample_buy_order)
    order_book.reduce_qty("B1", 10)

    assert not order_book.is_active("B1")
    assert order_book.get_best_bid() is None


def test_insert_multiple_bids_price_time_priority(order_book):
    o1 = CreateOrder(type=OrderType.CREATE, ts=1000, seq=1, symbol=Symbol.ABC,
                     side=OrderSide.BUY, order_id="B1", price=100, qty=5)
    o2 = CreateOrder(type=OrderType.CREATE, ts=1001, seq=2, symbol=Symbol.ABC,
                     side=OrderSide.BUY, order_id="B2", price=101, qty=5)
    o3 = CreateOrder(type=OrderType.CREATE, ts=1002, seq=3, symbol=Symbol.ABC,
                     side=OrderSide.BUY, order_id="B3", price=100, qty=5)

    order_book.add_order(o1)
    order_book.add_order(o2)
    order_book.add_order(o3)

    assert order_book.get_best_bid().order_id == "B2"

    dq = order_book.bids[100]
    assert [o.order_id for o in dq] == ["B1", "B3"]
