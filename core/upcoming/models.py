from django.db import models


class UpcomingMatch(models.Model):
  external_id = models.CharField(max_length=100, unique=True)
  team_home = models.CharField(max_length=100)
  team_away = models.CharField(max_length=100)
  series_name = models.CharField(max_length=200, blank=True, default="")
  venue = models.CharField(max_length=200, blank=True, default="")
  start_time_utc = models.DateTimeField()
  status = models.CharField(max_length=200, blank=True, default="")

  class Meta:
    ordering = ["start_time_utc"]


class TeamSquadCache(models.Model):
  team_id = models.CharField(max_length=32, unique=True)
  fetched_at = models.DateTimeField(auto_now=True)
  data = models.JSONField(null=True, blank=True)

  def __str__(self):
    return f"TeamSquadCache(team_id={self.team_id})"


class LeagueStandingsCache(models.Model):
  """Cached IPL/PSL points tables derived from Cricbuzz series payloads."""

  league = models.CharField(max_length=16, unique=True)
  series_id = models.CharField(max_length=32, blank=True, default="")
  data = models.JSONField(default=dict)

  fetched_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return f"LeagueStandingsCache(league={self.league})"

