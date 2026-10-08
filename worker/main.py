import logging
import time

import pika
from pydantic import ValidationError

from shared.config import settings
from shared.database import create_tables
from shared.dtos import OrderRequestDTO
from shared.repositories.order_repository import OrderRepository
from worker.infrastructure.viacep_client import (
    AddressNotFoundError,
    InvalidAddressResponseError,
    ViaCepClient,
)
from worker.services.order_processor import OrderProcessor

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

order_processor = OrderProcessor(
    address_client=ViaCepClient(),
    order_repository=OrderRepository(),
)


def handle_order_message(
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    body: bytes,
) -> None:
    del properties

    try:
        order = OrderRequestDTO.model_validate_json(body)
    except ValidationError:
        logger.exception("Rejecting invalid order message")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    try:
        order_processor.process(order)
    except (AddressNotFoundError, InvalidAddressResponseError):
        logger.exception("Rejecting order with an invalid destination address")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception:
        logger.exception("Order processing failed; message will be retried")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    else:
        channel.basic_ack(delivery_tag=method.delivery_tag)


def consume_orders() -> None:
    create_tables()

    while True:
        connection = None
        try:
            connection = pika.BlockingConnection(
                pika.URLParameters(settings.rabbitmq_url)
            )
            channel = connection.channel()
            channel.queue_declare(queue=settings.order_queue, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue=settings.order_queue,
                on_message_callback=handle_order_message,
            )
            logger.info("Consuming messages from %s", settings.order_queue)
            channel.start_consuming()
        except pika.exceptions.AMQPError:
            logger.exception("RabbitMQ connection failed; reconnecting in 5 seconds")
            time.sleep(5)
        finally:
            if connection is not None and connection.is_open:
                connection.close()


if __name__ == "__main__":
    consume_orders()
