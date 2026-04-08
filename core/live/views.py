import threading
import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import LiveMatch
from .serializers import LiveMatchListSerializer, LiveMatchSerializer
from .scorecard_helpers import (
    apply_scorecard_to_live_match,
    fetch_current_matches_batches,
    fetch_live_scorecard,
    is_ipl_current_match_item,
    LIVE_CRICAPI_KEY,
    LIVE_CRICAPI_KEY_IPL,
)


_LAST_LIVE_SYNC_AT = 0.0
_LIVE_SYNC_LOCK = threading.Lock()


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


def _upsert_from_current_match_item(item: dict, uses_ipl_api: bool, live_ids: list) -> None:
    # Prefer explicit matchStarted/matchEnded flags instead of fragile status text.
    started = item.get("matchStarted")
    ended = item.get("matchEnded")
    # Handle both boolean and string forms like "true"/"false"
    started_bool = str(started).lower() == "true" if not isinstance(started, bool) else started
    ended_bool = str(ended).lower() == "true" if not isinstance(ended, bool) else ended

    raw_id = item.get("id") or item.get("unique_id")
    if not raw_id:
        return
    match_id = str(raw_id)
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

    existing = LiveMatch.objects.filter(external_id=match_id).first()
    was_finished_before = bool(existing and existing.is_finished)

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
            "uses_ipl_api": uses_ipl_api,
        },
    )

    # When a fixture first becomes finished, persist the full scorecard once (DB cache).
    if ended_bool and not was_finished_before:
        row = LiveMatch.objects.filter(external_id=match_id).first()
        if row and not row.scorecard_data:
            sc, used_ipl = fetch_live_scorecard(match_id)
            if sc:
                if row.uses_ipl_api != used_ipl:
                    row.uses_ipl_api = used_ipl
                    row.save(update_fields=["uses_ipl_api"])
                apply_scorecard_to_live_match(row, sc, persist_full_scorecard=True)


def _sync_live_matches() -> None:
    """Fetch live matches: default key for non-IPL, IPL key for IPL only; cache in DB."""
    global _LAST_LIVE_SYNC_AT
    now = time.time()
    if now - _LAST_LIVE_SYNC_AT < 30:
        return

    with _LIVE_SYNC_LOCK:
        now = time.time()
        if now - _LAST_LIVE_SYNC_AT < 30:
            return

        live_ids: list = []

        for item in fetch_current_matches_batches(LIVE_CRICAPI_KEY):
            if is_ipl_current_match_item(item):
                continue
            _upsert_from_current_match_item(item, uses_ipl_api=False, live_ids=live_ids)

        for item in fetch_current_matches_batches(LIVE_CRICAPI_KEY_IPL):
            if not is_ipl_current_match_item(item):
                continue
            _upsert_from_current_match_item(item, uses_ipl_api=True, live_ids=live_ids)

        if live_ids:
            LiveMatch.objects.exclude(external_id__in=live_ids).update(is_live=False)

        _LAST_LIVE_SYNC_AT = time.time()


class LiveMatchesAPI(APIView):
    """Return all currently known live matches from DB (syncing from CricAPI)."""

    def get(self, request):
        _sync_live_matches()
        qs = LiveMatch.objects.filter(is_live=True).order_by("-last_updated")
        serializer = LiveMatchListSerializer(qs, many=True)
        return Response(serializer.data)


class LiveResultsAPI(APIView):
    """Return finished matches that came from the live feed (results)."""

    def get(self, request):
        _sync_live_matches()
        qs = LiveMatch.objects.filter(is_finished=True).order_by("-last_updated")
        serializer = LiveMatchListSerializer(qs, many=True)
        return Response(serializer.data)


class LiveMatchScorecardAPI(APIView):
    """
    Live scorecard: always fetch fresh from CricAPI while the match is in progress.
    Full JSON is stored in DB only after the match is marked finished (sync from
    currentMatches). Finished matches are served from DB when present.
    """

    def get(self, request, match_id: str):
        _sync_live_matches()
        match = LiveMatch.objects.filter(external_id=match_id).first()

        if match and match.is_finished and match.scorecard_data:
            return Response(match.scorecard_data)

        scorecard, used_ipl_key = fetch_live_scorecard(match_id)
        if scorecard is None:
            return Response(
                {"error": "Failed to fetch live scorecard"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        match = LiveMatch.objects.filter(external_id=match_id).first()
        persist_full = bool(match and match.is_finished)

        if match:
            apply_scorecard_to_live_match(
                match, scorecard, persist_full_scorecard=persist_full
            )
        else:
            match = LiveMatch.objects.create(
                external_id=match_id,
                name=scorecard.get("name", ""),
                status=scorecard.get("status", ""),
                team_home="",
                team_away="",
                home_score="",
                away_score="",
                is_live=True,
                is_finished=False,
                uses_ipl_api=used_ipl_key,
                scorecard_data=None,
            )
            apply_scorecard_to_live_match(
                match, scorecard, persist_full_scorecard=False
            )

        return Response(scorecard)

