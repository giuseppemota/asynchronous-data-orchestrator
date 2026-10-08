import pytest
from pydantic import ValidationError

from shared.dtos import OrderRequestDTO, ViaCepAddressDTO


def test_order_request_dto_validates_nested_payload() -> None:
    order = OrderRequestDTO.model_validate(
        {
            "order_id": "order-123",
            "items_total": 42.50,
            "customer": {
                "customer_id": "customer-123",
                "name": "Ana Silva",
                "email": "ana@example.com",
            },
            "shipping": {"cep": "01001-000"},
        }
    )

    assert order.order_id == "order-123"
    assert order.customer.customer_id == "customer-123"
    assert order.shipping.cep == "01001-000"


def test_order_request_dto_rejects_invalid_cep() -> None:
    with pytest.raises(ValidationError):
        OrderRequestDTO.model_validate(
            {
                "order_id": "order-123",
                "items_total": 42.50,
                "customer": {
                    "customer_id": "customer-123",
                    "name": "Ana Silva",
                    "email": "ana@example.com",
                },
                "shipping": {"cep": "invalid"},
            }
        )


def test_viacep_address_dto_preserves_structured_fields() -> None:
    address = ViaCepAddressDTO.model_validate(
        {
            "logradouro": "Praça da Sé",
            "bairro": "Sé",
            "localidade": "São Paulo",
            "uf": "SP",
        }
    )

    assert address.logradouro == "Praça da Sé"
    assert address.localidade == "São Paulo"
    assert address.uf == "SP"
