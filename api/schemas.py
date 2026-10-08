from typing import Literal

from pydantic import BaseModel


class OrderAcceptedDTO(BaseModel):
    order_id: str
    status: Literal["ACCEPTED"]


class OrderShippingDTO(BaseModel):
    cep: str
    logradouro: str | None
    complemento: str | None
    bairro: str | None
    cidade: str
    estado: str


class OrderResponseDTO(BaseModel):
    order_id: str
    customer_id: str
    shipping: OrderShippingDTO
    items_total: float
    shipping_cost: float
    total: float
    status: str
