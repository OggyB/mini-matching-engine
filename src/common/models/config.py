from pydantic import BaseModel
from common.enums.nats import NatsSubject


class NatsConnectionConfig(BaseModel):
    reconnect: bool = True
    max_reconnect_attempts: int = 5
    reconnect_wait_ms: int = 500
    timeout_ms: int = 2000

class NatsConfig(BaseModel):
    url: str = "nats://localhost:4222"
    orders_subject: NatsSubject = NatsSubject.ORDERS_IN
    consume_subject: NatsSubject = NatsSubject.ORDERS_IN
    trades_subject: NatsSubject = NatsSubject.TRADES_OUT
    connection: NatsConnectionConfig = NatsConnectionConfig()


class EngineConfig(BaseModel):
    input_path: str | None = None
    output_path: str | None = None


class Settings(BaseModel):
    nats: NatsConfig
    engine: EngineConfig
