from rest_framework import serializers
from .models import LiveMatch


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
        ]

