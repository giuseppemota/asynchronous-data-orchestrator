import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from api.infrastructure.order_publisher import (
    MessageBrokerUnavailableError,
    RabbitMQOrderPublisher,
)
from api.schemas import OrderAcceptedDTO, OrderResponseDTO
from api.services.order_service import OrderNotFoundError, OrderService
from shared.dtos import OrderRequestDTO
from shared.repositories.order_repository import OrderRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders", tags=["orders"])
order_service = OrderService(
    publisher=RabbitMQOrderPublisher(),
    repository=OrderRepository(),
)


@router.post(
    "",
    response_model=OrderAcceptedDTO,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_order(payload: OrderRequestDTO) -> OrderAcceptedDTO:
    try:
        order_service.submit(payload)
    except MessageBrokerUnavailableError as exc:
        logger.exception("Could not publish order %s", payload.order_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Order queue is temporarily unavailable",
        ) from exc

    return OrderAcceptedDTO(order_id=payload.order_id, status="ACCEPTED")


@router.get("/{order_id}", response_model=OrderResponseDTO)
def get_order(order_id: str) -> OrderResponseDTO:
    try:
        return order_service.get_by_id(order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        ) from exc
    except SQLAlchemyError as exc:
        logger.exception("Could not query order %s", order_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Order database is temporarily unavailable",
        ) from exc
