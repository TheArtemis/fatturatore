from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

from .constants import DEFAULT_OUTPUT_DIR


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fatturatore",
        description=(
            "Genera una fattura elettronica XML FPR12. "
            "Il lordo indicato include la rivalsa INPS al 4% ed esclude il bollo."
        ),
    )
    parser.add_argument(
        "lordo",
        nargs="?",
        help="lordo senza bollo, per esempio 2917 oppure 2.917,00",
    )
    parser.add_argument(
        "--numero",
        help="numero fattura; predefinito: progressivo automatico annuale",
    )
    parser.add_argument(
        "--data",
        type=parse_date,
        metavar="DATA",
        help="data fattura; predefinita: oggi",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"cartella di destinazione; predefinita: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument("--sovrascrivi", action="store_true", help="sovrascrivi un file esistente")
    parser.add_argument(
        "-p",
        "--progressivi",
        action="store_true",
        help="visualizza e modifica il prossimo numero fattura senza generare una fattura",
    )
    return parser


def parse_date(raw: str) -> date:
    value = raw.strip()
    try:
        if "/" in value:
            return datetime.strptime(value, "%d/%m/%Y").date()
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("usa GG/MM/AAAA oppure AAAA-MM-GG") from exc
