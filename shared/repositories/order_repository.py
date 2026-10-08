from sqlalchemy.dialects.postgresql import insert

from shared.database import SessionLocal
from shared.dtos import OrderRequestDTO, ViaCepAddressDTO
from shared.models import Customer, Order


class OrderRepository:
    def get_by_id(self, order_id: str) -> Order | None:
        with SessionLocal() as session:
            return session.get(Order, order_id)

    def save_completed(
        self,
        order: OrderRequestDTO,
        cep: str,
        address: ViaCepAddressDTO,
        shipping_cost: float,
    ) -> None:
        customer_id = order.customer.customer_id

        with SessionLocal.begin() as session:
            customer_insert = insert(Customer).values(
                id_cliente=customer_id,
                nome=order.customer.name,
                email=order.customer.email,
            )
            session.execute(
                customer_insert.on_conflict_do_nothing(index_elements=["id_cliente"])
            )

            order_insert = insert(Order).values(
                id_pedido=order.order_id,
                customer_id=customer_id,
                cep_destino=address.cep or cep,
                logradouro=address.logradouro,
                complemento=address.complemento,
                bairro=address.bairro,
                cidade=address.localidade,
                estado=address.uf,
                valor_frete=shipping_cost,
                valor_total=order.items_total + shipping_cost,
                status="COMPLETED",
            )
            session.execute(
                order_insert.on_conflict_do_update(
                    index_elements=["id_pedido"],
                    set_={
                        "customer_id": order_insert.excluded.customer_id,
                        "cep_destino": order_insert.excluded.cep_destino,
                        "logradouro": order_insert.excluded.logradouro,
                        "complemento": order_insert.excluded.complemento,
                        "bairro": order_insert.excluded.bairro,
                        "cidade": order_insert.excluded.cidade,
                        "estado": order_insert.excluded.estado,
                        "valor_frete": order_insert.excluded.valor_frete,
                        "valor_total": order_insert.excluded.valor_total,
                        "status": order_insert.excluded.status,
                    },
                )
            )
