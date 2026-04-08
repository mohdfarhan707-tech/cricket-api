from django.conf import settings
from django.utils import timezone
import requests
import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Series, Match, TeamComparisonStat, TeamLastNStat, TeamHeadToHeadStat, TeamFormStat, SeriesStatsCache, MatchHighlightsCache
from .serializers import (
    SeriesSerializer,
    TeamComparisonStatSerializer,
    TeamLastNStatSerializer,
    TeamHeadToHeadStatSerializer,
    TeamFormStatSerializer,
    SeriesStatsCacheSerializer,
)
from .updater import update_cricket_data
from .scorecard_helpers import fetch_scorecard, apply_scorecard_to_match


def _is_bbl_series(series) -> bool:
    """True if this series is BBL (Big Bash League) from Cricbuzz."""
    if not series:
        return False
    name = (getattr(series, "name", "") or "").lower()
    ext_id = (getattr(series, "external_id", "") or "").lower()
    return "big bash" in name or ext_id.startswith("cricbuzz-")


def _is_icc_mens_t20_world_cup(series) -> bool:
    if not series:
        return False
    name = (getattr(series, "name", "") or "").lower()
    return "icc men" in name and "t20" in name and "world cup" in name


def _build_wc_highlights_query(match: Match) -> str:
    a = (match.team_home or "").strip()
    b = (match.team_away or "").strip()
    return f"{a} vs {b} T20 World Cup 2026 highlights".strip()


def _build_bbl_highlights_query(match: Match) -> str:
    a = (match.team_home or "").strip()
    b = (match.team_away or "").strip()
    name = (match.name or "").strip().lower()

    # Default stage for regular season games.
    stage = "League Stage"
    # Explicit stage names in match title win first.
    if "qualifier" in name:
        stage = "Qualifier"
    elif "challenger" in name:
        stage = "Challenger"
    elif "knockout" in name:
        stage = "Knockout"
    elif "final" in name:
        stage = "Final"
    else:
        # Last 4 matches should use: Qualifier, Challenger, Knockout, Final.
        m = re.search(r"(\d+)\s*(st|nd|rd|th)?\s*match\b", name)
        n = int(m.group(1)) if m else None
        if n is not None:
            if n == 41:
                stage = "The Qualifier"
            elif n == 42:
                stage = "Knockout"
            elif n == 43:
                stage = "Challenger"
            elif n == 44:
                stage = "Final"

    return f"{a} vs {b} {stage} BBL 2025-26 highlights".strip()


def _stage_rank(text: str) -> int:
    t = (text or "").lower()
    if "qualifier" in t:
        return 0
    if "challenger" in t:
        return 1
    if "knockout" in t:
        return 2
    if "final" in t:
        return 3
    if "league stage" in t:
        return 4
    if "group stage" in t or "group" in t:
        return 5
    return 6


def _sort_highlights_items(items: list[dict], match: Match) -> list[dict]:
    match_name = (match.name or "").lower()
    target_rank = _stage_rank(match_name)
    out = list(items or [])
    # Prefer exact stage match first.
    out.sort(
        key=lambda x: (
            0 if _stage_rank(str(x.get("title") or "")) == target_rank else 1,
            _stage_rank(str(x.get("title") or "")),
            str(x.get("title") or "").lower(),
        )
    )
    # For similarly ranked entries, prefer latest publish time.
    out.sort(key=lambda x: str(x.get("publishedAt") or ""), reverse=True)
    return out


def _normalize_youtube_items(payload: dict) -> list[dict]:
    out: list[dict] = []
    items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        return out

    for it in items:
        if not isinstance(it, dict):
            continue
        ident = it.get("id") or {}
        if not isinstance(ident, dict):
            continue
        video_id = str(ident.get("videoId") or "").strip()
        if not video_id:
            continue
        sn = it.get("snippet") or {}
        if not isinstance(sn, dict):
            sn = {}
        thumbs = sn.get("thumbnails") or {}
        if not isinstance(thumbs, dict):
            thumbs = {}
        thumb = (
            (thumbs.get("high") or {}).get("url")
            or (thumbs.get("medium") or {}).get("url")
            or (thumbs.get("default") or {}).get("url")
            or ""
        )
        out.append(
            {
                "videoId": video_id,
                "title": sn.get("title") or "",
                "description": sn.get("description") or "",
                "channelTitle": sn.get("channelTitle") or "",
                "publishedAt": sn.get("publishedAt") or "",
                "thumbnail": thumb,
                "url": f"https://www.youtube.com/watch?v={video_id}",
            }
        )
    return out


class MatchScorecardAPI(APIView):
    """Serve scorecard from DB if cached, else fetch from CricAPI or Cricbuzz (for BBL) and cache."""

    def get(self, request, match_id):
        match = Match.objects.select_related("series").filter(external_id=match_id).first()
        scorecard = None
        # Use cache only if it has actual score/scorecard content (not empty)
        if match and match.scorecard_data:
            sc = match.scorecard_data
            if isinstance(sc, dict) and (sc.get("score") or sc.get("scorecard")):
                scorecard = dict(sc)

        if scorecard is None:
            # IPL/PSL (and other feed-only rows) may exist as live.LiveMatch with a cached scorecard
            # but not as matches.Match — reuse that JSON so clients using /matches/... still work.
            try:
                from live.models import LiveMatch as _LiveMatchRow
            except ImportError:
                _LiveMatchRow = None
            if _LiveMatchRow is not None:
                live_row = _LiveMatchRow.objects.filter(external_id=str(match_id)).first()
                if live_row and live_row.scorecard_data:
                    sc = live_row.scorecard_data
                    if isinstance(sc, dict) and (sc.get("score") or sc.get("scorecard")):
                        scorecard = dict(sc)

        if scorecard is None:
            # BBL (and other Cricbuzz-sourced series) use Cricbuzz match IDs – fetch from Cricbuzz mcenter.
            if match and _is_bbl_series(match.series):
                try:
                    from upcoming.rapidapi_client import fetch_mcenter_raw
                    from upcoming.cricbuzz_scorecard import transform_cricbuzz_to_scorecard
                except ImportError:
                    pass
                else:
                    raw = fetch_mcenter_raw(match_id)
                    if raw:
                        scorecard = transform_cricbuzz_to_scorecard(raw, match_id)

            # Fallback: CricAPI (for ICC T20 World Cup, etc.).
            if scorecard is None:
                scorecard = fetch_scorecard(match_id)

            if scorecard is None:
                return Response(
                    {"error": "Failed to fetch scorecard"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )
            if match:
                apply_scorecard_to_match(match, scorecard)

        # Enrich with match info when name/venue/date are empty (e.g. BBL hscard)
        if match and scorecard and not (scorecard.get("name") or "").strip():
            scorecard = dict(scorecard)
            parts = [match.team_home or "", match.team_away or ""]
            scorecard["name"] = " vs ".join(p for p in parts if p).strip() or (match.name or "")
        return Response(scorecard)


class MatchHighlightsAPI(APIView):
    """
    YouTube highlights for ICC Men's T20 World Cup and BBL matches.
    Caches by match in DB to reduce API usage.
    """

    def get(self, request, match_id):
        match = Match.objects.select_related("series").filter(external_id=match_id).first()
        if not match:
            return Response({"error": "Match not found"}, status=status.HTTP_404_NOT_FOUND)
        is_wc = _is_icc_mens_t20_world_cup(match.series)
        is_bbl = _is_bbl_series(match.series)
        if not (is_wc or is_bbl):
            return Response({"error": "Highlights available for ICC Men's T20 World Cup and BBL matches only"}, status=status.HTTP_400_BAD_REQUEST)

        refresh = request.query_params.get("refresh") == "1"
        cache = MatchHighlightsCache.objects.filter(match=match).first()
        ttl = timezone.timedelta(days=30)
        now = timezone.now()

        item_limit = 5 if is_bbl else 3

        if cache and cache.data and not refresh and (now - cache.fetched_at) < ttl:
            return Response(
                {
                    "match_id": match.external_id,
                    "query": cache.query,
                    "items": (cache.data.get("items", []) if isinstance(cache.data, dict) else [])[:item_limit],
                    "cached": True,
                }
            )

        api_key = getattr(settings, "YOUTUBE_API_KEY", "") or ""
        if not api_key:
            if cache and cache.data:
                return Response(
                    {
                        "match_id": match.external_id,
                        "query": cache.query,
                        "items": (cache.data.get("items", []) if isinstance(cache.data, dict) else [])[:item_limit],
                        "cached": True,
                    }
                )
            return Response({"error": "YOUTUBE_API_KEY not configured"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        query = _build_wc_highlights_query(match) if is_wc else _build_bbl_highlights_query(match)
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": item_limit,
            "key": api_key,
        }
        try:
            resp = requests.get("https://www.googleapis.com/youtube/v3/search", params=params, timeout=12)
            payload = resp.json() if resp.content else {}
        except Exception:
            if cache and cache.data:
                return Response(
                    {
                        "match_id": match.external_id,
                        "query": cache.query,
                        "items": (cache.data.get("items", []) if isinstance(cache.data, dict) else [])[:item_limit],
                        "cached": True,
                    }
                )
            return Response({"error": "Failed to fetch highlights"}, status=status.HTTP_502_BAD_GATEWAY)

        if resp.status_code >= 400:
            if cache and cache.data:
                return Response(
                    {
                        "match_id": match.external_id,
                        "query": cache.query,
                        "items": (cache.data.get("items", []) if isinstance(cache.data, dict) else [])[:item_limit],
                        "cached": True,
                    }
                )
            return Response(
                {
                    "error": "Failed to fetch highlights",
                    "details": payload.get("error", {}).get("message", "") if isinstance(payload, dict) else "",
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        items = _normalize_youtube_items(payload if isinstance(payload, dict) else {})
        items = _sort_highlights_items(items, match)[:item_limit]
        cache_data = {"items": items, "raw_page_info": (payload.get("pageInfo") if isinstance(payload, dict) else None)}
        if cache:
            cache.query = query
            cache.data = cache_data
            cache.save(update_fields=["query", "data", "fetched_at"])
        else:
            MatchHighlightsCache.objects.create(match=match, query=query, data=cache_data)

        return Response({"match_id": match.external_id, "query": query, "items": items, "cached": False})


class MatchDashboardAPI(APIView):
    def get(self, request):
        # Prevent burning API limits on every page refresh.
        # Call `/api/matches/?refresh=1` when you explicitly want to sync from CricAPI.
        if request.query_params.get("refresh") == "1":
            try:
                update_cricket_data()
            except Exception as e:
                print(f"Update failed: {e}")

        series = Series.objects.all().prefetch_related('matches')
        serializer = SeriesSerializer(series, many=True)
        return Response(serializer.data)

class TeamComparisonAPI(APIView):
    """
    Return manually curated team comparison stats (e.g. IPL last 10 matches).
    Query params:
      - a: team code/name (e.g. RCB)
      - b: team code/name (e.g. SRH)
      - scope: overall|on_venue (default overall)
    """

    def get(self, request):
        a = (request.query_params.get("a") or "").strip().upper()
        b = (request.query_params.get("b") or "").strip().upper()
        scope = (request.query_params.get("scope") or "overall").strip().lower()

        if not a or not b:
            return Response({"error": "Missing query params: a, b"}, status=status.HTTP_400_BAD_REQUEST)

        row = TeamComparisonStat.objects.filter(team_a=a, team_b=b, scope=scope).first()
        swapped = False
        if row is None:
            row = TeamComparisonStat.objects.filter(team_a=b, team_b=a, scope=scope).first()
            swapped = row is not None

        if row is None:
            return Response({"error": "No team comparison found"}, status=status.HTTP_404_NOT_FOUND)

        data = TeamComparisonStatSerializer(row).data
        if swapped:
            # Swap sides so response always matches requested a/b ordering.
            data = {
                **data,
                "team_a": a,
                "team_b": b,
                "matches_played_a": data["matches_played_b"],
                "matches_played_b": data["matches_played_a"],
                "win_pct_a": data["win_pct_b"],
                "win_pct_b": data["win_pct_a"],
                "avg_score_a": data["avg_score_b"],
                "avg_score_b": data["avg_score_a"],
                "highest_score_a": data["highest_score_b"],
                "highest_score_b": data["highest_score_a"],
                "lowest_score_a": data["lowest_score_b"],
                "lowest_score_b": data["lowest_score_a"],
            }

        return Response(data)


class TeamLastNAPI(APIView):
    """
    Return manually curated last-N stats for a single team (vs all teams).
    Query params:
      - team: team code (e.g. RCB)
      - scope: overall|on_venue (default overall)
    """

    def get(self, request):
        team = (request.query_params.get("team") or "").strip().upper()
        scope = (request.query_params.get("scope") or "overall").strip().lower()
        if not team:
            return Response({"error": "Missing query param: team"}, status=status.HTTP_400_BAD_REQUEST)
        row = TeamLastNStat.objects.filter(team=team, scope=scope).first()
        if row is None:
            return Response({"error": "No team stats found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(TeamLastNStatSerializer(row).data)


class TeamHeadToHeadAPI(APIView):
    """
    Return manually curated head-to-head stats for two teams.
    Query params:
      - a: team code (e.g. RCB)
      - b: team code (e.g. SRH)
    """

    def get(self, request):
        a = (request.query_params.get("a") or "").strip().upper()
        b = (request.query_params.get("b") or "").strip().upper()
        scope = (request.query_params.get("scope") or "overall").strip().lower()
        if not a or not b:
            return Response({"error": "Missing query params: a, b"}, status=status.HTTP_400_BAD_REQUEST)

        row = TeamHeadToHeadStat.objects.filter(team_a=a, team_b=b, scope=scope).first()
        swapped = False
        if row is None:
            row = TeamHeadToHeadStat.objects.filter(team_a=b, team_b=a, scope=scope).first()
            swapped = row is not None
        if row is None:
            return Response({"error": "No head-to-head data yet"}, status=status.HTTP_404_NOT_FOUND)

        data = TeamHeadToHeadStatSerializer(row).data
        if swapped:
            data = {
                **data,
                "team_a": a,
                "team_b": b,
                "won_a": data["won_b"],
                "won_b": data["won_a"],
                "highest_total_a": data["highest_total_b"],
                "highest_total_b": data["highest_total_a"],
                "lowest_total_a": data["lowest_total_b"],
                "lowest_total_b": data["lowest_total_a"],
                "tosses_won_a": data["tosses_won_b"],
                "tosses_won_b": data["tosses_won_a"],
                "elected_to_bat_a": data["elected_to_bat_b"],
                "elected_to_bat_b": data["elected_to_bat_a"],
                "elected_to_field_a": data["elected_to_field_b"],
                "elected_to_field_b": data["elected_to_field_a"],
                "won_toss_and_match_a": data["won_toss_and_match_b"],
                "won_toss_and_match_b": data["won_toss_and_match_a"],
                "toss_won_bat_first_match_won_a": data["toss_won_bat_first_match_won_b"],
                "toss_won_bat_first_match_won_b": data["toss_won_bat_first_match_won_a"],
                "toss_won_bowl_first_match_won_a": data["toss_won_bowl_first_match_won_b"],
                "toss_won_bowl_first_match_won_b": data["toss_won_bowl_first_match_won_a"],
                "avg_runs_a": data["avg_runs_b"],
                "avg_runs_b": data["avg_runs_a"],
            }

        return Response(data)


class TeamFormAPI(APIView):
    """
    Return manually curated team form string for last N matches.
    Query params:
      - team: team code (e.g. RCB)
      - n: number of matches (default 5)
    """

    def get(self, request):
        team = (request.query_params.get("team") or "").strip().upper()
        n = request.query_params.get("n") or "5"
        try:
            n_int = int(n)
        except Exception:
            n_int = 5
        if not team:
            return Response({"error": "Missing query param: team"}, status=status.HTTP_400_BAD_REQUEST)
        row = TeamFormStat.objects.filter(team=team, last_n=n_int).first()
        if row is None:
            return Response({"error": "No team form data yet"}, status=status.HTTP_404_NOT_FOUND)
        return Response(TeamFormStatSerializer(row).data)


class BblSeriesStatsAPI(APIView):
    """
    Return cached BBL 2025/26 stats (seeded via management command).

    Query params:
      - refresh=1 (optional): if present and we have data, still returns cached data
        (scraping is intentionally not done at request-time).
    """

    # ESPN series external id for Big Bash League 2025/26
    SERIES_EXTERNAL_ID = "1490534"

    def get(self, request):
        refresh = request.query_params.get("refresh") == "1"
        _ = refresh  # kept for API compatibility; no runtime scrape

        row = SeriesStatsCache.objects.filter(series_external_id=self.SERIES_EXTERNAL_ID).first()
        if not row or not row.data:
            return Response({"error": "BBL stats not seeded yet"}, status=status.HTTP_404_NOT_FOUND)

        return Response(SeriesStatsCacheSerializer(row).data)