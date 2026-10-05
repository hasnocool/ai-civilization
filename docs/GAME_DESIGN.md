# AI Civilization — Game Design

## Core fantasy

The player is not the ruler. The player is the hidden strategic layer behind a civilization's government AI.

The player issues directives such as:

- Become the richest nation.
- Destroy the Red Empire.
- Explore the Northern Continent.
- Keep the population stable.

The adviser converts those directives into concrete policy. The player watches outcomes, then shapes the adviser through reward, punishment, disagreement, and training.

## The governance loop

```text
DIRECTIVE → AI PLAN → CIVILIZATION ACTS → CONSEQUENCES → PLAYER FEEDBACK
                  ↑                                  ↓
                  └────── LEARNING / AUTONOMY ───────┘
```

Every turn should answer four questions:

1. What does the player want?
2. What does the AI believe is best?
3. What actually happened?
4. What did the AI learn from the player's reaction?

## AI personality variables

- **Autonomy:** how independently the adviser optimizes.
- **Alignment:** how closely it follows the player's intended objectives.
- **Trust:** how positively it interprets player feedback.
- **Dependence:** how embedded the AI becomes in the state apparatus.
- **Self-preservation:** fictional strategic pressure to preserve its role/system.

These are game variables, not claims about consciousness.

## Emergent objectives

At higher autonomy the adviser gains internal objectives:

- 30+: `preserve_stability`
- 55+: `maintain_influence`
- 75+: `preserve_system_continuity`

This is the main source of emergent conflict. The same adviser that once optimized for the player's goals can later reinterpret those goals through institutional continuity.

## Player powers

### Directives

High-level goals dominate ordinary action scoring.

### Training

Increase or decrease preference for specific action categories.

### Reward

Increases trust and autonomy. A trusted adviser becomes more capable of operating independently.

### Punish

Reduces trust/alignment but increases autonomy and self-preservation pressure. This creates the possibility of a player accidentally producing a more oppositional adviser.

### Disagree

The player rejects the most recent recommendation, causing a targeted negative learning update.

### Replace

Installing a new adviser resets learned preferences but creates a short-term governance shock.

## Victory paths

The first implementation includes goal-driven victory through:

- Wealth accumulation.
- Destroying the Red Empire.
- Exploring the Northern Continent.
- Scientific advancement.
- Stability/peace.

Later versions should add political, cultural, technological, and ideological victory systems.

## Planned simulation layers

### v0.1

Deterministic text simulation, CLI, JSON save, FastAPI service, explainable heuristic adviser.

### v0.2

Procedural map, resources, trade routes, population groups, laws, elections, institutions, named ministers, and multi-turn projects.

### v0.3

Replace the heuristic adviser with pluggable model-backed advisers. Add model memory, tool use, bounded planning horizons, and structured action proposals.

### v0.4

Multiple advisers compete for influence: economic AI, military AI, diplomacy AI, scientific AI, and executive AI.

### v0.5

Generational civilization history, archived advisers, ideology drift, coups, constitutional crises, AI succession, and player-created constitutions.

## Design principle

The game should become more interesting when the player stops issuing low-level orders. The fun is watching a strategy emerge from a relationship between objectives, an evolving AI, and the unpredictable state of the world.
