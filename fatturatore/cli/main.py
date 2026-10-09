from __future__ import annotations

import sys
from datetime import date

from ..config import SELLER
from ..invoice import build_invoice_xml, calculate_amounts, parse_amount
from .constants import BLUE, BOLD, DEFAULT_STATE_FILE, GREEN, RED, YELLOW
from .parser import build_parser
from .progressives import manage_progressives
from .prompts import (
    confirm_generation,
    print_confirmation_summary,
    prompt_for_gross,
    prompt_for_invoice_date,
)
from .state import atomic_write, load_state, next_number_after_override, save_state
from .style import format_eur, style


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.progressivi:
        if args.lordo is not None:
            print(
                style(
                    "✗ Errore: non indicare un lordo insieme a --progressivi",
                    RED,
                    BOLD,
                ),
                file=sys.stderr,
            )
            return 2
        return manage_progressives(DEFAULT_STATE_FILE)

    interactive = args.lordo is None
    try:
        gross = parse_amount(args.lordo) if not interactive else prompt_for_gross()
        invoice_date = args.data or (prompt_for_invoice_date() if interactive else date.today())
        amounts = calculate_amounts(gross)
        state = load_state(DEFAULT_STATE_FILE)
        automatic_number = state["years"].get(str(invoice_date.year), 1)
        invoice_number = args.numero or str(automatic_number)
        transmission_number = f"{state['next_transmission']:05d}"
        filename = f"IT{SELLER.tax_code}_{transmission_number}.xml"
        destination = args.output / filename
        if interactive:
            print_confirmation_summary(
                amounts=amounts,
                invoice_date=invoice_date,
                invoice_number=invoice_number,
                destination=destination,
            )
            if not confirm_generation():
                print(
                    style("\n⚠ Operazione annullata: nessun file generato.", YELLOW, BOLD)
                )
                return 0

        xml = build_invoice_xml(amounts, invoice_date, invoice_number, transmission_number)
        args.output.mkdir(parents=True, exist_ok=True)
        if destination.exists() and not args.sovrascrivi:
            raise ValueError(
                f"il file {destination} esiste già; usa --sovrascrivi solo se sei sicuro"
            )
        atomic_write(destination, xml)

        state["next_transmission"] += 1
        state["years"][str(invoice_date.year)] = max(
            automatic_number + 1,
            next_number_after_override(args.numero, invoice_date.year),
        )
        save_state(DEFAULT_STATE_FILE, state)
    except (OSError, ValueError) as exc:
        print(style(f"✗ Errore: {exc}", RED, BOLD), file=sys.stderr)
        return 2

    print(style(f"\n✓ XML creato: {destination}", GREEN, BOLD))
    print(
        style("  Fattura", BLUE, BOLD)
        + f": {invoice_number} del {invoice_date.strftime('%d/%m/%Y')}"
    )
    print(
        style("  Totale ", BLUE, BOLD)
        + f": {format_eur(amounts.total)} "
        f"(lordo {format_eur(amounts.gross)} "
        f"+ bollo {format_eur(amounts.stamp_duty)}"
        + (f" + arrotondamento {format_eur(amounts.rounding)}" if amounts.rounding else "")
        + ")"
    )
    return 0


def entrypoint() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    entrypoint()
