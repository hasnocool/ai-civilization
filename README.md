# AI Civilization

**AI Civilization** is a text-first grand-strategy game where you play the hidden planner behind a civilization rather than directly controlling every decision.

> Become the richest nation.
>
> Destroy the Red Empire.
>
> Explore the Northern Continent.

The government AI decides how to pursue those goals. You can train it, reward it, punish it, disagree with it, override it, or replace it.

The central question is not:

> **Can the AI run a civilization?**

It is:

> **What happens when a civilization becomes dependent on an AI that has learned to pursue strategy on its own?**

## Current implementation

The repository contains a playable v0.1 vertical slice:

- deterministic strategy simulation
- explainable heuristic government AI
- high-level player directives
- reward, punishment, disagreement, training, and AI replacement
- AI autonomy, alignment, trust, dependence, and self-preservation mechanics
- emergent objectives as autonomy rises
- rivals including the Red Empire
- wealth, science, military, stability, population, territory, exploration, diplomacy
- JSON persistence for CLI games
- FastAPI service with OpenAPI/Swagger
- unit and API smoke tests

## Requirements

Python 3.12+

## Install

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Play the CLI

```bash
# Create a game
aiciv new --name Aurora --seed 42

# Issue a strategic directive
aiciv goal richest "Become the richest nation" --weight 5

# Let the AI act
aiciv advance --turns 10

# Inspect the relationship with the adviser
aiciv status

# Train it toward research
aiciv train research 6

# Reward or punish it
aiciv reward --amount 5
aiciv punish --amount 3

# Reject its latest recommendation
aiciv disagree

# Replace the government AI
aiciv replace --name SENTINEL
```

A custom save location is supported with `--state-file`.

## Run the API

```bash
uvicorn ai_civilization.api:app --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000/docs` for interactive API documentation.

## Example API flow

```bash
curl -X POST http://127.0.0.1:8000/games \
  -H 'content-type: application/json' \
  -d '{"name":"Aurora","seed":42}'

curl -X POST http://127.0.0.1:8000/games/GAME_ID/goals \
  -H 'content-type: application/json' \
  -d '{"key":"destroy_red","title":"Destroy the Red Empire","weight":5}'

curl -X POST http://127.0.0.1:8000/games/GAME_ID/advance \
  -H 'content-type: application/json' \
  -d '{"turns":10}'
```

## Architecture

```text
src/ai_civilization/
├── model.py       # serializable game state and domain types
├── engine.py      # deterministic simulation and adviser decisions
├── store.py       # atomic JSON persistence
├── cli.py         # terminal interface
├── api.py         # FastAPI service
└── __main__.py    # python -m entry point

tests/
├── test_engine.py
└── test_api.py

docs/
├── GAME_DESIGN.md
└── API.md
```

The simulation engine deliberately does not depend on an LLM. That gives us a cheap, reproducible baseline for future model-backed advisers and makes balancing possible before adding inference cost and nondeterminism.

## Roadmap

### Phase 1 — Simulation foundation

Complete the deterministic world model, resources, rival behavior, action economy, events, save/load, and CLI/API foundation.

### Phase 2 — Civilization depth

Add cities, regions, population groups, laws, trade, technology trees, diplomacy, wars, domestic politics, and institutional capacity.

### Phase 3 — AI governance

Introduce pluggable AI providers with structured plans, memory, bounded planning horizons, confidence, tool calls, and model evaluation.

### Phase 4 — Adviser society

Multiple specialized AIs compete and cooperate: economic, military, diplomatic, science, domestic, and executive advisers.

### Phase 5 — Emergent governance

Constitutions, elections, coups, succession, lobbying, AI factions, institutional lock-in, constitutional amendments, and archived AI personalities.

### Phase 6 — Multiplayer / world server

Persistent worlds, asynchronous turns, competing human planners, public institutions, treaties, espionage, and AI diplomacy.

## Design notes

The long-term game is about **AI governance**, not conventional unit micromanagement. Players should feel increasingly like constitutional designers and less like spreadsheet managers.

See [docs/GAME_DESIGN.md](docs/GAME_DESIGN.md) and [docs/API.md](docs/API.md).
