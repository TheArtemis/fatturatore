from __future__ import annotations

import os
import sys
import textwrap
from decimal import Decimal

try:
    import readline as _readline  # Importing enables native terminal line editing.
except ImportError:  # pragma: no cover - unavailable on some non-Unix systems
    _readline = None

from .constants import BANNER, BLUE, BOLD, CYAN, RESET


def print_banner() -> None:
    colours = (CYAN, BLUE, CYAN, BLUE, CYAN, BLUE)
    for line, colour in zip(BANNER.splitlines(), colours, strict=False):
        print(style(line, colour, BOLD))


def summary_row(
    label: str,
    value: str,
    *,
    label_codes: tuple[str, ...] = (BLUE, BOLD),
    value_codes: tuple[str, ...] = (),
) -> None:
    lines = textwrap.wrap(value, width=53, break_long_words=True) or [""]
    for index, line in enumerate(lines):
        row_label = label if index == 0 else ""
        print(
            style("│", CYAN)
            + " "
            + style(f"{row_label:<18}", *label_codes)
            + style(f"{line:<53}", *value_codes)
            + style("│", CYAN)
        )


def format_eur(value: Decimal) -> str:
    international = f"{value:,.2f}"
    italian = international.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"{italian} EUR"


def style(text: str, *codes: str) -> str:
    if not colours_enabled():
        return text
    return "".join(codes) + text + RESET


def prompt_style(text: str, *codes: str) -> str:
    if not colours_enabled():
        return text
    opening = "".join(codes)
    if _readline is None:
        return opening + text + RESET
    return f"\001{opening}\002{text}\001{RESET}\002"


def colours_enabled() -> bool:
    return (
        sys.stdout.isatty()
        and "NO_COLOR" not in os.environ
        and os.environ.get("TERM", "") != "dumb"
    )
