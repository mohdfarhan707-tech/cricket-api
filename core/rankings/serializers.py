from rest_framework import serializers
from .models import TeamRanking, BatterRanking, BowlerRanking, AllRounderRanking


class TeamRankingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamRanking
        fields = ["team_name", "team_code", "format_type", "rank", "rating", "last_updated"]


class BatterRankingSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatterRanking
        fields = ["player_name", "country", "format_type", "rank", "rating", "career_best_rating", "last_updated"]


class BowlerRankingSerializer(serializers.ModelSerializer):
    class Meta:
        model = BowlerRanking
        fields = ["player_name", "country", "format_type", "rank", "rating", "career_best_rating", "last_updated"]


class AllRounderRankingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllRounderRanking
        fields = ["player_name", "country", "format_type", "rank", "rating", "career_best_rating", "last_updated"]

