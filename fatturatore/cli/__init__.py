"""CLI package: moduli nello stesso ordine del vecchio cli.py monolite."""

from __future__ import annotations

from .constants import (
    BANNER,
    BLUE,
    BOLD,
    CYAN,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_STATE_FILE,
    DIM,
    GREEN,
    PROJECT_ROOT,
    RED,
    RESET,
    YELLOW,
)
from .main import entrypoint, main
from .parser import build_parser, parse_date
from .progressives import manage_progressives, print_progressive_panel
from .prompts import (
    confirm_generation,
    print_confirmation_summary,
    prompt_for_gross,
    prompt_for_invoice_date,
    prompt_integer,
)
from .state import State, atomic_write, load_state, next_number_after_override, save_state
from .style import (
    colours_enabled,
    format_eur,
    print_banner,
    prompt_style,
    style,
    summary_row,
)

__all__ = [
    "BANNER",
    "BLUE",
    "BOLD",
    "CYAN",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_STATE_FILE",
    "DIM",
    "GREEN",
    "PROJECT_ROOT",
    "RED",
    "RESET",
    "State",
    "YELLOW",
    "atomic_write",
    "build_parser",
    "colours_enabled",
    "confirm_generation",
    "entrypoint",
    "format_eur",
    "load_state",
    "main",
    "manage_progressives",
    "next_number_after_override",
    "parse_date",
    "print_banner",
    "print_confirmation_summary",
    "print_progressive_panel",
    "prompt_for_gross",
    "prompt_for_invoice_date",
    "prompt_integer",
    "prompt_style",
    "save_state",
    "style",
    "summary_row",
]
