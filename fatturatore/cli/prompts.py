from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

from ..config import CUSTOMER, DESCRIPTION, SELLER
from ..invoice import InvoiceAmounts, parse_amount
from .constants import BLUE, BOLD, CYAN, GREEN, RED, YELLOW
from .parser import parse_date
from .style import format_eur, print_banner, prompt_style, style, summary_row


def prompt_for_gross() -> Decimal:
    print_banner()
    print(style("\n  Generatore XML FatturaPA\n", CYAN, BOLD))
    while True:
        try:
            raw = input(
                prompt_style("  Importo lordo", BLUE, BOLD)
                + " (compenso + INPS 4%, bollo escluso): "
            )
        except (EOFError, KeyboardInterrupt) as exc:
            print(style("\n⚠ Operazione annullata.", YELLOW, BOLD), file=sys.stderr)
            raise ValueError("nessun importo inserito") from exc
        try:
            return parse_amount(raw)
        except ValueError as exc:
            print(style(f"  ✗ Importo non valido: {exc}. Riprova.", RED), file=sys.stderr)


def prompt_for_invoice_date(today: date | None = None) -> date:
    today = today or date.today()
    while True:
        try:
            answer = input(
                prompt_style("  Usare la data di oggi", BLUE, BOLD)
                + f" ({today.strftime('%d/%m/%Y')})? "
                + prompt_style("[S/n]", YELLOW, BOLD)
                + ": "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt) as exc:
            print(style("\n⚠ Operazione annullata.", YELLOW, BOLD), file=sys.stderr)
            raise ValueError("nessuna data selezionata") from exc

        if answer in {"", "s", "si", "sì", "y", "yes"}:
            return today
        if answer in {"n", "no"}:
            break
        print(style("  Rispondi 's' per oggi oppure 'n' per un'altra data.", YELLOW))

    while True:
        try:
            raw = input(
                prompt_style("  Data fattura", BLUE, BOLD)
                + " (GG/MM/AAAA oppure AAAA-MM-GG): "
            )
        except (EOFError, KeyboardInterrupt) as exc:
            print(style("\n⚠ Operazione annullata.", YELLOW, BOLD), file=sys.stderr)
            raise ValueError("nessuna data inserita") from exc
        try:
            return parse_date(raw)
        except ValueError:
            print(style("  ✗ Data non valida. Riprova.", RED))


def print_confirmation_summary(
    *,
    amounts: InvoiceAmounts,
    invoice_date: date,
    invoice_number: str,
    destination: Path,
) -> None:
    separator = "─" * 72
    print("\n" + style("┌" + separator + "┐", CYAN))
    print(
        style("│", CYAN)
        + style(f" {'RIEPILOGO FATTURA':<71}", CYAN, BOLD)
        + style("│", CYAN)
    )
    print(style("├" + separator + "┤", CYAN))
    summary_row(
        "Cedente",
        f"{SELLER.first_name} {SELLER.last_name} · P.IVA {SELLER.vat_number}",
    )
    summary_row("Cliente", f"{CUSTOMER.name} · P.IVA {CUSTOMER.vat_number}")
    summary_row(
        "Sede cliente",
        f"{CUSTOMER.address.street} {CUSTOMER.address.number}, "
        f"{CUSTOMER.address.postal_code} {CUSTOMER.address.city} "
        f"({CUSTOMER.address.province})",
    )
    summary_row("Destinazione", f"{CUSTOMER.recipient_code} · {CUSTOMER.pec}")
    summary_row(
        "Documento",
        f"Fattura n. {invoice_number} del {invoice_date.strftime('%d/%m/%Y')}",
    )
    summary_row("Descrizione", DESCRIPTION)
    print(style("├" + separator + "┤", CYAN))
    summary_row("Compenso", format_eur(amounts.fee))
    summary_row("Rivalsa INPS", format_eur(amounts.social_security))
    summary_row(
        "Lordo",
        format_eur(amounts.gross),
        label_codes=(GREEN, BOLD),
        value_codes=(GREEN, BOLD),
    )
    summary_row("Bollo", format_eur(amounts.stamp_duty))
    if amounts.rounding:
        summary_row("Arrotondamento", format_eur(amounts.rounding))
    summary_row(
        "TOTALE",
        format_eur(amounts.total),
        label_codes=(GREEN, BOLD),
        value_codes=(GREEN, BOLD),
    )
    print(style("├" + separator + "┤", CYAN))
    summary_row("File", str(destination))
    print(style("└" + separator + "┘", CYAN))


def confirm_generation() -> bool:
    while True:
        try:
            answer = input(
                "\n"
                + prompt_style("  Confermi la generazione?", BOLD)
                + " "
                + prompt_style("[s/N]", YELLOW, BOLD)
                + ": "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        if answer in {"s", "si", "sì", "y", "yes"}:
            return True
        if answer in {"", "n", "no"}:
            return False
        print(style("  Rispondi 's' per confermare oppure 'n' per annullare.", YELLOW))


def prompt_integer(label: str, *, minimum: int, maximum: int) -> int | None:
    while True:
        try:
            raw = input(prompt_style(f"  {label}", BLUE, BOLD) + ": ").strip()
        except (EOFError, KeyboardInterrupt):
            print(style("\n  ⚠ Modifica annullata.", YELLOW))
            return None
        try:
            value = int(raw)
        except ValueError:
            print(style("  ✗ Inserisci un numero intero.", RED))
            continue
        if minimum <= value <= maximum:
            return value
        print(style(f"  ✗ Inserisci un valore tra {minimum} e {maximum}.", RED))
