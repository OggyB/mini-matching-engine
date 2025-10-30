from abc import ABC, abstractmethod
from typing import Callable, Awaitable

from nats.aio.msg import Msg


class BaseBroker(ABC):
    def __init__(self):
        """Initialize the base broker."""
        pass

    @abstractmethod
    def connect(self) -> object:
        """Connect to the broker service."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the broker connection."""
        pass

    @abstractmethod
    def publish(self, subject: None | str, message: None | bytes | dict) -> None:
        """Publish a message to the broker."""
        pass

    @abstractmethod
    def subscribe(self, subject: None | str, handler: Callable[[Msg], Awaitable[None]] | None) -> None:
        """Subscribe to a broker topic with a message handler."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check the broker connection health."""
        pass