import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    rabbitmq_url: str
    order_queue: str
    viacep_base_url: str
    shipping_cost: float
    log_level: str

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            database_url=os.getenv(
                "DATABASE_URL",
                "postgresql+psycopg2://postgres:postgres@localhost:5432/orderdb",
            ),
            rabbitmq_url=os.getenv(
                "RABBITMQ_URL",
                "amqp://guest:guest@localhost:5672/%2F",
            ),
            order_queue=os.getenv("ORDER_QUEUE", "order_queue"),
            viacep_base_url=os.getenv("VIACEP_BASE_URL", "https://viacep.com.br/ws"),
            shipping_cost=float(os.getenv("SHIPPING_COST", "15.00")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


settings = Settings.from_environment()
