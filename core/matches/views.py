import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Series, Match
from .serializers import SeriesSerializer
from .updater import update_cricket_data
from .scorecard_helpers import fetch_scorecard, apply_scorecard_to_match


class MatchScorecardAPI(APIView):
    """Serve scorecard from DB if cached, else fetch from CricAPI and cache."""

    def get(self, request, match_id):
        match = Match.objects.filter(external_id=match_id).first()
        if match and match.scorecard_data:
            return Response(match.scorecard_data)

        scorecard = fetch_scorecard(match_id)
        if scorecard is None:
            return Response(
                {"error": "Failed to fetch scorecard"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        if match:
            apply_scorecard_to_match(match, scorecard)
        return Response(scorecard)


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