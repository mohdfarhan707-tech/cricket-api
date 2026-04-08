"""Helpers for fetching live scorecards with a separate API key."""

import re
import requests
from .models import LiveMatch

# Non-IPL live matches + scorecards
LIVE_CRICAPI_KEY = "6453a7cb-133e-443e-9e4a-cffa1370393f"
# IPL-only (currentMatches + scorecards for those rows)
LIVE_CRICAPI_KEY_IPL = "32791bbc-e8fa-4e2c-8e25-804ce118da58"

_IPL_WORD = re.compile(r"\bipl\b", re.IGNORECASE)


def is_ipl_current_match_item(item: dict) -> bool:
    """True if this currentMatches row is treated as IPL (Indian Premier League)."""
    parts: list[str] = []
    name = item.get("name")
    if name:
        parts.append(str(name))
    series = item.get("series")
    if isinstance(series, dict):
        parts.append(str(series.get("name") or ""))
    else:
        parts.append(str(series or ""))
    parts.append(str(item.get("seriesName") or ""))
    blob = " ".join(parts).lower()
    if "indian premier league" in blob:
        return True
    return bool(_IPL_WORD.search(blob))


def fetch_current_matches_batches(api_key: str) -> list[dict]:
    """Paginated currentMatches for one API key; de-duplicated by match id."""
    all_items: list[dict] = []
    for offset in (0, 25):
        url = f"https://api.cricapi.com/v1/currentMatches?apikey={api_key}&offset={offset}"
        try:
            resp = requests.get(url, timeout=8)
            root = resp.json() or {}
            batch = root.get("data") or root.get("matches") or []
            if isinstance(batch, list):
                all_items.extend(batch)
        except Exception:
            continue
    seen: set[str] = set()
    out: list[dict] = []
    for item in all_items:
        if not isinstance(item, dict):
            continue
        mid = item.get("id") or item.get("unique_id")
        if not mid:
            continue
        sid = str(mid)
        if sid in seen:
            continue
        seen.add(sid)
        out.append(item)
    return out


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


def apply_scorecard_to_live_match(
    match: LiveMatch, scorecard: dict, *, persist_full_scorecard: bool
) -> None:
    """
    Update snapshot fields from the latest scorecard payload.

    For in-progress matches, persist_full_scorecard should be False so we do not
    keep a stale partial JSON blob (e.g. only first innings) in the DB. For
    finished matches, True stores the full scorecard permanently.
    """
    if persist_full_scorecard:
        match.scorecard_data = scorecard
    else:
        match.scorecard_data = None

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

    if not match.is_finished:
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


def _fetch_scorecard_with_key(api_key: str, match_id: str) -> dict | None:
    url = f"https://api.cricapi.com/v1/match_scorecard?apikey={api_key}&id={match_id}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json() or {}
        if data.get("status") != "success":
            return None
        return data.get("data") or {}
    except Exception:
        return None


def fetch_live_scorecard(match_id: str) -> tuple[dict | None, bool]:
    """
    Fetch full scorecard. Returns (data, used_ipl_key).
    Order of keys follows LiveMatch.uses_ipl_api when a row exists.
    """
    sid = str(match_id)
    row = LiveMatch.objects.filter(external_id=sid).first()
    if row and row.uses_ipl_api:
        order = [(LIVE_CRICAPI_KEY_IPL, True), (LIVE_CRICAPI_KEY, False)]
    else:
        order = [(LIVE_CRICAPI_KEY, False), (LIVE_CRICAPI_KEY_IPL, True)]
    for key, is_ipl in order:
        data = _fetch_scorecard_with_key(key, sid)
        if data is not None:
            if row and row.uses_ipl_api != is_ipl:
                row.uses_ipl_api = is_ipl
                row.save(update_fields=["uses_ipl_api"])
            return data, is_ipl
    return None, False

