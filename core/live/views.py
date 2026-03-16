import time
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import LiveMatch
from .serializers import LiveMatchSerializer
from .scorecard_helpers import fetch_live_scorecard, apply_scorecard_to_live_match, LIVE_CRICAPI_KEY


_LAST_LIVE_SYNC_AT = 0.0


def _split_teams_from_name(name: str) -> tuple[str, str]:
    n = (name or "").strip()
    if " vs " in n:
        left = n.split(" vs ", 1)[0].strip()
        right = n.split(" vs ", 1)[1].split(",", 1)[0].strip()
        return left, right
    if " v " in n:
        left = n.split(" v ", 1)[0].strip()
        right = n.split(" v ", 1)[1].split(",", 1)[0].strip()
        return left, right
    return "", ""


def _sync_live_matches() -> None:
    """Fetch live matches using separate API key and cache in DB."""
    global _LAST_LIVE_SYNC_AT
    now = time.time()
    if now - _LAST_LIVE_SYNC_AT < 30:
        return

    # Use currentMatches for two windows: offset=0 and offset=25
    all_items = []
    for offset in (0, 25):
        url = f"https://api.cricapi.com/v1/currentMatches?apikey={LIVE_CRICAPI_KEY}&offset={offset}"
        try:
            resp = requests.get(url, timeout=8)
            root = resp.json() or {}
            batch = root.get("data") or root.get("matches") or []
            if isinstance(batch, list):
                all_items.extend(batch)
        except Exception:
            continue

    live_ids = []

    for item in all_items:
        # Prefer explicit matchStarted/matchEnded flags instead of fragile status text.
        started = item.get("matchStarted")
        ended = item.get("matchEnded")
        # Handle both boolean and string forms like "true"/"false"
        started_bool = str(started).lower() == "true" if not isinstance(started, bool) else started
        ended_bool = str(ended).lower() == "true" if not isinstance(ended, bool) else ended

        match_id = item.get("id") or item.get("unique_id")
        if not match_id:
            continue
        if started_bool and not ended_bool:
            live_ids.append(match_id)

        team_home = item.get("t1") or ""
        team_away = item.get("t2") or ""
        # currentMatches often provides a `teams` list; use it if t1/t2 are missing
        if (not team_home or not team_away) and isinstance(item.get("teams"), list):
            teams = [t for t in item.get("teams") if isinstance(t, str)]
            if len(teams) >= 2:
                team_home = team_home or teams[0]
                team_away = team_away or teams[1]
        # last resort: parse from "A vs B, ..." in the match name
        if not team_home or not team_away:
            left, right = _split_teams_from_name(item.get("name") or "")
            team_home = team_home or left
            team_away = team_away or right

        # Try to get quick scoreboard strings
        home_score = item.get("t1s") or ""
        away_score = item.get("t2s") or ""

        # Fallback: build from score array if t1s/t2s are missing
        if (not home_score or not away_score) and isinstance(item.get("score"), list):
            score_list = item["score"]
            if len(score_list) >= 1:
                s0 = score_list[0]
                r0 = s0.get("r")
                w0 = s0.get("w")
                o0 = s0.get("o")
                if r0 is not None:
                    home_score = f"{r0}/{w0 if w0 is not None else 0}"
                    if o0 is not None:
                        home_score += f" ({o0} ov)"
            if len(score_list) >= 2:
                s1 = score_list[1]
                r1 = s1.get("r")
                w1 = s1.get("w")
                o1 = s1.get("o")
                if r1 is not None:
                    away_score = f"{r1}/{w1 if w1 is not None else 0}"
                    if o1 is not None:
                        away_score += f" ({o1} ov)"

        LiveMatch.objects.update_or_create(
            external_id=match_id,
            defaults={
                "name": item.get("name") or "",
                "status": item.get("status") or "",
                "team_home": team_home,
                "team_away": team_away,
                "home_score": home_score,
                "away_score": away_score,
                "is_live": started_bool and not ended_bool,
                "is_finished": ended_bool,
            },
        )

    # Mark old ones as not live anymore (but keep them as finished if they were)
    if live_ids:
        LiveMatch.objects.exclude(external_id__in=live_ids).update(is_live=False)

    _LAST_LIVE_SYNC_AT = now


class LiveMatchesAPI(APIView):
    """Return all currently known live matches from DB (syncing from CricAPI)."""

    def get(self, request):
        _sync_live_matches()
        qs = LiveMatch.objects.filter(is_live=True).order_by("-last_updated")
        serializer = LiveMatchSerializer(qs, many=True)
        return Response(serializer.data)


class LiveResultsAPI(APIView):
    """Return finished matches that came from the live feed (results)."""

    def get(self, request):
        _sync_live_matches()
        qs = LiveMatch.objects.filter(is_finished=True).order_by("-last_updated")
        serializer = LiveMatchSerializer(qs, many=True)
        return Response(serializer.data)


class LiveMatchScorecardAPI(APIView):
    """Serve live scorecard; cache into DB on first fetch."""

    def get(self, request, match_id: str):
        match = LiveMatch.objects.filter(external_id=match_id).first()
        if match and match.scorecard_data:
            return Response(match.scorecard_data)

        scorecard = fetch_live_scorecard(match_id)
        if scorecard is None:
            return Response(
                {"error": "Failed to fetch live scorecard"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if match:
            apply_scorecard_to_live_match(match, scorecard)
        else:
            # Create placeholder so next time we can reuse cached data
            match = LiveMatch.objects.create(
                external_id=match_id,
                name=scorecard.get("name", ""),
                status=scorecard.get("status", ""),
                team_home="",
                team_away="",
                home_score="",
                away_score="",
                is_live=True,
                scorecard_data=scorecard,
            )
            apply_scorecard_to_live_match(match, scorecard)

        return Response(scorecard)

