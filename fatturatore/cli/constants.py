from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUTPUT_DIR = Path.home() / "Downloads"
DEFAULT_STATE_FILE = Path(
    os.environ.get("FATTURATORE_STATE_FILE", PROJECT_ROOT / ".fatturatore-state.json")
)

BANNER = r"""
 ______      _______ _______ _    _ _____            _______ ____  _____ ______
|  ____/\   |__   __|__   __| |  | |  __ \     /\   |__   _/ __ \|  __ \|  ____|
| |__ /  \     | |     | |  | |  | | |__) |   /  \     | || |  | | |__) | |__
|  __/ /\ \    | |     | |  | |  | |  _  /   / /\ \    | || |  | |  _  /|  __|
| | / ____ \   | |     | |  | |__| | | \ \  / ____ \   | || |__| | | \ \| |____
|_|/_/    \_\  |_|     |_|   \____/|_|  \_\/_/    \_\  |_| \____/|_|  \_\______|
""".strip("\n")

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
BLUE = "\033[34m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
