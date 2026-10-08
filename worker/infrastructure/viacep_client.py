import requests
from pydantic import ValidationError

from shared.config import settings
from shared.dtos import ViaCepAddressDTO


class AddressNotFoundError(Exception):
    """Raised when ViaCEP does not have an address for the requested CEP."""


class InvalidAddressResponseError(Exception):
    """Raised when ViaCEP returns an unusable response."""


class ViaCepClient:
    def get_address(self, cep: str) -> ViaCepAddressDTO:
        response = requests.get(
            f"{settings.viacep_base_url.rstrip('/')}/{cep}/json/",
            timeout=10,
        )
        response.raise_for_status()

        try:
            address = ViaCepAddressDTO.model_validate_json(response.content)
        except ValidationError as exc:
            raise InvalidAddressResponseError(
                "ViaCEP returned an invalid address response"
            ) from exc

        if address.erro:
            raise AddressNotFoundError(f"CEP {cep} was not found by ViaCEP")
        if not address.localidade or not address.uf:
            raise InvalidAddressResponseError(
                f"ViaCEP returned incomplete address data for CEP {cep}"
            )

        return address
