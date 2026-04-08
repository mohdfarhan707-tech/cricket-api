"""
Build IPL/PSL-style points tables from Cricbuzz `series/v1/<id>` payloads.
Uses completed matches + matchScore innings for wins/losses/NR and NRR.
"""

from __future__ import annotations

from typing import Any, Iterator

# Cricbuzz series ids (aligned with `fetch_upcoming` for IPL/PSL fixtures)
SERIES_ID_IPL = "9241"
SERIES_ID_PSL = "11537"


def series_name_from_payload(series_data: dict) -> str:
    for m in iter_series_match_entries(series_data):
        mi = m.get("matchInfo") or {}
        if isinstance(mi, dict):
            name = (mi.get("seriesName") or "").strip()
            if name:
                return name
    return ""


def iter_series_match_entries(series_data: dict) -> Iterator[dict]:
    for md in series_data.get("matchDetails") or []:
        if not isinstance(md, dict):
            continue
        mdm = md.get("matchDetailsMap")
        if not isinstance(mdm, dict):
            continue
        for match in mdm.get("match") or []:
            if isinstance(match, dict) and match.get("matchInfo"):
                yield match


def _overs_to_balls(overs: Any) -> int:
    if overs is None:
        return 0
    try:
        f = float(overs)
    except (TypeError, ValueError):
        return 0
    s = f"{f:.10f}".rstrip("0").rstrip(".")
    if "." not in s:
        return int(float(s)) * 6
    whole, frac = s.split(".", 1)
    w = int(whole) if whole else 0
    digit = int(frac[0]) if frac and frac[0].isdigit() else 0
    return w * 6 + min(digit, 5)


def _classify_result(status: str, t1: str, t2: str) -> tuple[str, str | None, str | None]:
    """
    Returns (kind, winner, loser) where kind is win | nr | tie | pending.
    """
    st = (status or "").strip()
    low = st.lower()
    if any(x in low for x in ("abandon", "no result", "called off", "match abandoned")):
        return "nr", None, None
    if "tie" in low and "won" not in low:
        return "tie", None, None
    idx = st.find(" won")
    if idx == -1:
        return "pending", None, None
    cand = st[:idx].strip()
    if cand == t1:
        return "win", t1, t2
    if cand == t2:
        return "win", t2, t1
    return "pending", None, None


def _ing_score(ms: dict, side: str) -> tuple[int, int]:
    block = (ms.get(f"{side}Score") or {}) if isinstance(ms, dict) else {}
    inn = block.get("inngs1") or {}
    if not isinstance(inn, dict):
        return 0, 0
    runs = inn.get("runs")
    overs = inn.get("overs")
    try:
        r = int(runs) if runs is not None else 0
    except (TypeError, ValueError):
        r = 0
    return r, _overs_to_balls(overs)


def build_standings_rows(series_data: dict) -> list[dict[str, Any]]:
    """
    Output rows: team, team_s_name, P, W, L, NR, NRR (str), Pts, nrr_sort (float).
    """
    entries = list(iter_series_match_entries(series_data))
    team_order: list[tuple[str, str]] = []
    seen: set[str] = set()

    for match in entries:
        mi = match.get("matchInfo") or {}
        if not isinstance(mi, dict):
            continue
        for key in ("team1", "team2"):
            tm = mi.get(key) or {}
            if not isinstance(tm, dict):
                continue
            nm = (tm.get("teamName") or "").strip()
            if not nm or nm in seen:
                continue
            seen.add(nm)
            sn = (tm.get("teamSName") or "").strip()
            team_order.append((nm, sn))

    stats: dict[str, dict[str, Any]] = {
        nm: {
            "sname": sn,
            "runs_for": 0,
            "balls_for": 0,
            "runs_against": 0,
            "balls_against": 0,
            "P": 0,
            "W": 0,
            "L": 0,
            "NR": 0,
            "Pts": 0,
        }
        for nm, sn in team_order
    }

    for match in entries:
        mi = match.get("matchInfo") or {}
        if not isinstance(mi, dict):
            continue
        state = (mi.get("state") or "").strip().lower()
        if state not in ("complete", "completed"):
            continue

        t1 = ((mi.get("team1") or {}).get("teamName") or "").strip()
        t2 = ((mi.get("team2") or {}).get("teamName") or "").strip()
        if not t1 or not t2 or t1 not in stats or t2 not in stats:
            continue

        status = mi.get("status") or ""
        kind, winner, loser = _classify_result(status, t1, t2)

        ms = match.get("matchScore") if isinstance(match.get("matchScore"), dict) else {}

        if kind == "nr":
            for t in (t1, t2):
                s = stats[t]
                s["P"] += 1
                s["NR"] += 1
                s["Pts"] += 1
            continue

        if kind == "tie":
            for t in (t1, t2):
                s = stats[t]
                s["P"] += 1
                s["NR"] += 1
                s["Pts"] += 1
            continue

        if kind == "win" and winner and loser:
            stats[winner]["P"] += 1
            stats[winner]["W"] += 1
            stats[winner]["Pts"] += 2
            stats[loser]["P"] += 1
            stats[loser]["L"] += 1

            r1, b1 = _ing_score(ms, "team1")
            r2, b2 = _ing_score(ms, "team2")
            if b1 > 0 and b2 > 0:
                stats[t1]["runs_for"] += r1
                stats[t1]["balls_for"] += b1
                stats[t1]["runs_against"] += r2
                stats[t1]["balls_against"] += b2
                stats[t2]["runs_for"] += r2
                stats[t2]["balls_for"] += b2
                stats[t2]["runs_against"] += r1
                stats[t2]["balls_against"] += b1
            continue

        # Unknown completed state — do not guess W/L
        continue

    rows: list[dict[str, Any]] = []
    for nm, _sn in team_order:
        st = stats[nm]
        bf = st["balls_for"] / 6.0
        ba = st["balls_against"] / 6.0
        rr_for = st["runs_for"] / bf if bf > 0 else 0.0
        rr_aga = st["runs_against"] / ba if ba > 0 else 0.0
        nrr_val = rr_for - rr_aga
        sign = "+" if nrr_val >= 0 else ""
        nrr_str = f"{sign}{nrr_val:.3f}"
        rows.append(
            {
                "team": nm,
                "team_s_name": st["sname"],
                "P": st["P"],
                "W": st["W"],
                "L": st["L"],
                "NR": st["NR"],
                "NRR": nrr_str,
                "Pts": st["Pts"],
                "nrr_sort": round(nrr_val, 6),
            }
        )

    rows.sort(key=lambda r: (-int(r["Pts"]), -float(r["nrr_sort"])))
    for r in rows:
        r.pop("nrr_sort", None)
    return rows
