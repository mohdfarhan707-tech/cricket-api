from datetime import timedelta

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import UpcomingMatch, TeamSquadCache, LeagueStandingsCache
from .serializers import UpcomingMatchSerializer
from .rapidapi_client import fetch_team_players_raw, fetch_series_raw
from .points_table_builder import (
    SERIES_ID_IPL,
    SERIES_ID_PSL,
    build_standings_rows,
    series_name_from_payload,
)


class UpcomingMatchesAPI(APIView):
    def get(self, request):
        now = timezone.now()
        qs = UpcomingMatch.objects.filter(start_time_utc__gt=now).order_by("start_time_utc")
        serializer = UpcomingMatchSerializer(qs, many=True)
        return Response(serializer.data)


class TeamSquadAPI(APIView):
    """
    Cached team squad endpoint.
    Query params:
      - team_id: Cricbuzz team id
      - refresh: 1 to force refresh
    """

    def get(self, request):
        team_id = (request.query_params.get("team_id") or "").strip()
        if not team_id:
            return Response({"error": "Missing query param: team_id"}, status=status.HTTP_400_BAD_REQUEST)

        refresh = request.query_params.get("refresh") == "1"
        cache = TeamSquadCache.objects.filter(team_id=team_id).first()

        # cache TTL: 24h
        ttl = timezone.timedelta(hours=24)
        now = timezone.now()
        if cache and cache.data and not refresh and (now - cache.fetched_at) < ttl:
            return Response(cache.data)

        data = fetch_team_players_raw(team_id)
        if data is None:
            if cache and cache.data:
                return Response(cache.data)
            return Response({"error": "Failed to fetch team squad"}, status=status.HTTP_502_BAD_GATEWAY)

        if cache:
            cache.data = data
            cache.save(update_fields=["data", "fetched_at"])
        else:
            TeamSquadCache.objects.create(team_id=team_id, data=data)

        return Response(data)


class LeagueStandingsAPI(APIView):
    """
    GET ?league=ipl|psl
    Points table from Cricbuzz series schedule + results (cached ~10 minutes).
    """

    def get(self, request):
        league = (request.query_params.get("league") or "").strip().lower()
        if league not in ("ipl", "psl"):
            return Response({"error": "Query param league must be ipl or psl"}, status=status.HTTP_400_BAD_REQUEST)

        series_id = SERIES_ID_IPL if league == "ipl" else SERIES_ID_PSL
        refresh = request.query_params.get("refresh") == "1"
        ttl = timedelta(minutes=10)
        now = timezone.now()

        row = LeagueStandingsCache.objects.filter(league=league).first()
        if row and row.data and not refresh and (now - row.fetched_at) < ttl:
            return Response(row.data)

        raw = fetch_series_raw(series_id)
        if raw is None:
            if row and row.data:
                return Response(row.data)
            return Response({"error": "Failed to fetch series from Cricbuzz"}, status=status.HTTP_502_BAD_GATEWAY)

        rows = build_standings_rows(raw)
        label = series_name_from_payload(raw)
        payload = {
            "league": league,
            "series_id": series_id,
            "series_name": label,
            "rows": rows,
            "fetched_at": now.isoformat(),
        }
        LeagueStandingsCache.objects.update_or_create(
            league=league,
            defaults={"series_id": series_id, "data": payload},
        )
        return Response(payload)

