from rest_framework import serializers
from .models import Series, Match, TeamComparisonStat, TeamLastNStat, TeamHeadToHeadStat, TeamFormStat, SeriesStatsCache

class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = ['external_id', 'name', 'team_home', 'team_away', 'home_score', 'away_score', 'status', 'scorecard_data']

class SeriesSerializer(serializers.ModelSerializer):
    matches = MatchSerializer(many=True, read_only=True)

    class Meta:
        model = Series
        fields = ['name', 'external_id', 'matches']


class TeamComparisonStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamComparisonStat
        fields = [
            "team_a",
            "team_b",
            "scope",
            "last_n",
            "matches_played_a",
            "matches_played_b",
            "win_pct_a",
            "win_pct_b",
            "avg_score_a",
            "avg_score_b",
            "highest_score_a",
            "highest_score_b",
            "lowest_score_a",
            "lowest_score_b",
            "updated_at",
        ]


class TeamLastNStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamLastNStat
        fields = [
            "team",
            "scope",
            "last_n",
            "matches_played",
            "win_pct",
            "avg_score",
            "highest_score",
            "lowest_score",
            "updated_at",
        ]


class TeamHeadToHeadStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamHeadToHeadStat
        fields = [
            "team_a",
            "team_b",
            "scope",
            "played",
            "won_a",
            "won_b",
            "highest_total_a",
            "highest_total_b",
            "lowest_total_a",
            "lowest_total_b",
            "tosses_won_a",
            "tosses_won_b",
            "elected_to_bat_a",
            "elected_to_bat_b",
            "elected_to_field_a",
            "elected_to_field_b",
            "won_toss_and_match_a",
            "won_toss_and_match_b",
            "toss_won_bat_first_match_won_a",
            "toss_won_bat_first_match_won_b",
            "toss_won_bowl_first_match_won_a",
            "toss_won_bowl_first_match_won_b",
            "avg_runs_a",
            "avg_runs_b",
            "updated_at",
        ]


class TeamFormStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamFormStat
        fields = ["team", "last_n", "form", "updated_at"]


class SeriesStatsCacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeriesStatsCache
        fields = ["series_external_id", "series_name", "fetched_at", "data"]