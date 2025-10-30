import pytest
from engine.core.matcher import Matcher
from common.enums.order import Symbol, OrderSide, OrderType
from common.models.orders import CreateOrder, AmendOrder


@pytest.mark.asyncio
async def test_basic_cross_and_resting_buy():
    matcher = Matcher()

    sell1 = CreateOrder(
        type=OrderType.CREATE,
        ts=1000,
        seq=1,
        symbol=Symbol.ABC,
        side=OrderSide.SELL,
        order_id="S1",
        price=99,
        qty=4
    )
    sell2 = CreateOrder(
        type=OrderType.CREATE,
        ts=1010,
        seq=2,
        symbol=Symbol.ABC,
        side=OrderSide.SELL,
        order_id="S2",
        price=100,
        qty=3
    )

    await matcher.handle_event(sell1)
    await matcher.handle_event(sell2)

    # incoming BUY crosses both partially
    buy = CreateOrder(
        type=OrderType.CREATE,
        ts=1020,
        seq=3,
        symbol=Symbol.ABC,
        side=OrderSide.BUY,
        order_id="B1",
        price=101,
        qty=10
    )
    trades = await matcher.handle_event(buy)

    assert len(trades) == 2
    assert sum(t.qty for t in trades) == 7

    assert trades[0].price == 99
    assert trades[1].price == 100

    book = matcher.books[Symbol.ABC]
    best_bid = book.get_best_bid()
    assert best_bid.qty == 3
    assert best_bid.order_id == "B1"

    assert not book.is_active("S1")
    assert not book.is_active("S2")


@pytest.mark.asyncio
async def test_duplicate_order_ignored():
    matcher = Matcher()

    order = CreateOrder(
        type=OrderType.CREATE,
        ts=1000,
        seq=1,
        symbol=Symbol.XYZ,
        side=OrderSide.BUY,
        order_id="B1",
        price=100,
        qty=5
    )
    await matcher.handle_event(order)

    dup = CreateOrder(
        type=OrderType.CREATE,
        ts=1010,
        seq=2,
        symbol=Symbol.XYZ,
        side=OrderSide.BUY,
        order_id="B1",
        price=101,
        qty=7
    )
    trades = await matcher.handle_event(dup)

    assert trades == []
    book = matcher.books[Symbol.XYZ]
    best_bid = book.get_best_bid()
    assert best_bid.qty == 5
    assert best_bid.price == 100


@pytest.mark.asyncio
async def test_amend_qty_zero_behaves_as_cancel():
    matcher = Matcher()

    order = CreateOrder(
        type=OrderType.CREATE,
        ts=1000,
        seq=1,
        symbol=Symbol.DEF,
        side=OrderSide.SELL,
        order_id="S1",
        price=101,
        qty=10
    )
    await matcher.handle_event(order)

    amend = AmendOrder(
        type=OrderType.AMEND,
        ts=1010,
        seq=2,
        symbol=Symbol.DEF,
        order_id="S1",
        qty=0
    )
    await matcher.handle_event(amend)

    book = matcher.books[Symbol.DEF]
    assert not book.is_active("S1")
