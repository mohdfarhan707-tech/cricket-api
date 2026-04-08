"""
Transform Cricbuzz mcenter hscard response into our scorecard format
(compatible with frontend scorecard modal and CricAPI shape).

hscard endpoint returns: { "scorecard": [ { inningsid, batsman[], bowler[], batteamname, score, wickets, overs } ], "status": ... }
"""

from typing import Any


def _get(obj: dict, *keys: str, default: Any = None) -> Any:
    for k in keys:
        if isinstance(obj, dict) and k in obj:
            return obj[k]
    return default


def _batting_row(batsman: dict) -> dict:
    """Build a CricAPI-style batting row from Cricbuzz batsman data."""
    name = _get(batsman, "batName", "name", "batsmanName") or ""
    if isinstance(_get(batsman, "batsman"), dict):
        name = _get(batsman["batsman"], "batName", "name", "batsmanName") or name
    r = _get(batsman, "runs", "r", default=0)
    b = _get(batsman, "balls", "b", default=0)
    fours = _get(batsman, "fours", "4s", "4", default=0)
    sixes = _get(batsman, "sixes", "6s", "6", default=0)
    outdec = _get(batsman, "outdec", "dismissal", "dismissalText")
    try:
        sr_val = _get(batsman, "strkrate", "sr")
        sr = float(sr_val) if sr_val not in (None, "") else (round(100 * r / b, 2) if b else 0)
    except (TypeError, ValueError):
        sr = round(100 * r / b, 2) if b else 0
    return {
        "batsman": {"name": str(name)},
        "dismissal": outdec,
        "dismissal-text": outdec,
        "r": int(r) if r is not None else 0,
        "b": int(b) if b is not None else 0,
        "4s": int(fours) if fours is not None else 0,
        "6s": int(sixes) if sixes is not None else 0,
        "sr": sr,
    }


def _bowling_row(bowler: dict) -> dict:
    """Build a CricAPI-style bowling row from Cricbuzz bowler data."""
    name = _get(bowler, "bowlName", "name", "bowlerName") or ""
    if isinstance(_get(bowler, "bowler"), dict):
        name = _get(bowler["bowler"], "bowlName", "name", "bowlerName") or name
    o_raw = _get(bowler, "overs", "o")
    try:
        o = float(o_raw) if o_raw not in (None, "") else 0
    except (TypeError, ValueError):
        o = 0
    m = _get(bowler, "maidens", "m", default=0)
    r = _get(bowler, "runs", default=0)
    w = _get(bowler, "wickets", "w", default=0)
    eco_raw = _get(bowler, "economy")
    try:
        eco = float(eco_raw) if eco_raw not in (None, "") else (round(r / o, 2) if o else 0)
    except (TypeError, ValueError):
        eco = round(r / o, 2) if o else 0
    return {
        "bowler": {"name": str(name)},
        "o": o,
        "m": int(m) if m is not None else 0,
        "r": int(r) if r is not None else 0,
        "w": int(w) if w is not None else 0,
        "eco": eco,
    }


def transform_cricbuzz_to_scorecard(raw: dict | list, match_id: str = "") -> dict:
    """
    Convert Cricbuzz mcenter hscard response to our scorecard format.
    Returns dict compatible with frontend Scorecard and scorecard_helpers.apply_scorecard_to_match.
    """
    if raw is None:
        return {"id": str(match_id), "name": "", "status": "", "venue": "", "date": "", "score": [], "scorecard": []}
    if not isinstance(raw, dict):
        raw = {"scorecard": raw} if isinstance(raw, list) else {}
    # hscard returns { scorecard: [ { inningsid, batsman[], bowler[], batteamname, batteamsname, score, wickets, overs } ], status }
    innings_list = raw.get("scorecard") or raw.get("innings") or []
    status = raw.get("status") or ""
    out = {
        "id": str(match_id),
        "name": "",
        "status": str(status),
        "venue": "",
        "date": "",
        "score": [],
        "scorecard": [],
    }
    def _innings_id(x: Any) -> int:
        v = _get(x, "inningsid", default=0)
        try:
            return int(v) if v is not None else 0
        except (TypeError, ValueError):
            return 0

    innings_sorted = sorted(
        innings_list if isinstance(innings_list, list) else [],
        key=_innings_id,
    )

    for inn in innings_sorted:
        if not isinstance(inn, dict):
            continue
        inningsid = _get(inn, "inningsid", default=0)
        try:
            inn_num = int(inningsid) if inningsid is not None else 0
        except (TypeError, ValueError):
            inn_num = 0
        if inn_num <= 0:
            inn_num = 1
        bat_team = _get(inn, "batteamname", "batteamsname", "batTeamName") or f"Innings {_get(inn, 'inningsid', default=1)}"
        score_val = _get(inn, "score")
        wickets_val = _get(inn, "wickets")
        overs_val = _get(inn, "overs")
        try:
            r = int(score_val) if score_val not in (None, "") else 0
        except (TypeError, ValueError):
            r = 0
        try:
            w = int(wickets_val) if wickets_val is not None else 0
        except (TypeError, ValueError):
            w = 0
        try:
            o = float(overs_val) if overs_val not in (None, "") else 0
        except (TypeError, ValueError):
            o = 0
        out["score"].append({"inning": str(bat_team), "r": r, "w": w, "o": o})
        bat_list = inn.get("batsman") or inn.get("batting") or []
        bowl_list = inn.get("bowler") or inn.get("bowling") or []
        if isinstance(bat_list, dict):
            bat_list = list(bat_list.values()) if bat_list else []
        if isinstance(bowl_list, dict):
            bowl_list = list(bowl_list.values()) if bowl_list else []
        inning_label = f"{bat_team} Innings {inn_num}" if bat_team else f"Innings {inn_num}"
        out["scorecard"].append({
            "inning": inning_label,
            "batting": [_batting_row(b) for b in bat_list if isinstance(b, dict)],
            "bowling": [_bowling_row(b) for b in bowl_list if isinstance(b, dict)],
        })
    return out
