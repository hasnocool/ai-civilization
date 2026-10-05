# filename: store.py
"""Atomic JSON persistence for CLI games."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from .model import GameState


def default_state_path() -> Path:
    return Path.home() / ".local" / "share" / "ai-civilization" / "state.json"


def save_game(game: GameState, path: Path | str) -> None:
    """Write game state atomically so interrupted saves do not corrupt it."""
    destination = Path(path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(game.to_dict(), indent=2, sort_keys=True) + "\n"
    with NamedTemporaryFile("w", encoding="utf-8", dir=destination.parent, delete=False) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    os.replace(temporary, destination)


def load_game(path: Path | str) -> GameState:
    """Load a game from disk."""
    source = Path(path).expanduser()
    return GameState.from_dict(json.loads(source.read_text(encoding="utf-8")))
