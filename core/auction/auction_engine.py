"""
Mini auction rules: increments, reserve budget, auto-bid helpers.
Budgets in LAKHS (₹1 Cr = 100 lakhs).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import AuctionSession, AuctionTeam

# ₹50 Cr = 5000 lakhs
DEFAULT_BUDGET_LAKHS = 5000
MIN_SQUAD = 14
MAX_SQUAD = 18
PLAYER_MIN_LAKHS = 30
# Only these base prices: 30L, 40L, 50L, 75L, 1 Cr, 1.5 Cr, 2 Cr (lakhs)
ALLOWED_BASE_PRICE_LAKHS = (30, 40, 50, 75, 100, 150, 200)
PLAYER_MAX_LAKHS = max(ALLOWED_BASE_PRICE_LAKHS)

# Every N players in order: enforce unsold count in [WINDOW_UNSOLD_MIN, WINDOW_UNSOLD_MAX]
AUCTION_WINDOW_SIZE = 30
WINDOW_UNSOLD_MIN = 1
WINDOW_UNSOLD_MAX = 4


def bid_increment(current_lakhs: int) -> int:
    """Before ₹1 Cr: +10L; ₹1 Cr–₹10 Cr: +25L; after ₹10 Cr: +50L."""
    if current_lakhs < 100:
        return 10
    if current_lakhs < 1000:
        return 25
    return 50


def next_bid_amount(current_lakhs: int) -> int:
    return current_lakhs + bid_increment(current_lakhs)


def min_reserve_after_buy(squad_count_after: int) -> int:
    """Minimum budget to keep so minimum squad (14) can still be completed at ₹30L each."""
    if squad_count_after >= MIN_SQUAD:
        return 0
    need = MIN_SQUAD - squad_count_after
    return need * PLAYER_MIN_LAKHS


def max_bid_allowed(budget_lakhs: int, squad_count: int) -> int:
    """Max price this team can pay for the next player (before buying)."""
    after_buy = squad_count + 1
    reserve = min_reserve_after_buy(after_buy)
    return budget_lakhs - reserve


def random_timer_seconds() -> int:
    return 10


def autobid_probability(strategy: str, category_match_bonus: float = 0.0) -> float:
    """Higher floor so all franchises stay active in bidding from the first lot."""
    base = {"aggressive": 0.78, "balanced": 0.58, "defensive": 0.42}.get(strategy, 0.52)
    return min(0.92, base + category_match_bonus)


def category_interest_bonus(team, player_category: str) -> float:
    """Use team's interest JSON if present."""
    raw = getattr(team, "category_interest", None) or {}
    if not isinstance(raw, dict):
        return 0.0
    key = (player_category or "").lower().replace(" ", "_").replace("-", "_")
    mapping = {
        "batsman": "batsman",
        "bowler": "bowler",
        "all-rounder": "allrounder",
        "allrounder": "allrounder",
        "wk": "wk",
        "wicketkeeper": "wk",
    }
    k = mapping.get(key, "batsman")
    return float(raw.get(k, 0.35)) * 0.15  # scale into probability bonus
