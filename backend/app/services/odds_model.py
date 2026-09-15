from typing import Optional

RECENT_GAMES_WINDOW = 10
PRIOR_WEIGHT = 6  # how many "phantom games" of weight the position-default prior carries
MARGIN = 0.07  # bookmaker-style overround

MARKET_PREDICATES = {
    "yellow_card": lambda g: g.get("yellow_cards", 0) >= 1,
    "red_card": lambda g: g.get("red_cards", 0) >= 1,
    "anytime_scorer": lambda g: g.get("goals_scored", 0) >= 1,
    "assist": lambda g: g.get("assists", 0) >= 1,
    "defensive_actions_5plus": lambda g: g.get("defensive_contribution", 0) >= 5,
    "clean_sheet": lambda g: g.get("goals_conceded", 0) == 0,
    "saves_3plus": lambda g: g.get("saves", 0) >= 3,
}

# Position-based priors — used as the "default" belief before we see any
# real games, and blended in as a fixed weight alongside observed data.
DEFAULT_PROBABILITIES = {
    "yellow_card": 0.18,
    "red_card": 0.02,
    "anytime_scorer": {"FWD": 0.35, "MID": 0.15, "DEF": 0.05, "GK": 0.01},
    "assist": {"FWD": 0.15, "MID": 0.15, "DEF": 0.05, "GK": 0.01},
    "defensive_actions_5plus": {"DEF": 0.35, "MID": 0.15, "FWD": 0.03, "GK": 0.01},
    "clean_sheet": {"GK": 0.30, "DEF": 0.30, "MID": 0.05, "FWD": 0.0},
    "saves_3plus": {"GK": 0.30},
}

POSITION_RESTRICTIONS = {
    "saves_3plus": {"GK"},
    "clean_sheet": {"GK", "DEF", "MID"},
}


def _played_games(history: list[dict]) -> list[dict]:
    return [g for g in history if g.get("minutes", 0) > 0]


def probability_to_decimal_odds(probability: float, margin: float = MARGIN) -> float:
    probability = max(min(probability, 0.98), 0.02)
    implied_with_margin = min(probability * (1 + margin), 0.99)
    return round(1 / implied_with_margin, 2)


def calculate_market_odds(market_code: str, history: list[dict], position: str) -> Optional[dict]:
    predicate = MARKET_PREDICATES.get(market_code)
    if predicate is None:
        return None

    allowed_positions = POSITION_RESTRICTIONS.get(market_code)
    if allowed_positions and position not in allowed_positions:
        return None

    default = DEFAULT_PROBABILITIES.get(market_code)
    prior_probability = default.get(position, 0.1) if isinstance(default, dict) else default
    if prior_probability is None:
        return None

    recent = _played_games(history[-RECENT_GAMES_WINDOW:])
    sample_size = len(recent)
    hits = sum(1 for g in recent if predicate(g))

    # Shrinkage estimator: the prior acts as PRIOR_WEIGHT "phantom" games,
    # so with 0 real games probability == prior_probability exactly, and
    # as sample_size grows past PRIOR_WEIGHT, real form dominates.
    probability = (prior_probability * PRIOR_WEIGHT + hits) / (PRIOR_WEIGHT + sample_size)

    return {
        "market_code": market_code,
        "probability": round(probability, 3),
        "odds_decimal": probability_to_decimal_odds(probability),
        "sample_size": sample_size,
    }