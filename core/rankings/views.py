from django.db.models import Max
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import TeamRanking, BatterRanking, BowlerRanking, AllRounderRanking
from .serializers import (
    TeamRankingSerializer,
    BatterRankingSerializer,
    BowlerRankingSerializer,
    AllRounderRankingSerializer,
)


def _group_by_format(rows):
    grouped = {"odi": [], "t20": [], "test": []}
    for r in rows:
        fmt = r.get("format_type")
        if fmt in grouped:
            grouped[fmt].append(r)
    return grouped


class RankingsAPI(APIView):
    """
    Read cached rankings from DB.

    /api/rankings/<kind>/ where kind is teams|batsmen|bowlers|allrounders

    Response shape: { "odi": [...], "t20": [...], "test": [...], "fetched_at": "<iso8601>|null" }
    """

    def get(self, request, kind: str):
        kind = (kind or "").strip().lower()

        def build_response(model, serializer_cls):
            data = serializer_cls(model.objects.all(), many=True).data
            grouped = _group_by_format(data)
            latest = model.objects.aggregate(m=Max("last_updated"))["m"]
            grouped["fetched_at"] = latest.isoformat() if latest else None
            return Response(grouped)

        if kind == "teams":
            return build_response(TeamRanking, TeamRankingSerializer)
        if kind == "batsmen":
            return build_response(BatterRanking, BatterRankingSerializer)
        if kind == "bowlers":
            return build_response(BowlerRanking, BowlerRankingSerializer)
        if kind == "allrounders":
            return build_response(AllRounderRanking, AllRounderRankingSerializer)

        return Response({"error": "Unknown kind"}, status=400)
