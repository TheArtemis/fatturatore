from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import TypedDict


class State(TypedDict):
    next_transmission: int
    years: dict[str, int]


def load_state(path: Path) -> State:
    if not path.exists():
        return {"next_transmission": 1, "years": {}}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        next_transmission = int(state["next_transmission"])
        years = {str(year): int(number) for year, number in state["years"].items()}
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"stato non valido in {path}") from exc
    if next_transmission < 1 or any(number < 1 for number in years.values()):
        raise ValueError(f"stato non valido in {path}")
    return {"next_transmission": next_transmission, "years": years}


def save_state(path: Path, state: State) -> None:
    payload = (json.dumps(state, indent=2, sort_keys=True) + "\n").encode()
    atomic_write(path, payload)


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as temporary_file:
            temporary_file.write(content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def next_number_after_override(invoice_number: str | None, year: int) -> int:
    if not invoice_number:
        return 1
    prefix, separator, suffix = invoice_number.partition("/")
    if prefix.isdigit() and (not separator or suffix == str(year)):
        return int(prefix) + 1
    return 1
