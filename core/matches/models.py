from django.db import models

class Series(models.Model):
    name = models.CharField(max_length=255)
    external_id = models.CharField(max_length=100, unique=True) # CricAPI Series ID

    def __str__(self):
        return self.name

class Match(models.Model):
    series = models.ForeignKey(Series, related_name='matches', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    team_home = models.CharField(max_length=100)
    team_away = models.CharField(max_length=100)
    home_score = models.CharField(max_length=50, blank=True, null=True)
    away_score = models.CharField(max_length=50, blank=True, null=True)
    external_id = models.CharField(max_length=100, unique=True)
    scorecard_data = models.JSONField(null=True, blank=True)  # Cached CricAPI scorecard

    def __str__(self):
        return self.name