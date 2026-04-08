from django.contrib import admin

from .models import LiveMatch


@admin.register(LiveMatch)
class LiveMatchAdmin(admin.ModelAdmin):
    list_display = (
        "short_name",
        "external_id",
        "team_home",
        "team_away",
        "status",
        "is_live",
        "is_finished",
        "has_scorecard",
        "last_updated",
    )
    list_filter = ("is_live", "is_finished", "uses_ipl_api")
    search_fields = ("name", "external_id", "team_home", "team_away", "status")
    ordering = ("-last_updated",)
    readonly_fields = ("last_updated", "scorecard_data")

    @admin.display(description="Match")
    def short_name(self, obj: LiveMatch) -> str:
        n = (obj.name or "").strip()
        return (n[:72] + "…") if len(n) > 72 else (n or "—")

    @admin.display(description="Scorecard cached", boolean=True)
    def has_scorecard(self, obj: LiveMatch) -> bool:
        return bool(obj.scorecard_data)
