from django.db import models


class LiveMatch(models.Model):
    """Flat model to store live match snapshots + cached scorecards."""

    external_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=100, blank=True, default="")
    team_home = models.CharField(max_length=100, blank=True, default="")
    team_away = models.CharField(max_length=100, blank=True, default="")
    home_score = models.CharField(max_length=50, blank=True, default="")
    away_score = models.CharField(max_length=50, blank=True, default="")
    is_live = models.BooleanField(default=True)
    is_finished = models.BooleanField(default=False)
    scorecard_data = models.JSONField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.name or self.external_id

