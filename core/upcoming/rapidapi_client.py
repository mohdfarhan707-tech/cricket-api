import requests

# RapidAPI key for Cricbuzz (upcoming, series schedules, IPL/PSL points, team/squad, BBL series, etc.)
RAPIDAPI_KEY_UPCOMING = "67cd391ccamsh3c9b9bd28cb6e24p12ac13jsn694f736eae1f"
RAPIDAPI_HOST = "cricbuzz-cricket.p.rapidapi.com"


def fetch_upcoming_raw() -> dict | None:
    url = f"https://{RAPIDAPI_HOST}/matches/v1/upcoming"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY_UPCOMING,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        data = resp.json() if resp.content else {}
        if resp.status_code >= 400:
            return None
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def fetch_series_raw(series_id: str) -> dict | None:
    url = f"https://{RAPIDAPI_HOST}/series/v1/{series_id}"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY_UPCOMING,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        data = resp.json() if resp.content else {}
        if resp.status_code >= 400:
            # Surface RapidAPI errors (quota/401/403) instead of silently returning None.
            try:
                snippet = (resp.text or "")[:500]
            except Exception:
                snippet = ""
            print(f"Cricbuzz series API error {resp.status_code}: {snippet}")
            return None
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def fetch_mcenter_raw(match_id: str) -> dict | list | None:
    """Fetch match center scorecard from Cricbuzz RapidAPI hscard endpoint (for BBL etc)."""
    url = f"https://{RAPIDAPI_HOST}/mcenter/v1/{match_id}/hscard"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY_UPCOMING,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        data = resp.json() if resp.content else None
        if resp.status_code >= 400:
            return None
        # hscard can return dict or list of innings
        return data if isinstance(data, (dict, list)) else None
    except Exception:
        return None


def fetch_team_players_raw(team_id: str) -> dict | None:
    url = f"https://{RAPIDAPI_HOST}/teams/v1/{team_id}/players"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY_UPCOMING,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        data = resp.json() if resp.content else {}
        if resp.status_code >= 400:
            return None
        return data if isinstance(data, dict) else None
    except Exception:
        return None

