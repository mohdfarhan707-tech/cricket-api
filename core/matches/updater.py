import requests
import time
from .models import Series, Match


_LAST_UPDATE_AT = 0.0


def _fetch_match_score(match_id: str, api_key: str):
    """
    Best‑effort helper to fetch scores for a given match.

    CricAPI/CricketData score endpoints typically return team names (t1, t2)
    and score strings (t1s, t2s). We try to read those, but fall back
    gracefully if the shape is different.
    """
    try:
        score_url = f"https://api.cricapi.com/v1/cricketScore?apikey={api_key}&id={match_id}"
        resp = requests.get(score_url, timeout=5)
        payload = resp.json() or {}
        if payload.get("status") == "failure":
            return None, None, None, None

        # Some responses nest under "data", some are top‑level
        data = payload.get("data") or payload

        team1 = data.get("t1")
        team2 = data.get("t2")
        team1_score = data.get("t1s")
        team2_score = data.get("t2s")

        # Fallbacks in case the API returns a slightly different shape
        if not team1_score:
            team1_score = data.get("score") or data.get("s1") or "0"
        if not team2_score:
            team2_score = data.get("s2") or "0"

        return team1, team2, team1_score, team2_score
    except Exception:
        # On any error just signal that we could not fetch scores
        return None, None, None, None


def _format_score_entry(entry) -> str | None:
    if not isinstance(entry, dict):
        return None
    r = entry.get("r") or entry.get("runs")
    w = entry.get("w") or entry.get("wkts") or entry.get("wickets")
    o = entry.get("o") or entry.get("overs")
    if r is None:
        return None
    s = str(r)
    if w is not None:
        s += f"/{w}"
    if o is not None:
        s += f" ({o} ov)"
    return s


def _extract_scores_from_match(m: dict) -> tuple[str | None, str | None]:
    """
    Try to extract home/away scores directly from the `series_info.matchList` item.
    This avoids making dozens of extra API calls and getting rate-limited.
    """
    score = m.get("score")
    if isinstance(score, list) and score:
        # Often the API provides a list of innings scores; use first two entries.
        s1 = _format_score_entry(score[0])
        s2 = _format_score_entry(score[1]) if len(score) > 1 else None
        return s1, s2

    # Common alternative shapes
    s1 = m.get("t1s") or m.get("score1") or m.get("s1")
    s2 = m.get("t2s") or m.get("score2") or m.get("s2")
    return (str(s1) if s1 else None), (str(s2) if s2 else None)


def update_cricket_data():
    global _LAST_UPDATE_AT
    now = time.time()
    if now - _LAST_UPDATE_AT < 60:
        return

    API_KEY = "9c2c729f-9194-4b1d-bc69-6aa5a16dde1e"
    # Only keep this series in the DB
    TOURNAMENT_IDS = ["5978f057-af70-4dcf-b9ee-04831b8df947"]

    # Delete old series (and their matches via cascade)
    Series.objects.exclude(external_id__in=TOURNAMENT_IDS).delete()

    for series_id in TOURNAMENT_IDS:
        url = f"https://api.cricapi.com/v1/series_info?apikey={API_KEY}&id={series_id}"
        response = requests.get(url, timeout=10)
        root = response.json() or {}
        if root.get("status") == "failure":
            continue

        # Some versions nest under `data`, others put it at top-level
        data = root.get("data") or root

        if not data:
            continue

        # 1. Update Series
        series_obj, _ = Series.objects.update_or_create(
            external_id=series_id,
            defaults={"name": data.get("info", {}).get("name", "Tournament")},
        )

        # 2. Update Matches + scores
        for m in data.get("matchList", []):
            match_id = m.get("id")
            if not match_id:
                continue

            # Base info from the series endpoint
            team_home = m.get("teams", [None, None])[0]
            team_away = m.get("teams", [None, None])[1]
            home_score = None
            away_score = None

            # Prefer scores embedded in series_info to avoid rate limits
            hs, as_ = _extract_scores_from_match(m)
            home_score = hs or home_score
            away_score = as_ or away_score

            # Optional enrichment (very limited) for live matches only
            status = (m.get("status") or "").lower()
            if (not home_score or not away_score) and ("live" in status):
                t1, t2, t1s, t2s = _fetch_match_score(match_id, API_KEY)
                if t1s or t2s:
                    home_score = t1s or home_score
                    away_score = t2s or away_score
                if t1 and t2:
                    team_home = t1
                    team_away = t2

            Match.objects.update_or_create(
                external_id=match_id,
                defaults={
                    "series": series_obj,
                    "name": m.get("name") or "",
                    "status": m.get("status", "Upcoming"),
                    "team_home": team_home or "",
                    "team_away": team_away or "",
                    "home_score": home_score or "",
                    "away_score": away_score or "",
                },
            )

    _LAST_UPDATE_AT = now