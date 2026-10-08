import logging
import time

import pika

from shared.config import settings
from shared.dtos import OrderRequestDTO

logger = logging.getLogger(__name__)


class MessageBrokerUnavailableError(Exception):
    """Raised when RabbitMQ cannot accept an order message."""


class RabbitMQOrderPublisher:
    def publish(self, order: OrderRequestDTO) -> None:
        parameters = pika.URLParameters(settings.rabbitmq_url)
        message = order.model_dump_json().encode("utf-8")
        last_error: pika.exceptions.AMQPError | None = None

        for attempt in range(1, 16):
            try:
                self._publish_once(parameters, message)
                return
            except pika.exceptions.AMQPError as exc:
                last_error = exc
                if attempt < 15:
                    logger.warning(
                        "RabbitMQ unavailable (attempt %s/15); retrying",
                        attempt,
                    )
                    time.sleep(2)

        raise MessageBrokerUnavailableError(
            "Could not publish order after 15 attempts"
        ) from last_error

    @staticmethod
    def _publish_once(
        parameters: pika.URLParameters,
        message: bytes,
    ) -> None:
        connection = pika.BlockingConnection(parameters)
        try:
            channel = connection.channel()
            channel.queue_declare(queue=settings.order_queue, durable=True)
            channel.basic_publish(
                exchange="",
                routing_key=settings.order_queue,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=pika.DeliveryMode.Persistent,
                    content_type="application/json",
                ),
            )
        finally:
            connection.close()
