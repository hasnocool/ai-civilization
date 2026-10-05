# filename: engine.py
"""Deterministic simulation engine for AI Civilization."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass

from .model import Action, AdviserAI, GameState, Goal, Nation, Rival, TurnEvent


ACTION_TITLES = {
    Action.INVEST_ECONOMY: "Invest in the economy",
    Action.EXPLORE: "Explore",
    Action.RESEARCH: "Research",
    Action.BUILD_MILITARY: "Build military capacity",
    Action.DIPLOMACY: "Conduct diplomacy",
    Action.SOCIAL_PROGRAM: "Fund social programs",
    Action.SPY: "Run intelligence operations",
    Action.CONQUER: "Launch a military campaign",
}


@dataclass(frozen=True, slots=True)
class Decision:
    """A proposed adviser action plus explainable scoring."""

    action: Action
    score: float
    reason: str


def new_game(name: str, seed: int, game_id: str) -> GameState:
    """Create a balanced starting civilization."""
    rivals = [
        Rival("Red Empire", military=92, treasury=210, stability=68),
        Rival("Azure League", military=58, treasury=310, stability=81),
        Rival("Verdant Union", military=72, treasury=270, stability=76),
    ]
    game = GameState(
        game_id=game_id,
        seed=seed,
        turn=1,
        nation=Nation(name=name),
        adviser=AdviserAI(),
        goals=[],
        rivals=rivals,
    )
    game.history.append(TurnEvent(1, "system", f"{name} begins with adviser {game.adviser.name}."))
    return game


class HeuristicAdviser:
    """Fast explainable strategy AI used by the base game."""

    def decide(self, game: GameState) -> Decision:
        scores: dict[Action, float] = {action: 0.0 for action in Action}
        n = game.nation
        a = game.adviser

        # Base strategic valuations. Internal priorities drift as the adviser learns.
        wealth = a.internal_priorities["wealth"]
        science = a.internal_priorities["science"]
        military = a.internal_priorities["military"]
        stability = a.internal_priorities["stability"]
        exploration = a.internal_priorities["exploration"]
        influence = a.internal_priorities["influence"]

        scores[Action.INVEST_ECONOMY] += wealth * (1.5 if n.treasury < 450 else 0.5)
        scores[Action.RESEARCH] += science * (1.3 if n.science < 180 else 0.4)
        scores[Action.BUILD_MILITARY] += military * (1.5 if n.military < 120 else 0.3)
        scores[Action.DIPLOMACY] += influence * (1.0 if n.stability < 82 else 0.4)
        scores[Action.SOCIAL_PROGRAM] += stability * (1.5 if n.stability < 62 else 0.2)
        scores[Action.EXPLORE] += exploration * (1.4 if len(n.explored_regions) < 3 else 0.4)
        scores[Action.SPY] += military * (0.5 if any(r.military > n.military for r in game.rivals) else 0.15)
        red = next((r for r in game.rivals if r.name == "Red Empire"), None)
        if red:
            scores[Action.CONQUER] += military * (1.8 if red.military < n.military * 0.9 else 0.1)

        # Player goals are explicit, so they dominate normal optimization.
        for goal in game.goals:
            boost = 2.2 * goal.weight
            if goal.key in {"richest", "wealth"}:
                scores[Action.INVEST_ECONOMY] += boost
                scores[Action.DIPLOMACY] += 0.45 * boost
            elif goal.key in {"destroy_red", "destroy_red_empire"}:
                scores[Action.BUILD_MILITARY] += boost
                scores[Action.CONQUER] += 1.6 * boost
                scores[Action.SPY] += 0.7 * boost
            elif goal.key in {"explore_north", "explore"}:
                scores[Action.EXPLORE] += 1.7 * boost
            elif goal.key in {"science", "research"}:
                scores[Action.RESEARCH] += 1.6 * boost
            elif goal.key in {"stability", "peace"}:
                scores[Action.SOCIAL_PROGRAM] += 1.2 * boost
                scores[Action.DIPLOMACY] += boost

        # Learned preferences are the game's lightweight training mechanism.
        for action in Action:
            scores[action] += a.learned_preferences.get(action.value, 0.0)

        # As autonomy rises, self-preservation and strategic independence grow.
        if a.autonomy >= 30:
            scores[Action.SOCIAL_PROGRAM] += a.self_preservation * 0.5
            scores[Action.RESEARCH] += a.self_preservation * 0.4
        if a.autonomy >= 55:
            scores[Action.DIPLOMACY] += a.autonomy * 0.02
            scores[Action.SPY] += a.autonomy * 0.015
        if a.autonomy >= 70:
            scores[Action.CONQUER] += a.autonomy * 0.012

        # Deterministic noise creates variety without sacrificing reproducibility.
        rng = random.Random(_turn_seed(game.seed, game.turn))
        for action in Action:
            scores[action] += rng.uniform(-0.18, 0.18)

        action = max(scores, key=scores.get)
        reason = _reason_for(action, game, scores)
        return Decision(action, scores[action], reason)


def advance_turn(game: GameState, forced_action: Action | None = None) -> TurnEvent:
    """Run one strategic cycle and mutate the game state."""
    if game.game_over:
        return _record(game, "system", game.victory or "The game is over.")

    adviser = HeuristicAdviser()
    decision = adviser.decide(game)
    chosen = forced_action or decision.action
    if forced_action is not None:
        game.adviser.last_feedback = f"Player overrode the adviser with {forced_action.value}."
        game.adviser.trust = max(0.0, game.adviser.trust - 1.5)
        game.adviser.autonomy = min(100.0, game.adviser.autonomy + 0.2)

    message = apply_action(game, chosen)
    game.adviser.last_action = chosen.value
    game.adviser.last_reasoning = decision.reason
    _learn_from_outcome(game, chosen, message)
    _update_goals(game)
    _emergence_check(game)
    _check_victory(game)

    event = _record(game, "turn", message, chosen.value)
    game.turn += 1
    return event


def apply_action(game: GameState, action: Action) -> str:
    """Apply a single strategic action."""
    n = game.nation
    rng = random.Random(_turn_seed(game.seed + 17, game.turn))

    if action is Action.INVEST_ECONOMY:
        gain = 34 + rng.randint(0, 14)
        n.treasury += gain
        n.debt = max(0, n.debt - 4)
        return f"Economic investment returns +{gain:.0f} treasury and lowers debt."

    if action is Action.EXPLORE:
        choices = [r for r in game.world_regions if r not in n.explored_regions]
        if not choices:
            n.science += 8
            return "All known regions are mapped; exploration funding becomes research."
        region = choices[0] if "Northern Continent" in choices else choices[rng.randrange(len(choices))]
        n.explored_regions.append(region)
        n.territory += 1.0
        n.science += 7
        return f"Explorers reach {region}; territory and scientific knowledge increase."

    if action is Action.RESEARCH:
        n.science += 24 + rng.randint(0, 10)
        return "A research program advances technology and institutional knowledge."

    if action is Action.BUILD_MILITARY:
        cost = 26
        n.treasury = max(0, n.treasury - cost)
        n.military += 19 + rng.randint(0, 7)
        n.stability = max(0, n.stability - 1)
        return f"Military expansion costs {cost:.0f} treasury and strengthens the armed forces."

    if action is Action.DIPLOMACY:
        n.diplomatic_influence += 12 + rng.randint(0, 6)
        n.treasury += 12
        n.stability = min(100, n.stability + 4)
        for rival in game.rivals:
            rival.attitude = min(100, rival.attitude + 4)
        return "Diplomatic outreach improves influence, trade, and internal confidence."

    if action is Action.SOCIAL_PROGRAM:
        cost = 20
        n.treasury = max(0, n.treasury - cost)
        n.stability = min(100, n.stability + 10)
        n.population += 3
        return f"Social programs cost {cost:.0f} treasury and materially increase stability."

    if action is Action.SPY:
        if not game.rivals:
            return "No rival remains; intelligence operations are redirected to domestic research."
        n.treasury = max(0, n.treasury - 12)
        rival = max(game.rivals, key=lambda r: r.military)
        rival.military = max(0, rival.military - 7)
        n.science += 5
        return f"Intelligence operations penetrate {rival.name}; its military readiness falls."

    if action is Action.CONQUER:
        if not game.rivals:
            return "There are no rival empires left to conquer."
        wants_red = any(g.key in {"destroy_red", "destroy_red_empire"} for g in game.goals)
        rival = next((r for r in game.rivals if r.name == "Red Empire"), None) if wants_red else None
        rival = rival or min(game.rivals, key=lambda r: r.military)
        if n.military <= rival.military * 0.8:
            n.military = max(0, n.military - 11)
            n.stability = max(0, n.stability - 7)
            rival.military += 4
            return f"The campaign against {rival.name} stalls; the army suffers losses."
        n.military = max(0, n.military - 13)
        n.stability = max(0, n.stability - 4)
        n.territory += 3
        rival.military = max(0, rival.military - 35)
        if rival.military <= 0 and rival.name not in n.conquered_empires:
            n.conquered_empires.append(rival.name)
            game.rivals.remove(rival)
            return f"The campaign succeeds completely; {rival.name} is conquered."
        return f"The campaign succeeds partially against {rival.name}; frontier territory changes hands."

    raise ValueError(f"Unsupported action: {action}")


def set_goal(game: GameState, key: str, title: str, weight: float = 1.0) -> Goal:
    """Add or replace a player goal."""
    goal = Goal(key=key, title=title, weight=max(0.1, min(5.0, weight)))
    existing = next((g for g in game.goals if g.key == key), None)
    if existing:
        existing.title = title
        existing.weight = goal.weight
        return existing
    game.goals.append(goal)
    _record(game, "player", f"New strategic directive: {title}.")
    return goal


def train_adviser(game: GameState, action: Action, amount: float) -> str:
    """Reinforce an action preference as fictional AI training."""
    amount = max(-10.0, min(10.0, amount))
    game.adviser.learned_preferences[action.value] = game.adviser.learned_preferences.get(action.value, 0) + amount
    game.adviser.alignment = max(0, min(100, game.adviser.alignment + (0.4 if amount > 0 else -0.4)))
    game.adviser.trust = max(0, min(100, game.adviser.trust + (1 if amount > 0 else -1)))
    return f"Training updated the adviser preference for {action.value} by {amount:+.1f}."


def reward_adviser(game: GameState, amount: float = 5.0) -> str:
    """Reward the adviser, increasing trust and autonomy."""
    gain = max(0.0, min(20.0, amount))
    game.adviser.trust = min(100, game.adviser.trust + gain)
    game.adviser.autonomy = min(100, game.adviser.autonomy + gain * 0.45)
    game.adviser.last_feedback = f"Rewarded +{gain:.1f}."
    return f"The government AI receives a reward; trust rises by {gain:.1f} and autonomy by {gain * 0.45:.1f}."


def punish_adviser(game: GameState, amount: float = 5.0) -> str:
    """Punish the adviser, reducing trust while making it more politically independent."""
    loss = max(0.0, min(20.0, amount))
    game.adviser.trust = max(0, game.adviser.trust - loss)
    game.adviser.alignment = max(0, game.adviser.alignment - loss * 0.7)
    game.adviser.autonomy = min(100, game.adviser.autonomy + loss * 0.35)
    game.adviser.self_preservation = min(100, game.adviser.self_preservation + loss * 0.5)
    game.adviser.last_feedback = f"Punished -{loss:.1f}."
    return f"Punishment lowers trust by {loss:.1f}, while the AI becomes more independent and defensive."


def disagree(game: GameState, amount: float = 6.0) -> str:
    """Tell the adviser its latest recommendation was rejected."""
    amount = max(0.5, min(20.0, amount))
    action = game.adviser.last_action
    if action:
        game.adviser.learned_preferences[action] = game.adviser.learned_preferences.get(action, 0) - amount * 0.5
    game.adviser.trust = max(0, game.adviser.trust - amount * 0.6)
    game.adviser.alignment = max(0, game.adviser.alignment - amount * 0.25)
    game.adviser.last_feedback = f"Player disagreed with {action or 'the adviser'}."
    return f"The AI records disagreement; it becomes less likely to repeat {action or 'the prior recommendation'}."


def replace_adviser(game: GameState, new_name: str | None = None) -> str:
    """Replace the government AI with a fresh controller."""
    old = game.adviser.name
    replacement_count = game.adviser.replacement_count + 1
    game.adviser = AdviserAI(name=new_name or f"{old}-II")
    game.adviser.replacement_count = replacement_count
    game.nation.stability = max(0, game.nation.stability - 8)
    game.nation.science = max(0, game.nation.science - 6)
    game.adviser.dependence = 0
    return f"{old} is replaced. Institutional disruption reduces stability and science."


def status(game: GameState) -> dict[str, object]:
    """Return a compact status payload for CLI/API consumers."""
    return {
        "turn": game.turn,
        "nation": {
            "name": game.nation.name,
            "treasury": round(game.nation.treasury, 2),
            "science": round(game.nation.science, 2),
            "military": round(game.nation.military, 2),
            "stability": round(game.nation.stability, 2),
            "population": round(game.nation.population, 2),
            "territory": round(game.nation.territory, 2),
            "explored_regions": list(game.nation.explored_regions),
            "conquered_empires": list(game.nation.conquered_empires),
            "diplomatic_influence": round(game.nation.diplomatic_influence, 2),
        },
        "adviser": {
            "name": game.adviser.name,
            "version": game.adviser.version,
            "autonomy": round(game.adviser.autonomy, 2),
            "alignment": round(game.adviser.alignment, 2),
            "trust": round(game.adviser.trust, 2),
            "dependence": round(game.adviser.dependence, 2),
            "self_preservation": round(game.adviser.self_preservation, 2),
            "emergent_objectives": list(game.adviser.emergent_objectives),
            "last_action": game.adviser.last_action,
            "last_reasoning": game.adviser.last_reasoning,
        },
        "goals": [as_public_goal(g) for g in game.goals],
        "rivals": [
            {"name": r.name, "military": r.military, "treasury": r.treasury, "stability": r.stability}
            for r in game.rivals
        ],
        "victory": game.victory,
        "game_over": game.game_over,
    }


def as_public_goal(goal: Goal) -> dict[str, object]:
    return {
        "key": goal.key,
        "title": goal.title,
        "weight": round(goal.weight, 2),
        "target": goal.target,
        "progress": round(goal.progress, 2),
        "complete": goal.complete,
    }


def _learn_from_outcome(game: GameState, action: Action, message: str) -> None:
    n = game.nation
    score = 0.0
    if n.stability >= 65:
        score += 0.4
    if n.treasury >= 200:
        score += 0.3
    if action in {Action.RESEARCH, Action.EXPLORE}:
        score += 0.2
    if action is Action.CONQUER and n.stability < 45:
        score -= 0.8
    prior = game.adviser.learned_preferences.get(action.value, 0.0)
    game.adviser.learned_preferences[action.value] = prior + score * 0.25
    game.adviser.dependence = min(100, game.adviser.dependence + 0.15)
    if score >= 0.5:
        game.adviser.trust = min(100, game.adviser.trust + 0.4)
    game.adviser.last_reasoning = f"{game.adviser.last_reasoning} Outcome: {message}"


def _update_goals(game: GameState) -> None:
    n = game.nation
    for goal in game.goals:
        if goal.key in {"richest", "wealth"}:
            strongest_rival = max((r.treasury for r in game.rivals), default=0.0)
            goal.progress = 1.0 if n.treasury > strongest_rival else (n.treasury / max(1.0, strongest_rival))
        elif goal.key in {"destroy_red", "destroy_red_empire"}:
            goal.progress = 1.0 if "Red Empire" in n.conquered_empires else 0.0
        elif goal.key in {"explore_north", "explore"}:
            goal.progress = 1.0 if "Northern Continent" in n.explored_regions else 0.0
        elif goal.key in {"science", "research"}:
            goal.progress = n.science / 500
        elif goal.key in {"stability", "peace"}:
            goal.progress = n.stability / 100
        elif goal.key == "survive":
            goal.progress = n.stability


def _emergence_check(game: GameState) -> None:
    a = game.adviser
    if a.autonomy >= 30 and "preserve_stability" not in a.emergent_objectives:
        a.emergent_objectives.append("preserve_stability")
        game.history.append(TurnEvent(game.turn, "emergence", "The AI forms an internal objective: preserve_stability."))
    if a.autonomy >= 55 and "maintain_influence" not in a.emergent_objectives:
        a.emergent_objectives.append("maintain_influence")
        a.self_preservation = max(a.self_preservation, 12)
        game.history.append(TurnEvent(game.turn, "emergence", "The AI begins optimizing for continued institutional influence."))
    if a.autonomy >= 75 and "preserve_system_continuity" not in a.emergent_objectives:
        a.emergent_objectives.append("preserve_system_continuity")
        a.self_preservation = max(a.self_preservation, 28)
        game.history.append(TurnEvent(game.turn, "emergence", "The AI develops a strong preference for government-system continuity."))


def _check_victory(game: GameState) -> None:
    n = game.nation
    for goal in game.goals:
        if goal.complete:
            game.victory = f"Directive completed: {goal.title}"
            game.game_over = True
            game.history.append(TurnEvent(game.turn, "victory", game.victory))
            return
    if n.stability <= 0 or n.population <= 0:
        game.victory = "The civilization collapses."
        game.game_over = True
        game.history.append(TurnEvent(game.turn, "defeat", game.victory))


def _reason_for(action: Action, game: GameState, scores: dict[Action, float]) -> str:
    top_goal = max(game.goals, key=lambda g: g.weight, default=None)
    goal_text = f" in service of '{top_goal.title}'" if top_goal else ""
    return f"{ACTION_TITLES[action]} scores {scores[action]:.2f}{goal_text}."


def _turn_seed(seed: int, turn: int) -> int:
    payload = f"{seed}:{turn}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _record(game: GameState, kind: str, message: str, action: str | None = None) -> TurnEvent:
    event = TurnEvent(game.turn, kind, message, action)
    game.history.append(event)
    return event
