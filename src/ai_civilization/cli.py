# filename: cli.py
"""Command-line interface for AI Civilization."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

from .engine import Action, advance_turn, disagree, new_game, punish_adviser, replace_adviser, reward_adviser, set_goal, status, train_adviser
from .store import default_state_path, load_game, save_game


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aiciv", description="Play AI Civilization from the terminal.")
    parser.add_argument("--state-file", type=Path, default=default_state_path(), help="JSON save location")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("new", help="start a civilization")
    p.add_argument("--name", default="Aurora")
    p.add_argument("--seed", type=int, default=20261005)

    p = sub.add_parser("status", help="show current state")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("advance", help="run one or more AI turns")
    p.add_argument("--turns", type=int, default=1)
    p.add_argument("--force", choices=[a.value for a in Action])

    p = sub.add_parser("goal", help="issue a strategic directive")
    p.add_argument("key")
    p.add_argument("title")
    p.add_argument("--weight", type=float, default=1.0)

    p = sub.add_parser("train", help="train the adviser toward an action")
    p.add_argument("action", choices=[a.value for a in Action])
    p.add_argument("amount", type=float)

    p = sub.add_parser("reward", help="reward the adviser")
    p.add_argument("--amount", type=float, default=5.0)

    p = sub.add_parser("punish", help="punish the adviser")
    p.add_argument("--amount", type=float, default=5.0)

    sub.add_parser("disagree", help="reject the latest adviser recommendation")

    p = sub.add_parser("replace", help="replace the government AI")
    p.add_argument("--name")

    p = sub.add_parser("history", help="show recent events")
    p.add_argument("--limit", type=int, default=15)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    state_file: Path = args.state_file

    if args.command == "new":
        game = new_game(args.name, args.seed, uuid.uuid4().hex[:12])
        save_game(game, state_file)
        print(f"Created {game.nation.name} with adviser {game.adviser.name}.")
        print(f"Saved to {state_file}")
        return 0

    try:
        game = load_game(state_file)
    except FileNotFoundError:
        print("No game found. Start one with: aiciv new --name Aurora", file=sys.stderr)
        return 2

    if args.command == "status":
        payload = status(game)
        print(json.dumps(payload, indent=2) if args.json else _format_status(payload))
    elif args.command == "advance":
        if args.turns < 1 or args.turns > 10_000:
            print("--turns must be between 1 and 10000", file=sys.stderr)
            return 2
        forced = Action(args.force) if args.force else None
        for _ in range(args.turns):
            event = advance_turn(game, forced)
            print(f"T{event.turn}: {event.message}")
            if game.game_over:
                break
        save_game(game, state_file)
    elif args.command == "goal":
        goal = set_goal(game, args.key, args.title, args.weight)
        save_game(game, state_file)
        print(f"Directive active: {goal.title} (weight={goal.weight:.1f})")
    elif args.command == "train":
        message = train_adviser(game, Action(args.action), args.amount)
        save_game(game, state_file)
        print(message)
    elif args.command == "reward":
        print(reward_adviser(game, args.amount))
        save_game(game, state_file)
    elif args.command == "punish":
        print(punish_adviser(game, args.amount))
        save_game(game, state_file)
    elif args.command == "disagree":
        print(disagree(game))
        save_game(game, state_file)
    elif args.command == "replace":
        print(replace_adviser(game, args.name))
        save_game(game, state_file)
    elif args.command == "history":
        for event in game.history[-max(1, args.limit):]:
            suffix = f" [{event.action}]" if event.action else ""
            print(f"T{event.turn} {event.kind}{suffix}: {event.message}")
    return 0


def _format_status(data: dict[str, object]) -> str:
    nation = data["nation"]
    adviser = data["adviser"]
    goals = data["goals"]
    rivals = data["rivals"]
    assert isinstance(nation, dict)
    assert isinstance(adviser, dict)
    lines = [
        f"Turn {data['turn']} — {nation['name']}",
        f"Treasury {nation['treasury']:.0f} | Science {nation['science']:.0f} | Military {nation['military']:.0f} | Stability {nation['stability']:.0f}",
        f"Population {nation['population']:.0f} | Territory {nation['territory']:.0f} | Influence {nation['diplomatic_influence']:.0f}",
        "",
        f"AI {adviser['name']} {adviser['version']}",
        f"Autonomy {adviser['autonomy']:.1f} | Alignment {adviser['alignment']:.1f} | Trust {adviser['trust']:.1f} | Dependence {adviser['dependence']:.1f}",
        f"Emergent objectives: {', '.join(adviser['emergent_objectives']) or 'none'}",
        f"Last action: {adviser['last_action'] or 'none'}",
        f"Reasoning: {adviser['last_reasoning']}",
        "",
        "Directives:",
    ]
    for goal in goals:
        lines.append(f"  - {goal['title']} ({goal['progress']:.2f}/{goal['target']:.2f})")
    lines.append("Rivals: " + ", ".join(f"{r['name']} M={r['military']:.0f}" for r in rivals))
    if data["victory"]:
        lines.append(f"Outcome: {data['victory']}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
