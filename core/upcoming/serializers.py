from rest_framework import serializers
from .models import UpcomingMatch, TeamSquadCache
from django.utils import timezone
from datetime import datetime


class UpcomingMatchSerializer(serializers.ModelSerializer):
    date_ist = serializers.SerializerMethodField()
    time_ist = serializers.SerializerMethodField()

    class Meta:
        model = UpcomingMatch
        fields = [
            "external_id",
            "team_home",
            "team_away",
            "series_name",
            "venue",
            "status",
            "start_time_utc",
            "date_ist",
            "time_ist",
        ]

    def _to_ist(self, dt: datetime) -> datetime:
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.utc)
        # Asia/Kolkata is UTC+5:30 with no DST; offset 5.5 hours
        return (dt + timezone.timedelta(hours=5, minutes=30))

    def get_date_ist(self, obj: UpcomingMatch) -> str:
        dt_ist = self._to_ist(obj.start_time_utc)
        return dt_ist.strftime("%a, %d %b %Y")

    def get_time_ist(self, obj: UpcomingMatch) -> str:
        dt_ist = self._to_ist(obj.start_time_utc)
        return dt_ist.strftime("%I:%M %p")


class TeamSquadCacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamSquadCache
        fields = ["team_id", "fetched_at", "data"]

