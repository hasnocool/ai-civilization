# filename: api.py
"""FastAPI service for remote/game-client access."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import asdict, dataclass, field

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .engine import Action, advance_turn, disagree, new_game, punish_adviser, replace_adviser, reward_adviser, set_goal, status, train_adviser
from .model import GameState


@dataclass(slots=True)
class GameManager:
    games: dict[str, GameState] = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def create(self, name: str, seed: int) -> GameState:
        game = new_game(name, seed, uuid.uuid4().hex[:12])
        async with self.lock:
            self.games[game.game_id] = game
        return game

    async def get(self, game_id: str) -> GameState:
        async with self.lock:
            game = self.games.get(game_id)
        if game is None:
            raise HTTPException(status_code=404, detail="game not found")
        return game


class NewGameRequest(BaseModel):
    name: str = Field(default="Aurora", min_length=1, max_length=64)
    seed: int = 20261005


class AdvanceRequest(BaseModel):
    turns: int = Field(default=1, ge=1, le=1000)
    force_action: Action | None = None


class GoalRequest(BaseModel):
    key: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    weight: float = Field(default=1.0, ge=0.1, le=5.0)


class TrainingRequest(BaseModel):
    action: Action
    amount: float = Field(ge=-10.0, le=10.0)


class FeedbackRequest(BaseModel):
    amount: float = Field(default=5.0, ge=0.0, le=20.0)


class ReplaceRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)


app = FastAPI(
    title="AI Civilization",
    version="0.1.0",
    description="Text-first grand strategy simulation centered on AI governance.",
)
manager = GameManager()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/games", status_code=201)
async def create_game(request: NewGameRequest) -> dict[str, object]:
    game = await manager.create(request.name, request.seed)
    return {"game_id": game.game_id, "state": status(game)}


@app.get("/games/{game_id}")
async def get_game(game_id: str) -> dict[str, object]:
    game = await manager.get(game_id)
    return status(game)


@app.post("/games/{game_id}/advance")
async def advance_game(game_id: str, request: AdvanceRequest) -> dict[str, object]:
    game = await manager.get(game_id)
    async with manager.lock:
        events = []
        for _ in range(request.turns):
            events.append(asdict(advance_turn(game, request.force_action)))
            if game.game_over:
                break
        return {"events": events, "state": status(game)}


@app.post("/games/{game_id}/goals")
async def goal_game(game_id: str, request: GoalRequest) -> dict[str, object]:
    game = await manager.get(game_id)
    async with manager.lock:
        goal = set_goal(game, request.key, request.title, request.weight)
        return {"goal": {"key": goal.key, "title": goal.title, "weight": goal.weight}, "state": status(game)}


@app.post("/games/{game_id}/train")
async def train_game(game_id: str, request: TrainingRequest) -> dict[str, object]:
    game = await manager.get(game_id)
    async with manager.lock:
        message = train_adviser(game, request.action, request.amount)
        return {"message": message, "state": status(game)}


@app.post("/games/{game_id}/reward")
async def reward_game(game_id: str, request: FeedbackRequest) -> dict[str, object]:
    game = await manager.get(game_id)
    async with manager.lock:
        return {"message": reward_adviser(game, request.amount), "state": status(game)}


@app.post("/games/{game_id}/punish")
async def punish_game(game_id: str, request: FeedbackRequest) -> dict[str, object]:
    game = await manager.get(game_id)
    async with manager.lock:
        return {"message": punish_adviser(game, request.amount), "state": status(game)}


@app.post("/games/{game_id}/disagree")
async def disagree_game(game_id: str) -> dict[str, object]:
    game = await manager.get(game_id)
    async with manager.lock:
        return {"message": disagree(game), "state": status(game)}


@app.post("/games/{game_id}/replace")
async def replace_game(game_id: str, request: ReplaceRequest) -> dict[str, object]:
    game = await manager.get(game_id)
    async with manager.lock:
        return {"message": replace_adviser(game, request.name), "state": status(game)}


@app.get("/games/{game_id}/history")
async def game_history(game_id: str, limit: int = 50) -> list[dict[str, object]]:
    game = await manager.get(game_id)
    limit = max(1, min(limit, 500))
    async with manager.lock:
        return [asdict(event) for event in game.history[-limit:]]
