import asyncio
import signal
from loguru import logger

from common.config.config import settings
from common.broker.nats_broker import NATSBroker
from common.utils.file_manager import FileManager


async def publish_orders(broker: NATSBroker, file_manager: FileManager):
    orders = file_manager.read_json()

    if not orders:
        logger.warning("No orders found to publish.")
        return

    logger.info(f"Loaded {len(orders)} orders from file.")

    for idx, order in enumerate(orders, start=1):
        try:
            await broker.publish(subject=settings.nats.orders_subject, message=order)
            logger.info(f"[{idx}] Published order: {order}")
        except Exception as e:
            logger.error(f"Failed to publish order #{idx}: {e}")

        await asyncio.sleep(0.2)


async def main():
    file_manager = FileManager(settings.engine.input_path)
    broker = NATSBroker(settings.nats)
    await broker.connect()
    logger.info(f"Connected to NATS at {settings.nats.url}")

    stop_event = asyncio.Event()

    async def shutdown():
        logger.info("Shutting down gracefully.")
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown()))

    try:
        await publish_orders(broker, file_manager)
        logger.info("All orders published successfully.")
    except asyncio.CancelledError:
        logger.warning("Publishing interrupted by cancel request.")
    finally:
        await broker.close()
        logger.info("NATS connection closed.")

    await stop_event.wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Interrupted manually. Exiting.")
