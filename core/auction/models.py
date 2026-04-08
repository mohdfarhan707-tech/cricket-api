import uuid
from django.db import models
from django.utils import timezone

from .auction_engine import (
    DEFAULT_BUDGET_LAKHS,
    MIN_SQUAD,
    MAX_SQUAD,
    PLAYER_MIN_LAKHS,
    PLAYER_MAX_LAKHS,
)


class AuctionSession(models.Model):
    LEAGUE_IPL = "ipl"
    LEAGUE_PSL = "psl"
    LEAGUE_CHOICES = [(LEAGUE_IPL, "IPL"), (LEAGUE_PSL, "PSL")]

    STATUS_SETUP = "setup"
    STATUS_RUNNING = "running"
    STATUS_PAUSED = "paused"
    STATUS_FINISHED = "finished"
    STATUS_CHOICES = [
        (STATUS_SETUP, "Setup"),
        (STATUS_RUNNING, "Running"),
        (STATUS_PAUSED, "Paused"),
        (STATUS_FINISHED, "Finished"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    league = models.CharField(max_length=8, choices=LEAGUE_CHOICES)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_SETUP)
    user_team = models.ForeignKey(
        "AuctionTeam",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_sessions",
    )
    current_player_index = models.IntegerField(default=0)
    # Active lot
    current_bid_lakhs = models.IntegerField(default=0)
    highest_bidder = models.ForeignKey(
        "AuctionTeam",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leading_lots",
    )
    lot_ends_at = models.DateTimeField(null=True, blank=True)
    last_autobid_at = models.DateTimeField(null=True, blank=True)
    round_number = models.PositiveSmallIntegerField(default=1)
    # Unsold count within the current block of AUCTION_WINDOW_SIZE players (reset each window)
    window_unsold_count = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Auction session"
        verbose_name_plural = "Auction sessions"


class AuctionTeam(models.Model):
    STRATEGY_AGGRESSIVE = "aggressive"
    STRATEGY_BALANCED = "balanced"
    STRATEGY_DEFENSIVE = "defensive"
    STRATEGY_CHOICES = [
        (STRATEGY_AGGRESSIVE, "Aggressive"),
        (STRATEGY_BALANCED, "Balanced"),
        (STRATEGY_DEFENSIVE, "Defensive"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(AuctionSession, on_delete=models.CASCADE, related_name="teams")
    name = models.CharField(max_length=64)
    short_code = models.CharField(max_length=8, blank=True, default="")
    is_user = models.BooleanField(default=False)
    strategy = models.CharField(max_length=16, choices=STRATEGY_CHOICES, default=STRATEGY_BALANCED)
    # JSON: {"batsman":0.8,"bowler":0.5,...} 0-1 interest weights
    category_interest = models.JSONField(default=dict, blank=True)
    budget_lakhs = models.IntegerField(default=DEFAULT_BUDGET_LAKHS)
    squad_count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["name"]
        unique_together = [["session", "name"]]
        verbose_name = "Auction team"
        verbose_name_plural = "Auction teams"


class AuctionPlayer(models.Model):
    CAT_BAT = "Batsman"
    CAT_BOWL = "Bowler"
    CAT_AR = "All-rounder"
    CAT_WK = "WK"
    CATEGORY_CHOICES = [
        (CAT_BAT, "Batsman"),
        (CAT_BOWL, "Bowler"),
        (CAT_AR, "All-rounder"),
        (CAT_WK, "WK"),
    ]

    STATUS_PENDING = "pending"
    STATUS_SOLD = "sold"
    STATUS_UNSOLD = "unsold"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SOLD, "Sold"),
        (STATUS_UNSOLD, "Unsold"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(AuctionSession, on_delete=models.CASCADE, related_name="players")
    name = models.CharField(max_length=128)
    base_price_lakhs = models.IntegerField()
    category = models.CharField(max_length=16, choices=CATEGORY_CHOICES)
    order_index = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    sold_price_lakhs = models.IntegerField(null=True, blank=True)
    sold_to = models.ForeignKey(
        AuctionTeam,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchases",
    )

    class Meta:
        ordering = ["order_index"]
        verbose_name = "Auction player"
        verbose_name_plural = "Auction players"


class AuctionBidLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    session = models.ForeignKey(AuctionSession, on_delete=models.CASCADE, related_name="bid_logs")
    team = models.ForeignKey(AuctionTeam, on_delete=models.CASCADE)
    player = models.ForeignKey(AuctionPlayer, on_delete=models.CASCADE)
    amount_lakhs = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Auction bid log"
        verbose_name_plural = "Auction bid logs"
