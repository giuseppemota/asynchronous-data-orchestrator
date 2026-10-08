from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id_cliente: Mapped[str] = mapped_column(String, primary_key=True)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)


class Order(Base):
    __tablename__ = "orders"

    id_pedido: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String, ForeignKey("customers.id_cliente"), nullable=False
    )
    cep_destino: Mapped[str] = mapped_column(String, nullable=False)
    logradouro: Mapped[str | None] = mapped_column(String, nullable=True)
    complemento: Mapped[str | None] = mapped_column(String, nullable=True)
    bairro: Mapped[str | None] = mapped_column(String, nullable=True)
    cidade: Mapped[str] = mapped_column(String, nullable=False)
    estado: Mapped[str] = mapped_column(String, nullable=False)
    valor_frete: Mapped[float] = mapped_column(Float, nullable=False)
    valor_total: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
