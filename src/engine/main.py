import asyncio
import json
import signal
from typing import List, Optional

from common.config.config import settings
from common.broker.nats_broker import NATSBroker
from common.enums.order import OrderType
from common.models.orders import BaseOrder, CreateOrder, AmendOrder
from common.models.trade import Trade
from common.utils.file_manager import FileManager
from engine.core.matcher import Matcher
from loguru import logger

async def handle_message(msg, matcher: Matcher, broker: NATSBroker, file_manager: FileManager) -> Optional[List[Trade]]:
    try:
        data = json.loads(msg.data.decode())
        order_type = data['type']
        if order_type == OrderType.CREATE.value:
            order = CreateOrder.model_validate(data)
        elif order_type == OrderType.AMEND.value:
            order = AmendOrder.model_validate(data)
        elif order_type == OrderType.CANCEL.value:
            order = BaseOrder.model_validate(data)
        else:
            logger.warning(f"Unexpected type is detected. skipping.")
            return None

        trades = await matcher.handle_event(order=order)
        if trades:
            for trade in trades:
                trade_json = trade.model_dump_json()
                logger.info(f"Trade is created. data: {trade_json}")
                await broker.publish(subject=settings.nats.trades_subject, message=trade)
                file_manager.write_json(trade.model_dump())
        return trades

    except Exception as e:
        logger.error(f"Failed to process message. error : {e}")
        return None


async def main():
    file_manager = FileManager(settings.engine.output_path)
    broker = NATSBroker(settings.nats)
    await broker.connect()
    matcher = Matcher()

    async def on_message(msg):
        await handle_message(msg, matcher, broker, file_manager)

    await broker.subscribe(settings.nats.orders_subject, handler=on_message)
    logger.info(f"Mini matching engine started, listening on: {settings.nats.orders_subject}", features="f-strings" )

    stop_event = asyncio.Event()

    def _signal_handler():
        logger.info("Shutting down gracefully...")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_event_loop().add_signal_handler(sig, lambda s=sig: _signal_handler())

    await stop_event.wait()
    await broker.close()
    logger.info("NATS connection closed.")



if __name__ == '__main__':
    asyncio.run(main())