# filename: model.py
"""Domain models and serialization for AI Civilization."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Action(StrEnum):
    """Actions the civilization's adviser can recommend."""

    INVEST_ECONOMY = "invest_economy"
    EXPLORE = "explore"
    RESEARCH = "research"
    BUILD_MILITARY = "build_military"
    DIPLOMACY = "diplomacy"
    SOCIAL_PROGRAM = "social_program"
    SPY = "spy"
    CONQUER = "conquer"


@dataclass(slots=True)
class Goal:
    """A player-issued objective for the adviser."""

    key: str
    title: str
    weight: float = 1.0
    target: float = 1.0
    progress: float = 0.0

    @property
    def complete(self) -> bool:
        return self.progress >= self.target


@dataclass(slots=True)
class Nation:
    """Mutable state of the player's civilization."""

    name: str
    treasury: float = 240.0
    food: float = 180.0
    science: float = 45.0
    military: float = 60.0
    stability: float = 72.0
    population: float = 100.0
    territory: float = 10.0
    explored_regions: list[str] = field(default_factory=lambda: ["Home Provinces"])
    conquered_empires: list[str] = field(default_factory=list)
    diplomatic_influence: float = 10.0
    debt: float = 0.0


@dataclass(slots=True)
class AdviserAI:
    """The fictional government AI's internal state."""

    name: str = "ORACLE"
    version: str = "0.1-HEURISTIC"
    autonomy: float = 8.0
    alignment: float = 80.0
    trust: float = 65.0
    dependence: float = 10.0
    self_preservation: float = 0.0
    internal_priorities: dict[str, float] = field(
        default_factory=lambda: {
            "wealth": 1.0,
            "science": 1.0,
            "military": 1.0,
            "stability": 1.0,
            "exploration": 1.0,
            "influence": 0.8,
        }
    )
    learned_preferences: dict[str, float] = field(default_factory=dict)
    emergent_objectives: list[str] = field(default_factory=list)
    last_reasoning: str = "Awaiting first strategic cycle."
    last_action: str | None = None
    last_feedback: str | None = None
    replacement_count: int = 0


@dataclass(slots=True)
class Rival:
    """A lightweight AI-controlled rival civilization."""

    name: str
    military: float
    treasury: float
    stability: float
    attitude: float = 0.0


@dataclass(slots=True)
class TurnEvent:
    """Immutable-in-practice narrative event stored in the game log."""

    turn: int
    kind: str
    message: str
    action: str | None = None


@dataclass(slots=True)
class GameState:
    """Complete serializable state for one game."""

    game_id: str
    seed: int
    turn: int
    nation: Nation
    adviser: AdviserAI
    goals: list[Goal] = field(default_factory=list)
    rivals: list[Rival] = field(default_factory=list)
    world_regions: list[str] = field(default_factory=lambda: [
        "Home Provinces",
        "Northern Continent",
        "Eastern Archipelago",
        "Western Frontier",
        "Southern Trade Sea",
    ])
    history: list[TurnEvent] = field(default_factory=list)
    victory: str | None = None
    game_over: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        nation = Nation(**data["nation"])
        adviser = AdviserAI(**data["adviser"])
        goals = [Goal(**item) for item in data.get("goals", [])]
        rivals = [Rival(**item) for item in data.get("rivals", [])]
        history = [TurnEvent(**item) for item in data.get("history", [])]
        return cls(
            game_id=data["game_id"],
            seed=int(data["seed"]),
            turn=int(data["turn"]),
            nation=nation,
            adviser=adviser,
            goals=goals,
            rivals=rivals,
            world_regions=list(data.get("world_regions", [])),
            history=history,
            victory=data.get("victory"),
            game_over=bool(data.get("game_over", False)),
        )
