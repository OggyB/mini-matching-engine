import asyncio
import json
from typing import Callable, Awaitable

from pydantic import BaseModel

from common.broker.base import BaseBroker
from nats.aio.client import Client
from nats.aio.msg import Msg
from loguru import logger

from common.models.config import NatsConfig


class NATSBroker(BaseBroker):
    """
    A simple NATS message broker.

    Handles connection, publishing, subscribing, and health checks
    for a NATS server.
    """
    def __init__(self, cfg: NatsConfig):
        """Initialize the NATS broker with given configuration."""
        super().__init__()
        self.client: Client | None = None
        self.config: NatsConfig = cfg

    async def connect(self) -> Client:
        """Connect to the NATS server."""
        if self.client and self.client.is_connected:
            logger.info("NATS client is already connected.")
            return self.client
        self.client = Client()

        try:
            await self.client.connect(
                servers=[self.config.url],
                max_reconnect_attempts=self.config.connection.max_reconnect_attempts,
                reconnect_time_wait=self.config.connection.reconnect_wait_ms,
                connect_timeout=self.config.connection.timeout_ms
            )

            logger.info(f"Connected NATS server, url: {self.config.url}" ,feature="f-strings")


        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}", feature="f-strings")
            raise

        return self.client

    async def close(self) -> None:
        """Close the NATS connection safely."""
        if self.client:
            try:
                if self.client.is_connected:
                    await asyncio.wait_for(self.client.drain(), timeout=5)

                logger.info("Connection closed successfully")

            except asyncio.TimeoutError:
                logger.warning("NATS drain timeout — forcing close.")
                await self.client.close()

            except Exception as e:
                logger.warning(f"Error while closing NATS connection: {e}")

    async def publish(self, subject: str, message: dict | bytes | BaseModel) -> None:
        """Publish a message to a NATS subject."""

        if not self.client or not self.client.is_connected:
            logger.warning("NATS not connected, attempting reconnect before publish...")
            await self.connect()
        try:
            if hasattr(message, "model_dump_json"):
                payload = message.model_dump_json().encode()
            elif isinstance(message, dict):
                payload = json.dumps(message).encode()
            elif isinstance(message, bytes):
                payload = message
            else:
                logger.error("Message could not published.")
                raise TypeError("Message must be dict, bytes, or Pydantic model")

            await self.client.publish(subject=subject, payload=payload)

        except Exception as e:
            logger.error(f"Failed to publish message to {subject}: {e}")
            raise

    async def subscribe(self, subject: str, handler: Callable[[Msg], Awaitable[None]]) -> None:
        """Subscribe to a NATS subject with a message handler."""
        if not self.client or not self.client.is_connected:
            await self.connect()

        try:
            await self.client.subscribe(subject, cb=handler)
            logger.info(f"Subscribed to subject: {subject}")
        except Exception as e:
            logger.error(f"Failed to subscribe to {subject}: {e}")
            raise

    async def health_check(self) -> bool:
        """Check the NATS connection health."""
        if not self.client:
            logger.warning(f"NATS client is not found.")
            raise

        if not self.client.is_connected:
            logger.warning(f"NATS client is not connected.")
            raise

        try:
            await self.client.flush(1)
            logger.info("NATS health check: OK")
            return True
        except Exception as e:
            logger.error(f"Health check was unsuccessful {e}", features="f-strings")
            return False

