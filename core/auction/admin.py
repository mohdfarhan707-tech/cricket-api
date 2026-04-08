from django.contrib import admin

from .models import AuctionBidLog, AuctionPlayer, AuctionSession, AuctionTeam


@admin.register(AuctionSession)
class AuctionSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "league", "status", "current_player_index", "round_number", "created_at")
    list_filter = ("league", "status")
    search_fields = ("id",)
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(AuctionTeam)
class AuctionTeamAdmin(admin.ModelAdmin):
    list_display = ("name", "session", "short_code", "is_user", "budget_lakhs", "squad_count", "strategy")
    list_filter = ("is_user", "strategy")
    search_fields = ("name", "short_code")
    raw_id_fields = ("session",)


@admin.register(AuctionPlayer)
class AuctionPlayerAdmin(admin.ModelAdmin):
    list_display = ("name", "session", "category", "base_price_lakhs", "status", "order_index")
    list_filter = ("category", "status")
    search_fields = ("name",)
    raw_id_fields = ("session", "sold_to")


@admin.register(AuctionBidLog)
class AuctionBidLogAdmin(admin.ModelAdmin):
    list_display = ("session", "team", "player", "amount_lakhs", "created_at")
    list_filter = ("session",)
    search_fields = ("team__name", "player__name")
    raw_id_fields = ("session", "team", "player")
    ordering = ("-created_at",)
