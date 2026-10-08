import json

import pytest

from worker.infrastructure.viacep_client import (
    AddressNotFoundError,
    ViaCepClient,
)


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.content = json.dumps(payload).encode("utf-8")

    def raise_for_status(self) -> None:
        pass


def test_viacep_client_returns_typed_address(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, timeout: int) -> FakeResponse:
        assert url.endswith("/01001000/json/")
        assert timeout == 10
        return FakeResponse(
            {
                "logradouro": "Praça da Sé",
                "bairro": "Sé",
                "localidade": "São Paulo",
                "uf": "SP",
            }
        )

    monkeypatch.setattr("worker.infrastructure.viacep_client.requests.get", fake_get)

    address = ViaCepClient().get_address("01001000")

    assert address.localidade == "São Paulo"
    assert address.uf == "SP"


def test_viacep_client_rejects_unknown_cep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "worker.infrastructure.viacep_client.requests.get",
        lambda url, timeout: FakeResponse({"erro": True}),
    )

    with pytest.raises(AddressNotFoundError):
        ViaCepClient().get_address("99999999")
