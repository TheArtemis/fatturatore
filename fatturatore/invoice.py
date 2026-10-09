from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from .config import (
    CUSTOMER,
    DESCRIPTION,
    REASONS,
    SELLER,
    SOCIAL_SECURITY_RATE,
    STAMP_DUTY,
    TAX_REFERENCE,
    VAT_NATURE,
    Address,
)

NS = "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2"
DS_NS = "http://www.w3.org/2000/09/xmldsig#"
CENT = Decimal("0.01")

ET.register_namespace("p", NS)
ET.register_namespace("ds", DS_NS)


@dataclass(frozen=True)
class InvoiceAmounts:
    gross: Decimal
    total: Decimal
    fee: Decimal
    social_security: Decimal
    taxable_total: Decimal
    stamp_duty: Decimal
    rounding: Decimal


def parse_amount(raw: str) -> Decimal:
    """Parse common Italian and international currency notations."""
    value = raw.strip().replace("€", "").replace(" ", "").replace("'", "")
    if not value:
        raise ValueError("l'importo non può essere vuoto")

    if "," in value and "." in value:
        decimal_separator = "," if value.rfind(",") > value.rfind(".") else "."
        thousands_separator = "." if decimal_separator == "," else ","
        value = value.replace(thousands_separator, "").replace(decimal_separator, ".")
    elif "," in value:
        value = _normalise_single_separator(value, ",")
    elif "." in value:
        value = _normalise_single_separator(value, ".")

    if not re.fullmatch(r"\+?\d+(?:\.\d{1,2})?", value):
        raise ValueError(f"importo non valido: {raw!r}")

    try:
        amount = Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError(f"importo non valido: {raw!r}") from exc

    if amount <= 0:
        raise ValueError("il lordo deve essere maggiore di zero")
    return amount


def _normalise_single_separator(value: str, separator: str) -> str:
    if value.count(separator) > 1:
        parts = value.split(separator)
        if all(len(part) == 3 for part in parts[1:]):
            return "".join(parts)
        return value

    integer, fraction = value.split(separator)
    if len(fraction) == 3 and 1 <= len(integer) <= 3:
        return integer + fraction
    return integer + "." + fraction


def calculate_amounts(gross: Decimal) -> InvoiceAmounts:
    """Split a stamp-duty-exclusive gross into fee and 4% INPS contribution."""
    gross = gross.quantize(CENT, rounding=ROUND_HALF_UP)
    approximate_fee = (gross / (Decimal("1") + SOCIAL_SECURITY_RATE / 100)).quantize(
        CENT,
        rounding=ROUND_HALF_UP,
    )

    candidates: list[tuple[Decimal, Decimal, Decimal]] = []
    for offset in range(-3, 4):
        fee = approximate_fee + CENT * offset
        contribution = (fee * SOCIAL_SECURITY_RATE / 100).quantize(
            CENT,
            rounding=ROUND_HALF_UP,
        )
        rounding = gross - fee - contribution
        candidates.append((abs(rounding), fee, contribution))

    _, fee, contribution = min(candidates, key=lambda candidate: candidate[0])
    rounding = (gross - fee - contribution).quantize(CENT)
    if abs(rounding) > CENT:
        raise ValueError("impossibile ripartire il totale con una rivalsa INPS del 4%")

    return InvoiceAmounts(
        gross=gross,
        total=gross + STAMP_DUTY,
        fee=fee,
        social_security=contribution,
        taxable_total=fee + contribution,
        stamp_duty=STAMP_DUTY,
        rounding=rounding,
    )


def build_invoice_xml(
    amounts: InvoiceAmounts,
    invoice_date: date,
    invoice_number: str,
    transmission_number: str,
) -> bytes:
    root = ET.Element(f"{{{NS}}}FatturaElettronica", {"versione": "FPR12"})
    header = ET.SubElement(root, _tag("FatturaElettronicaHeader"))
    _add_transmission_data(header, transmission_number)
    _add_seller(header)
    _add_customer(header)

    body = ET.SubElement(root, _tag("FatturaElettronicaBody"))
    _add_general_data(body, amounts, invoice_date, invoice_number)
    _add_goods_and_services(body, amounts)

    ET.indent(root, space="  ")
    xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    # ASCII is valid UTF-8; numeric references preserve accents even if misdecoded.
    return xml.decode("utf-8").encode("ascii", errors="xmlcharrefreplace")


def _tag(name: str) -> str:
    # Lo schema FatturaPA qualifica l'elemento globale radice, ma non i figli locali.
    return name


def _element(parent: ET.Element, name: str, value: object | None = None) -> ET.Element:
    child = ET.SubElement(parent, _tag(name))
    if value is not None:
        child.text = str(value)
    return child


def _money(value: Decimal) -> str:
    return f"{value.quantize(CENT):.2f}"


def _add_fiscal_id(parent: ET.Element, vat_number: str) -> None:
    fiscal_id = _element(parent, "IdFiscaleIVA")
    _element(fiscal_id, "IdPaese", "IT")
    _element(fiscal_id, "IdCodice", vat_number)


def _add_address(parent: ET.Element, address: Address) -> None:
    location = _element(parent, "Sede")
    _element(location, "Indirizzo", address.street)
    _element(location, "NumeroCivico", address.number)
    _element(location, "CAP", address.postal_code)
    _element(location, "Comune", address.city)
    _element(location, "Provincia", address.province)
    _element(location, "Nazione", address.country)


def _add_transmission_data(header: ET.Element, transmission_number: str) -> None:
    data = _element(header, "DatiTrasmissione")
    transmitter = _element(data, "IdTrasmittente")
    _element(transmitter, "IdPaese", "IT")
    _element(transmitter, "IdCodice", SELLER.tax_code)
    _element(data, "ProgressivoInvio", transmission_number)
    _element(data, "FormatoTrasmissione", "FPR12")
    _element(data, "CodiceDestinatario", CUSTOMER.recipient_code)
    _element(data, "PECDestinatario", CUSTOMER.pec)


def _add_seller(header: ET.Element) -> None:
    seller = _element(header, "CedentePrestatore")
    registry = _element(seller, "DatiAnagrafici")
    _add_fiscal_id(registry, SELLER.vat_number)
    _element(registry, "CodiceFiscale", SELLER.tax_code)
    personal_data = _element(registry, "Anagrafica")
    _element(personal_data, "Nome", SELLER.first_name)
    _element(personal_data, "Cognome", SELLER.last_name)
    _element(registry, "RegimeFiscale", SELLER.tax_regime)
    _add_address(seller, SELLER.address)


def _add_customer(header: ET.Element) -> None:
    customer = _element(header, "CessionarioCommittente")
    registry = _element(customer, "DatiAnagrafici")
    _add_fiscal_id(registry, CUSTOMER.vat_number)
    _element(registry, "CodiceFiscale", CUSTOMER.tax_code)
    company_data = _element(registry, "Anagrafica")
    _element(company_data, "Denominazione", CUSTOMER.name)
    _add_address(customer, CUSTOMER.address)


def _add_general_data(
    body: ET.Element,
    amounts: InvoiceAmounts,
    invoice_date: date,
    invoice_number: str,
) -> None:
    general = _element(body, "DatiGenerali")
    document = _element(general, "DatiGeneraliDocumento")
    _element(document, "TipoDocumento", "TD01")
    _element(document, "Divisa", "EUR")
    _element(document, "Data", invoice_date.isoformat())
    _element(document, "Numero", invoice_number)

    stamp = _element(document, "DatiBollo")
    _element(stamp, "BolloVirtuale", "SI")
    _element(stamp, "ImportoBollo", _money(amounts.stamp_duty))

    social_security = _element(document, "DatiCassaPrevidenziale")
    _element(social_security, "TipoCassa", "TC22")
    _element(social_security, "AlCassa", _money(SOCIAL_SECURITY_RATE))
    _element(
        social_security,
        "ImportoContributoCassa",
        _money(amounts.social_security),
    )
    _element(social_security, "ImponibileCassa", _money(amounts.fee))
    _element(social_security, "AliquotaIVA", "0.00")
    _element(social_security, "Natura", VAT_NATURE)

    _element(document, "ImportoTotaleDocumento", _money(amounts.total))
    if amounts.rounding:
        _element(document, "Arrotondamento", _money(amounts.rounding))
    for reason in REASONS:
        _element(document, "Causale", reason)


def _add_goods_and_services(body: ET.Element, amounts: InvoiceAmounts) -> None:
    goods = _element(body, "DatiBeniServizi")
    line = _element(goods, "DettaglioLinee")
    _element(line, "NumeroLinea", "1")
    _element(line, "Descrizione", DESCRIPTION)
    _element(line, "Quantita", "1.00")
    _element(line, "PrezzoUnitario", _money(amounts.fee))
    _element(line, "PrezzoTotale", _money(amounts.fee))
    _element(line, "AliquotaIVA", "0.00")
    _element(line, "Natura", VAT_NATURE)

    summary = _element(goods, "DatiRiepilogo")
    _element(summary, "AliquotaIVA", "0.00")
    _element(summary, "Natura", VAT_NATURE)
    _element(summary, "ImponibileImporto", _money(amounts.taxable_total))
    _element(summary, "Imposta", "0.00")
    _element(summary, "RiferimentoNormativo", TAX_REFERENCE)
