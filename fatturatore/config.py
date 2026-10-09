from __future__ import annotations

import json
import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import NotRequired, TypedDict, cast


@dataclass(frozen=True)
class Address:
    street: str
    number: str
    postal_code: str
    city: str
    province: str
    country: str = "IT"


@dataclass(frozen=True)
class Person:
    vat_number: str
    tax_code: str
    first_name: str
    last_name: str
    tax_regime: str
    address: Address


@dataclass(frozen=True)
class Company:
    vat_number: str
    tax_code: str
    name: str
    recipient_code: str
    pec: str
    address: Address


class AddressConfig(TypedDict):
    street: str
    number: str
    postal_code: str
    city: str
    province: str
    country: NotRequired[str]


class SellerConfig(TypedDict):
    vat_number: str
    tax_code: str
    first_name: str
    last_name: str
    tax_regime: str
    address: AddressConfig


class CustomerConfig(TypedDict):
    vat_number: str
    tax_code: str
    name: str
    recipient_code: str
    pec: str
    address: AddressConfig


class InvoiceConfig(TypedDict):
    description: str
    social_security_rate: str
    stamp_duty: str
    vat_nature: str
    reasons: list[str]
    tax_reference: str


class LocalConfig(TypedDict):
    seller: SellerConfig
    customer: CustomerConfig
    invoice: InvoiceConfig


def _address(data: AddressConfig) -> Address:
    return Address(
        street=data["street"],
        number=data["number"],
        postal_code=data["postal_code"],
        city=data["city"],
        province=data["province"],
        country=data.get("country", "IT"),
    )


def _load_local_config() -> LocalConfig:
    default_path = Path(__file__).resolve().parent.parent / "fatturatore.local.json"
    path = Path(os.environ.get("FATTURATORE_CONFIG", default_path))
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"configurazione locale mancante: copia fatturatore.example.json in {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"JSON non valido in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON non valido in {path}: atteso un oggetto")
    return cast(LocalConfig, payload)


try:
    _CONFIG = _load_local_config()
    _SELLER = _CONFIG["seller"]
    _CUSTOMER = _CONFIG["customer"]
    _INVOICE = _CONFIG["invoice"]

    SELLER = Person(
        vat_number=_SELLER["vat_number"],
        tax_code=_SELLER["tax_code"],
        first_name=_SELLER["first_name"],
        last_name=_SELLER["last_name"],
        tax_regime=_SELLER["tax_regime"],
        address=_address(_SELLER["address"]),
    )
    CUSTOMER = Company(
        vat_number=_CUSTOMER["vat_number"],
        tax_code=_CUSTOMER["tax_code"],
        name=_CUSTOMER["name"],
        recipient_code=_CUSTOMER["recipient_code"],
        pec=_CUSTOMER["pec"],
        address=_address(_CUSTOMER["address"]),
    )
    DESCRIPTION = _INVOICE["description"]
    SOCIAL_SECURITY_RATE = Decimal(_INVOICE["social_security_rate"])
    STAMP_DUTY = Decimal(_INVOICE["stamp_duty"])
    VAT_NATURE = _INVOICE["vat_nature"]
    REASONS = tuple(_INVOICE["reasons"])
    TAX_REFERENCE = _INVOICE["tax_reference"]
except (KeyError, TypeError, ValueError) as exc:
    raise RuntimeError("configurazione locale incompleta o non valida") from exc
