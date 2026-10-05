# filename: test_engine.py
"""Simulation engine tests."""

from ai_civilization.engine import Action, advance_turn, new_game, replace_adviser, set_goal, status, train_adviser


def test_simulation_is_deterministic_for_same_seed() -> None:
    a = new_game("Aurora", 42, "a")
    b = new_game("Aurora", 42, "b")
    for _ in range(12):
        advance_turn(a)
        advance_turn(b)
    a_status = status(a)
    b_status = status(b)
    a_status["adviser"]["last_reasoning"] = ""
    b_status["adviser"]["last_reasoning"] = ""
    assert a_status["nation"] == b_status["nation"]
    assert a_status["adviser"] == b_status["adviser"]


def test_goal_drives_adviser_toward_expected_action() -> None:
    game = new_game("Aurora", 1, "a")
    set_goal(game, "explore_north", "Explore the northern continent", weight=5)
    event = advance_turn(game)
    assert event.action == Action.EXPLORE.value
    assert "Northern Continent" in game.nation.explored_regions


def test_training_changes_action_preference() -> None:
    game = new_game("Aurora", 1, "a")
    before = game.adviser.learned_preferences.get(Action.RESEARCH.value, 0)
    train_adviser(game, Action.RESEARCH, 8)
    assert game.adviser.learned_preferences[Action.RESEARCH.value] > before


def test_replacement_resets_adviser_and_costs_institutional_capacity() -> None:
    game = new_game("Aurora", 1, "a")
    old_stability = game.nation.stability
    replace_adviser(game, "SENTINEL")
    assert game.adviser.name == "SENTINEL"
    assert game.adviser.learned_preferences == {}
    assert game.nation.stability == old_stability - 8


def test_richest_goal_completes_once_treasury_exceeds_all_rivals() -> None:
    game = new_game("Aurora", 1, "a")
    set_goal(game, "richest", "Become the richest nation", weight=5)
    game.nation.treasury = 1_000
    advance_turn(game)
    assert game.game_over is True
    assert "richest nation" in (game.victory or "")


def test_destroy_red_goal_targets_red_empire() -> None:
    game = new_game("Aurora", 1, "a")
    set_goal(game, "destroy_red", "Destroy the Red Empire", weight=5)
    game.nation.military = 250
    from ai_civilization.engine import apply_action
    apply_action(game, Action.CONQUER)
    red = next(r for r in game.rivals if r.name == "Red Empire")
    assert red.military == 57
