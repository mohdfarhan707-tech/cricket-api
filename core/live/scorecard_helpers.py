"""Helpers for fetching live scorecards with a separate API key."""

import requests
from .models import LiveMatch

LIVE_CRICAPI_KEY = "6453a7cb-133e-443e-9e4a-cffa1370393f"


def _team_from_inning(inning_str: str) -> str:
    s = (inning_str or "").strip()
    for sep in (" Inning 1", " Innings 1", " Inning 2", " Innings 2", " Inning"):
        if sep in s:
            return s.split(sep)[0].strip()
    return s


def _is_first_innings(inning_str: str) -> bool:
    s = (inning_str or "").lower()
    return (
        "inning 1" in s
        or "innings 1" in s
        or "1st inning" in s
        or "1st innings" in s
    )


def apply_scorecard_to_live_match(match: LiveMatch, scorecard: dict) -> None:
    """Ensure batting-first team is stored on the left for live matches."""
    match.scorecard_data = scorecard
    match.status = scorecard.get("status") or match.status
    scores = scorecard.get("score") or []

    if len(scores) >= 2:
        s0, s1 = scores[0], scores[1]
        if _is_first_innings(s0.get("inning") or ""):
            first, second = s0, s1
        else:
            first, second = s1, s0
        match.team_home = _team_from_inning(first.get("inning")) or match.team_home
        match.team_away = _team_from_inning(second.get("inning")) or match.team_away
        match.home_score = f"{first.get('r', 0)}/{first.get('w', 0)}"
        match.away_score = f"{second.get('r', 0)}/{second.get('w', 0)}"
    elif len(scores) == 1:
        match.team_home = _team_from_inning(scores[0].get("inning")) or match.team_home
        match.home_score = f"{scores[0].get('r', 0)}/{scores[0].get('w', 0)}"

    match.is_live = True
    match.save(
        update_fields=[
            "scorecard_data",
            "status",
            "team_home",
            "team_away",
            "home_score",
            "away_score",
            "is_live",
        ]
    )


def fetch_live_scorecard(match_id: str) -> dict | None:
    """Fetch full scorecard for a live match from CricAPI."""
    url = f"https://api.cricapi.com/v1/match_scorecard?apikey={LIVE_CRICAPI_KEY}&id={match_id}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json() or {}
        if data.get("status") != "success":
            return None
        return data.get("data") or {}
    except Exception:
        return None

