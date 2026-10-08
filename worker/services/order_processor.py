import logging

from shared.config import settings
from shared.dtos import OrderRequestDTO
from shared.repositories.order_repository import OrderRepository
from worker.infrastructure.viacep_client import ViaCepClient

logger = logging.getLogger(__name__)


class OrderProcessor:
    def __init__(
        self,
        address_client: ViaCepClient,
        order_repository: OrderRepository,
    ) -> None:
        self._address_client = address_client
        self._order_repository = order_repository

    def process(self, order: OrderRequestDTO) -> None:
        cep = order.shipping.cep.replace("-", "")
        address = self._address_client.get_address(cep)
        self._order_repository.save_completed(
            order=order,
            cep=cep,
            address=address,
            shipping_cost=settings.shipping_cost,
        )
        logger.info("Order %s processed successfully", order.order_id)
