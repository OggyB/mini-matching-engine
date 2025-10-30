from abc import ABC, abstractmethod
from typing import Callable, Awaitable

from nats.aio.msg import Msg


class BaseBroker(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def publish(self, subject: None | str, message: None | bytes | dict):
        pass

    @abstractmethod
    def subscribe(self, subject: None | str, handler: Callable[[Msg], Awaitable[None]] | None):
        pass

    @abstractmethod
    def health_check(self):
        pass