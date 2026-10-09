from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from .constants import BLUE, BOLD, CYAN, GREEN, RED, YELLOW
from .prompts import prompt_integer
from .state import State, load_state, save_state
from .style import print_banner, prompt_style, style, summary_row


def manage_progressives(path: Path, initial_year: int | None = None) -> int:
    try:
        state = load_state(path)
    except (OSError, ValueError) as exc:
        print(style(f"✗ Errore: {exc}", RED, BOLD), file=sys.stderr)
        return 2

    year = initial_year or date.today().year
    print_banner()
    print(style("\n  Gestione numerazione fatture", CYAN, BOLD))

    while True:
        print_progressive_panel(state, year)
        try:
            choice = input(
                "\n"
                + prompt_style("  Scegli", BLUE, BOLD)
                + " "
                + prompt_style("[1/2/q]", YELLOW, BOLD)
                + ": "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(style("\n⚠ Gestione numerazione chiusa.", YELLOW, BOLD))
            return 0

        if choice in {"q", "quit", "esci", "0", ""}:
            print(style("\n✓ Numerazione salvata.", GREEN, BOLD))
            return 0

        if choice == "1":
            value = prompt_integer(
                f"Prossimo numero fattura per il {year}",
                minimum=1,
                maximum=9_999_999_999,
            )
            if value is None:
                continue
            state["years"][str(year)] = value
            save_state(path, state)
            print(
                style(
                    f"  ✓ Prossima fattura {year} impostata a {value}.",
                    GREEN,
                    BOLD,
                )
            )
            continue

        if choice == "2":
            selected_year = prompt_integer("Anno da gestire", minimum=1900, maximum=9999)
            if selected_year is not None:
                year = selected_year
            continue

        print(style("  ✗ Scelta non valida.", RED))


def print_progressive_panel(state: State, year: int) -> None:
    separator = "─" * 72
    next_invoice = state["years"].get(str(year), 1)
    print("\n" + style("┌" + separator + "┐", CYAN))
    print(
        style("│", CYAN)
        + style(f" {'NUMERAZIONE FATTURE':<71}", CYAN, BOLD)
        + style("│", CYAN)
    )
    print(style("├" + separator + "┤", CYAN))
    summary_row("Anno", str(year))
    summary_row("Prossima fattura", str(next_invoice))
    print(style("├" + separator + "┤", CYAN))
    summary_row("1", "Imposta il prossimo numero fattura")
    summary_row("2", "Cambia anno da visualizzare o modificare")
    summary_row("q", "Esci")
    print(style("└" + separator + "┘", CYAN))
