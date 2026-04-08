from django.db import models

class Series(models.Model):
    name = models.CharField(max_length=255)
    external_id = models.CharField(max_length=100, unique=True) # CricAPI Series ID

    class Meta:
        verbose_name = "Series"
        verbose_name_plural = "Series"

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

    class Meta:
        verbose_name = "Match"
        verbose_name_plural = "Matches"

    def __str__(self):
        return self.name


class TeamComparisonStat(models.Model):
    """
    Manually curated "Last N matches" team comparison stats (e.g. IPL Last 10).
    Stored per (team_a, team_b, scope).
    """

    SCOPE_OVERALL = "overall"
    SCOPE_ON_VENUE = "on_venue"
    SCOPE_CHOICES = [
        (SCOPE_OVERALL, "Overall"),
        (SCOPE_ON_VENUE, "On Venue"),
    ]

    team_a = models.CharField(max_length=16)
    team_b = models.CharField(max_length=16)
    scope = models.CharField(max_length=16, choices=SCOPE_CHOICES, default=SCOPE_OVERALL)
    last_n = models.PositiveIntegerField(default=10)

    matches_played_a = models.PositiveIntegerField(default=0)
    matches_played_b = models.PositiveIntegerField(default=0)
    win_pct_a = models.PositiveIntegerField(default=0)
    win_pct_b = models.PositiveIntegerField(default=0)
    avg_score_a = models.PositiveIntegerField(default=0)
    avg_score_b = models.PositiveIntegerField(default=0)
    highest_score_a = models.PositiveIntegerField(default=0)
    highest_score_b = models.PositiveIntegerField(default=0)
    lowest_score_a = models.PositiveIntegerField(default=0)
    lowest_score_b = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Team comparison stat"
        verbose_name_plural = "Team comparison stats"
        constraints = [
            models.UniqueConstraint(fields=["team_a", "team_b", "scope"], name="uniq_teamcomp_pair_scope")
        ]

    def __str__(self):
        return f"{self.team_a} vs {self.team_b} ({self.scope}, last {self.last_n})"


class TeamLastNStat(models.Model):
    """Manually curated team form stats for the last N matches (vs all teams)."""

    SCOPE_OVERALL = "overall"
    SCOPE_ON_VENUE = "on_venue"
    SCOPE_CHOICES = [
        (SCOPE_OVERALL, "Overall"),
        (SCOPE_ON_VENUE, "On Venue"),
    ]

    team = models.CharField(max_length=16)
    scope = models.CharField(max_length=16, choices=SCOPE_CHOICES, default=SCOPE_OVERALL)
    last_n = models.PositiveIntegerField(default=10)

    matches_played = models.PositiveIntegerField(default=0)
    win_pct = models.PositiveIntegerField(default=0)
    avg_score = models.PositiveIntegerField(default=0)
    highest_score = models.PositiveIntegerField(default=0)
    lowest_score = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Team last N stat"
        verbose_name_plural = "Team last N stats"
        constraints = [
            models.UniqueConstraint(fields=["team", "scope"], name="uniq_team_lastn_scope")
        ]

    def __str__(self):
        return f"{self.team} ({self.scope}, last {self.last_n})"


class TeamHeadToHeadStat(models.Model):
    """Manually curated head-to-head stats for two teams."""

    SCOPE_OVERALL = "overall"
    SCOPE_CHOICES = [
        (SCOPE_OVERALL, "Overall"),
    ]

    team_a = models.CharField(max_length=16)
    team_b = models.CharField(max_length=16)
    scope = models.CharField(max_length=16, choices=SCOPE_CHOICES, default=SCOPE_OVERALL)

    played = models.PositiveIntegerField(default=0)
    won_a = models.PositiveIntegerField(default=0)
    won_b = models.PositiveIntegerField(default=0)
    highest_total_a = models.PositiveIntegerField(default=0)
    highest_total_b = models.PositiveIntegerField(default=0)
    lowest_total_a = models.PositiveIntegerField(default=0)
    lowest_total_b = models.PositiveIntegerField(default=0)
    tosses_won_a = models.PositiveIntegerField(default=0)
    tosses_won_b = models.PositiveIntegerField(default=0)
    elected_to_bat_a = models.PositiveIntegerField(default=0)
    elected_to_bat_b = models.PositiveIntegerField(default=0)
    elected_to_field_a = models.PositiveIntegerField(default=0)
    elected_to_field_b = models.PositiveIntegerField(default=0)
    won_toss_and_match_a = models.PositiveIntegerField(default=0)
    won_toss_and_match_b = models.PositiveIntegerField(default=0)
    toss_won_bat_first_match_won_a = models.PositiveIntegerField(default=0)
    toss_won_bat_first_match_won_b = models.PositiveIntegerField(default=0)
    toss_won_bowl_first_match_won_a = models.PositiveIntegerField(default=0)
    toss_won_bowl_first_match_won_b = models.PositiveIntegerField(default=0)
    avg_runs_a = models.FloatField(default=0.0)
    avg_runs_b = models.FloatField(default=0.0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Team head-to-head stat"
        verbose_name_plural = "Team head-to-head stats"
        constraints = [
            models.UniqueConstraint(fields=["team_a", "team_b", "scope"], name="uniq_h2h_pair_scope")
        ]

    def __str__(self):
        return f"{self.team_a} vs {self.team_b} (H2H)"


class TeamFormStat(models.Model):
    """Manually curated team form for last N matches, e.g. 'WWLWL'."""

    team = models.CharField(max_length=16)
    last_n = models.PositiveIntegerField(default=5)
    # String of 'W'/'L' (optionally other markers later). Length should be last_n.
    form = models.CharField(max_length=16)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Team form stat"
        verbose_name_plural = "Team form stats"
        constraints = [
            models.UniqueConstraint(fields=["team", "last_n"], name="uniq_team_form_lastn")
        ]

    def __str__(self):
        return f"{self.team} form (last {self.last_n})"


class SeriesStatsCache(models.Model):
    """
    Cache series-level stats (so the frontend can show them without scraping).
    """

    # e.g. ESPNcricinfo series external id (Big Bash League 2025/26 => 1490534)
    series_external_id = models.CharField(max_length=100, unique=True)
    series_name = models.CharField(max_length=255, blank=True, default="")
    fetched_at = models.DateTimeField(auto_now=True)
    data = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "Series stats cache"
        verbose_name_plural = "Series stats caches"

    def __str__(self):
        return f"SeriesStatsCache(series_external_id={self.series_external_id})"


class MatchHighlightsCache(models.Model):
    """
    Cached YouTube highlights per match to reduce API usage.
    """

    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name="highlights_cache")
    query = models.CharField(max_length=255, blank=True, default="")
    fetched_at = models.DateTimeField(auto_now=True)
    data = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "Match highlights cache"
        verbose_name_plural = "Match highlights caches"

    def __str__(self):
        return f"MatchHighlightsCache(match_id={self.match.external_id})"