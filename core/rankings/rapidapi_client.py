import requests
from django.conf import settings

# Prefer environment / Django settings — do not commit live API keys to the repo.
def _api_key() -> str:
    return (getattr(settings, "RAPIDAPI_KEY", None) or "").strip()


def _api_host() -> str:
    return (getattr(settings, "RAPIDAPI_HOST", None) or "cricbuzz-cricket.p.rapidapi.com").strip()


def fetch_rankings(kind: str, format_type: str) -> dict | None:
    """
    Fetch rankings from RapidAPI Cricbuzz.

    kind: teams | batsmen | bowlers | allrounders
    format_type: odi | t20 | test
    """
    key = _api_key()
    if not key:
        return None

    host = _api_host()
    url = f"https://{host}/stats/v1/rankings/{kind}"
    headers = {
        "X-RapidAPI-Key": key,
        "X-RapidAPI-Host": host,
    }
    params = {"formatType": format_type}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        data = resp.json() if resp.content else {}
        if resp.status_code >= 400:
            return None
        return data if isinstance(data, dict) else None
    except Exception:
        return None
