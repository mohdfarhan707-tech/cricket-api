from rest_framework import serializers
from .models import Series, Match

class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = ['external_id', 'team_home', 'team_away', 'home_score', 'away_score', 'status']

class SeriesSerializer(serializers.ModelSerializer):
    matches = MatchSerializer(many=True, read_only=True)

    class Meta:
        model = Series
        fields = ['name', 'matches']