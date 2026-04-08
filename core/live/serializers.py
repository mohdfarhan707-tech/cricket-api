from rest_framework import serializers
from .models import LiveMatch


class LiveMatchListSerializer(serializers.ModelSerializer):
    """
    List payload for home dashboard (live + results). Omits scorecard_data — that JSON
    can be huge per finished IPL/PSL match and was slowing every page load.
    Full scorecard: GET /api/live-matches/<id>/scorecard/ or matches scorecard API.
    """

    class Meta:
        model = LiveMatch
        fields = [
            "external_id",
            "name",
            "status",
            "team_home",
            "team_away",
            "home_score",
            "away_score",
            "is_live",
            "is_finished",
        ]


class LiveMatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveMatch
        fields = [
            "external_id",
            "name",
            "status",
            "team_home",
            "team_away",
            "home_score",
            "away_score",
            "is_live",
            "is_finished",
            "scorecard_data",
        ]

