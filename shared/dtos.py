from pydantic import BaseModel, ConfigDict, Field


class CustomerDTO(BaseModel):
    customer_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    email: str = Field(min_length=1)


class ShippingDTO(BaseModel):
    cep: str = Field(pattern=r"^\d{5}-?\d{3}$")


class OrderRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str = Field(min_length=1)
    items_total: float = Field(ge=0, allow_inf_nan=False)
    customer: CustomerDTO
    shipping: ShippingDTO


class ViaCepAddressDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    logradouro: str | None = None
    complemento: str | None = None
    bairro: str | None = None
    localidade: str | None = None
    uf: str | None = None
    cep: str | None = None
    erro: bool = False
