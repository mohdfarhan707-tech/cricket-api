"""Shared helpers for fetching and applying CricAPI scorecard data to Match."""
import requests
from .models import Match

CRICAPI_KEY = "9c2c729f-9194-4b1d-bc69-6aa5a16dde1e"


def _team_from_inning(inning_str):
    s = (inning_str or "").strip()
    for sep in (" Inning 1", " Innings 1", " Inning 2", " Innings 2", " Inning"):
        if sep in s:
            return s.split(sep)[0].strip()
    return s


def _is_first_innings(inning_str: str) -> bool:
    """True if this inning label is the first (batting first) innings."""
    s = (inning_str or "").lower()
    return "inning 1" in s or "innings 1" in s or "1st inning" in s or "1st innings" in s


def apply_scorecard_to_match(match: Match, scorecard: dict) -> None:
    """Update match with scorecard data. Batting-first team is always team_home (left)."""
    match.scorecard_data = scorecard
    match.status = scorecard.get("status") or match.status
    scores = scorecard.get("score") or []
    if len(scores) >= 2:
        s0, s1 = scores[0], scores[1]
        # API may return [1st, 2nd] or [2nd, 1st]; detect so batting first is always left
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
    match.save(update_fields=["scorecard_data", "status", "team_home", "team_away", "home_score", "away_score"])


def fetch_scorecard(match_id: str) -> dict | None:
    """Fetch scorecard from CricAPI. Returns scorecard dict or None on failure."""
    url = f"https://api.cricapi.com/v1/match_scorecard?apikey={CRICAPI_KEY}&id={match_id}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data.get("status") != "success":
            return None
        return data.get("data") or {}
    except Exception:
        return None
