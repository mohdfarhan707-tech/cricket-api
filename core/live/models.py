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
    uses_ipl_api = models.BooleanField(
        default=False,
        help_text="Scorecard/currentMatches for this match use the IPL CricAPI key.",
    )
    scorecard_data = models.JSONField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Live match"
        verbose_name_plural = "Live matches"
        ordering = ("-last_updated",)

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.name or self.external_id

