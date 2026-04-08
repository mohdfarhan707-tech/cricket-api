from django.contrib import admin

from .models import AllRounderRanking, BatterRanking, BowlerRanking, TeamRanking


@admin.register(TeamRanking)
class TeamRankingAdmin(admin.ModelAdmin):
    list_display = ("team_name", "team_code", "format_type", "rank", "rating", "last_updated")
    list_filter = ("format_type",)
    search_fields = ("team_name", "team_code")
    ordering = ("format_type", "rank")


@admin.register(BatterRanking)
class BatterRankingAdmin(admin.ModelAdmin):
    list_display = ("player_name", "country", "format_type", "rank", "rating", "last_updated")
    list_filter = ("format_type",)
    search_fields = ("player_name", "country")
    ordering = ("format_type", "rank")


@admin.register(BowlerRanking)
class BowlerRankingAdmin(admin.ModelAdmin):
    list_display = ("player_name", "country", "format_type", "rank", "rating", "last_updated")
    list_filter = ("format_type",)
    search_fields = ("player_name", "country")
    ordering = ("format_type", "rank")


@admin.register(AllRounderRanking)
class AllRounderRankingAdmin(admin.ModelAdmin):
    list_display = ("player_name", "country", "format_type", "rank", "rating", "last_updated")
    list_filter = ("format_type",)
    search_fields = ("player_name", "country")
    ordering = ("format_type", "rank")
