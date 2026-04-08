from django.db import models


FORMAT_CHOICES = [
    ("odi", "ODI"),
    ("t20", "T20"),
    ("test", "Test"),
]


class TeamRanking(models.Model):
    team_name = models.CharField(max_length=100)
    team_code = models.CharField(max_length=10, blank=True, default="")
    format_type = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    rank = models.PositiveIntegerField()
    rating = models.PositiveIntegerField()
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Team ranking"
        verbose_name_plural = "Team rankings"
        ordering = ["format_type", "rank"]
        unique_together = ("team_name", "format_type")


class BatterRanking(models.Model):
    player_name = models.CharField(max_length=100)
    country = models.CharField(max_length=100, blank=True, default="")
    format_type = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    rank = models.PositiveIntegerField()
    rating = models.PositiveIntegerField()
    career_best_rating = models.PositiveIntegerField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Batter ranking"
        verbose_name_plural = "Batter rankings"
        ordering = ["format_type", "rank"]
        unique_together = ("player_name", "format_type")


class BowlerRanking(models.Model):
    player_name = models.CharField(max_length=100)
    country = models.CharField(max_length=100, blank=True, default="")
    format_type = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    rank = models.PositiveIntegerField()
    rating = models.PositiveIntegerField()
    career_best_rating = models.PositiveIntegerField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bowler ranking"
        verbose_name_plural = "Bowler rankings"
        ordering = ["format_type", "rank"]
        unique_together = ("player_name", "format_type")


class AllRounderRanking(models.Model):
    player_name = models.CharField(max_length=100)
    country = models.CharField(max_length=100, blank=True, default="")
    format_type = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    rank = models.PositiveIntegerField()
    rating = models.PositiveIntegerField()
    career_best_rating = models.PositiveIntegerField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "All-rounder ranking"
        verbose_name_plural = "All-rounder rankings"
        ordering = ["format_type", "rank"]
        unique_together = ("player_name", "format_type")

