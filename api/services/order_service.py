from api.infrastructure.order_publisher import RabbitMQOrderPublisher
from api.schemas import OrderResponseDTO, OrderShippingDTO
from shared.dtos import OrderRequestDTO
from shared.repositories.order_repository import OrderRepository


class OrderNotFoundError(Exception):
    """Raised when an order does not exist."""


class OrderService:
    def __init__(
        self,
        publisher: RabbitMQOrderPublisher,
        repository: OrderRepository,
    ) -> None:
        self._publisher = publisher
        self._repository = repository

    def submit(self, order: OrderRequestDTO) -> None:
        self._publisher.publish(order)

    def get_by_id(self, order_id: str) -> OrderResponseDTO:
        order = self._repository.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)

        return OrderResponseDTO(
            order_id=order.id_pedido,
            customer_id=order.customer_id,
            shipping=OrderShippingDTO(
                cep=order.cep_destino,
                logradouro=order.logradouro,
                complemento=order.complemento,
                bairro=order.bairro,
                cidade=order.cidade,
                estado=order.estado,
            ),
            items_total=order.valor_total - order.valor_frete,
            shipping_cost=order.valor_frete,
            total=order.valor_total,
            status=order.status,
        )
