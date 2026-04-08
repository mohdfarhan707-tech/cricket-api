from django.contrib import admin

from .models import (
    Match,
    MatchHighlightsCache,
    Series,
    SeriesStatsCache,
    TeamComparisonStat,
    TeamFormStat,
    TeamHeadToHeadStat,
    TeamLastNStat,
)


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ("name", "external_id")
    search_fields = ("name", "external_id")
    ordering = ("name",)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("short_name", "series", "status", "team_home", "team_away", "external_id")
    list_filter = ("series", "status")
    search_fields = ("name", "external_id", "team_home", "team_away", "status")
    ordering = ("-id",)
    raw_id_fields = ("series",)
    readonly_fields = ("scorecard_data_preview", "scorecard_data")

    @admin.display(description="Match")
    def short_name(self, obj: Match) -> str:
        n = (obj.name or "").strip()
        return (n[:80] + "…") if len(n) > 80 else n

    @admin.display(description="Scorecard (summary)")
    def scorecard_data_preview(self, obj: Match) -> str:
        sc = obj.scorecard_data
        if not sc or not isinstance(sc, dict):
            return "—"
        score = sc.get("score")
        if isinstance(score, list) and score:
            return f"{len(score)} innings in score[]"
        return "present" if sc else "—"


@admin.register(TeamComparisonStat)
class TeamComparisonStatAdmin(admin.ModelAdmin):
    list_display = ("team_a", "team_b", "scope", "last_n", "updated_at")
    list_filter = ("scope",)
    search_fields = ("team_a", "team_b")


@admin.register(TeamLastNStat)
class TeamLastNStatAdmin(admin.ModelAdmin):
    list_display = ("team", "scope", "last_n", "win_pct", "updated_at")
    list_filter = ("scope",)
    search_fields = ("team",)


@admin.register(TeamHeadToHeadStat)
class TeamHeadToHeadStatAdmin(admin.ModelAdmin):
    list_display = ("team_a", "team_b", "scope", "played", "updated_at")
    list_filter = ("scope",)
    search_fields = ("team_a", "team_b")


@admin.register(TeamFormStat)
class TeamFormStatAdmin(admin.ModelAdmin):
    list_display = ("team", "last_n", "form", "updated_at")
    search_fields = ("team", "form")


@admin.register(SeriesStatsCache)
class SeriesStatsCacheAdmin(admin.ModelAdmin):
    list_display = ("series_name", "series_external_id", "fetched_at")
    search_fields = ("series_name", "series_external_id")
    ordering = ("-fetched_at",)


@admin.register(MatchHighlightsCache)
class MatchHighlightsCacheAdmin(admin.ModelAdmin):
    list_display = ("match", "query", "fetched_at")
    search_fields = ("query", "match__name", "match__external_id")
    raw_id_fields = ("match",)
    ordering = ("-fetched_at",)
