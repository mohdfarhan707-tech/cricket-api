"""
REST API for mini auction (IPL / PSL).
"""
from __future__ import annotations

import random
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .auction_engine import (
    ALLOWED_BASE_PRICE_LAKHS,
    AUCTION_WINDOW_SIZE,
    DEFAULT_BUDGET_LAKHS,
    MAX_SQUAD,
    MIN_SQUAD,
    PLAYER_MAX_LAKHS,
    PLAYER_MIN_LAKHS,
    WINDOW_UNSOLD_MAX,
    WINDOW_UNSOLD_MIN,
    autobid_probability,
    category_interest_bonus,
    max_bid_allowed,
    next_bid_amount,
    random_timer_seconds,
)
from .ipl_players_data import get_ipl_player_rows, resolve_ipl_base_price_lakhs
from .models import AuctionBidLog, AuctionPlayer, AuctionSession, AuctionTeam
from .psl_players_data import get_psl_player_rows, resolve_psl_base_price_lakhs

IPL_TEAMS = [
    ("MI", "Mumbai Indians"),
    ("CSK", "Chennai Super Kings"),
    ("RCB", "Royal Challengers Bengaluru"),
    ("KKR", "Kolkata Knight Riders"),
    ("RR", "Rajasthan Royals"),
    ("SRH", "Sunrisers Hyderabad"),
    ("DC", "Delhi Capitals"),
    ("PBKS", "Punjab Kings"),
    ("LSG", "Lucknow Super Giants"),
    ("GT", "Gujarat Titans"),
]

PSL_TEAMS = [
    ("IU", "Islamabad United"),
    ("KK", "Karachi Kings"),
    ("LQ", "Lahore Qalandars"),
    ("MS", "Multan Sultans"),
    ("PZ", "Peshawar Zalmi"),
    ("QG", "Quetta Gladiators"),
]

def _build_player_pool(league: str) -> list[dict]:
    """Full IPL/PSL roster — every listed player enters the auction (order shuffled)."""
    rows = get_ipl_player_rows() if league == AuctionSession.LEAGUE_IPL else get_psl_player_rows()
    random.shuffle(rows)
    picked = list(rows)
    out: list[dict] = []
    for i, row in enumerate(picked):
        if league == AuctionSession.LEAGUE_IPL:
            base = resolve_ipl_base_price_lakhs(row["name"])
        else:
            base = resolve_psl_base_price_lakhs(row["name"])
        out.append(
            {
                "name": row["name"],
                "category": row["category"],
                "base_price_lakhs": base,
                "order_index": i,
            }
        )
    random.shuffle(out)
    for i, p in enumerate(out):
        p["order_index"] = i
    return out


def _default_category_interest():
    return {
        "batsman": round(random.uniform(0.4, 0.95), 2),
        "bowler": round(random.uniform(0.4, 0.95), 2),
        "allrounder": round(random.uniform(0.4, 0.95), 2),
        "wk": round(random.uniform(0.3, 0.85), 2),
    }


def _serialize_team(t: AuctionTeam) -> dict:
    return {
        "id": str(t.id),
        "name": t.name,
        "short_code": t.short_code,
        "is_user": t.is_user,
        "strategy": t.strategy,
        "budget_lakhs": t.budget_lakhs,
        "budget_crores": round(t.budget_lakhs / 100.0, 2),
        "squad_count": t.squad_count,
    }


def _pick_forced_sale_team(session: AuctionSession, p: AuctionPlayer) -> AuctionTeam | None:
    """AI franchise with the most purse left that can afford at least base price (forced sale)."""
    price = p.base_price_lakhs
    candidates: list[AuctionTeam] = []
    for t in session.teams.all():
        if t.is_user:
            continue
        if t.squad_count >= MAX_SQUAD:
            continue
        if max_bid_allowed(t.budget_lakhs, t.squad_count) >= price:
            candidates.append(t)
    if not candidates:
        return None
    candidates.sort(key=lambda t: (-t.budget_lakhs, t.squad_count))
    return candidates[0]


def _serialize_player(p: AuctionPlayer) -> dict:
    return {
        "id": str(p.id),
        "name": p.name,
        "category": p.category,
        "base_price_lakhs": p.base_price_lakhs,
        "base_price_crores": round(p.base_price_lakhs / 100.0, 2),
        "order_index": p.order_index,
        "status": p.status,
        "sold_price_lakhs": p.sold_price_lakhs,
        "sold_to_id": str(p.sold_to_id) if p.sold_to_id else None,
    }


def _open_lot(session: AuctionSession) -> None:
    """
    current_player_index is the index into the FULL ordered pool (order_index 0..N-1),
    not into the filtered pending-only list — using pending[] caused wrong player/base bids.
    """
    players = list(session.players.all().order_by("order_index"))
    idx = session.current_player_index
    if idx >= len(players):
        session.status = AuctionSession.STATUS_FINISHED
        session.lot_ends_at = None
        session.save(update_fields=["status", "lot_ends_at", "updated_at"])
        return
    p = players[idx]
    if idx % AUCTION_WINDOW_SIZE == 0:
        session.window_unsold_count = 0
    session.current_bid_lakhs = p.base_price_lakhs
    session.highest_bidder = None
    session.lot_ends_at = timezone.now() + timedelta(seconds=random_timer_seconds())
    session.save(
        update_fields=["current_bid_lakhs", "highest_bidder", "lot_ends_at", "updated_at", "window_unsold_count"]
    )


def _resolve_lot_if_needed(session: AuctionSession) -> bool:
    """Return True if resolved (or finished)."""
    if session.status != AuctionSession.STATUS_RUNNING:
        return False
    if not session.lot_ends_at or timezone.now() < session.lot_ends_at:
        return False

    players = list(session.players.order_by("order_index"))
    idx = session.current_player_index
    if idx >= len(players):
        session.status = AuctionSession.STATUS_FINISHED
        session.save(update_fields=["status", "updated_at"])
        return True

    p = players[idx]
    hb = session.highest_bidder
    price = session.current_bid_lakhs
    wu = session.window_unsold_count or 0

    sold_ok = (
        hb is not None
        and price > 0
        and hb.budget_lakhs >= price
        and hb.squad_count < MAX_SQUAD
    )

    if sold_ok:
        hb.budget_lakhs -= price
        hb.squad_count += 1
        hb.save(update_fields=["budget_lakhs", "squad_count"])
        p.status = AuctionPlayer.STATUS_SOLD
        p.sold_price_lakhs = price
        p.sold_to = hb
        p.save(update_fields=["status", "sold_price_lakhs", "sold_to"])
    else:
        # No valid winning bid — normally unsold, unless we've hit max unsold in this window
        if wu >= WINDOW_UNSOLD_MAX:
            buyer = _pick_forced_sale_team(session, p)
            if buyer is not None:
                price = p.base_price_lakhs
                buyer.budget_lakhs -= price
                buyer.squad_count += 1
                buyer.save(update_fields=["budget_lakhs", "squad_count"])
                p.status = AuctionPlayer.STATUS_SOLD
                p.sold_price_lakhs = price
                p.sold_to = buyer
                p.save(update_fields=["status", "sold_price_lakhs", "sold_to"])
            else:
                p.status = AuctionPlayer.STATUS_UNSOLD
                p.save(update_fields=["status"])
                session.window_unsold_count = wu + 1
        else:
            p.status = AuctionPlayer.STATUS_UNSOLD
            p.save(update_fields=["status"])
            session.window_unsold_count = wu + 1

    session.current_player_index = idx + 1
    session.highest_bidder = None
    session.save(update_fields=["current_player_index", "highest_bidder", "window_unsold_count", "updated_at"])

    if session.current_player_index >= session.players.count():
        session.status = AuctionSession.STATUS_FINISHED
        session.lot_ends_at = None
        session.save(update_fields=["status", "lot_ends_at", "updated_at"])
        return True

    _open_lot(session)
    return True


def _maybe_autobid(session: AuctionSession) -> None:
    if session.status != AuctionSession.STATUS_RUNNING or not session.lot_ends_at:
        return
    if timezone.now() >= session.lot_ends_at:
        return
    now = timezone.now()
    if session.last_autobid_at and (now - session.last_autobid_at).total_seconds() < random.uniform(0.65, 1.35):
        return

    players = list(session.players.order_by("order_index"))
    idx = session.current_player_index
    if idx >= len(players):
        return
    p = players[idx]
    # Table amount must match this lot's base until someone bids (fixes stale session drift)
    if session.highest_bidder_id is None and session.current_bid_lakhs != p.base_price_lakhs:
        session.current_bid_lakhs = p.base_price_lakhs
        session.save(update_fields=["current_bid_lakhs", "updated_at"])

    if session.highest_bidder_id is None:
        next_amt = next_bid_amount(p.base_price_lakhs)
    else:
        next_amt = next_bid_amount(session.current_bid_lakhs)

    slot = idx % AUCTION_WINDOW_SIZE
    wu = session.window_unsold_count or 0
    # Need ≥1 unsold per window: last 3 lots with 0 unsold — no AI bids so timer can expire unsold
    if (
        wu == 0
        and slot >= AUCTION_WINDOW_SIZE - 3
        and session.highest_bidder_id is None
    ):
        return

    # Higher remaining purse first (then smaller squads as tie-breaker)
    teams = list(session.teams.all())
    teams.sort(key=lambda t: (-t.budget_lakhs, t.squad_count))

    time_left = (session.lot_ends_at - now).total_seconds()
    near_end = time_left < 4.0

    ai_teams = [t for t in teams if not t.is_user]
    min_ai_squad = min((x.squad_count for x in ai_teams), default=0)

    for t in teams:
        if t.is_user:
            continue
        if t.squad_count >= MAX_SQUAD:
            continue
        max_b = max_bid_allowed(t.budget_lakhs, t.squad_count)
        if max_b < next_amt:
            continue
        if session.highest_bidder_id == t.id:
            continue
        bonus = category_interest_bonus(t, p.category)
        prob = autobid_probability(t.strategy, bonus)
        # Teams with more purse left bid more aggressively
        purse_edge = 0.22 * (t.budget_lakhs / DEFAULT_BUDGET_LAKHS)
        prob = min(0.95, prob + purse_edge)
        if near_end:
            prob = min(0.95, prob + 0.2)
        # Nudge under-buying teams so more franchises stay active in the auction
        if t.squad_count < 2:
            prob = min(0.95, prob + 0.28)
        elif t.squad_count < 4:
            prob = min(0.95, prob + 0.12)
        if t.squad_count == min_ai_squad and len(ai_teams) > 1:
            prob = min(0.95, prob + 0.1)
        if session.highest_bidder_id is None:
            prob = min(0.95, prob + 0.12)
        if random.random() > prob:
            continue
        # Softer cap so more franchises stay in the bidding (all teams "active")
        soft_cap = p.base_price_lakhs * (
            3.6
            if t.strategy == AuctionTeam.STRATEGY_AGGRESSIVE
            else 2.85
            if t.strategy == AuctionTeam.STRATEGY_BALANCED
            else 2.15
        )
        if t.squad_count < 2:
            soft_cap = int(soft_cap * 1.45)
        elif t.squad_count < 5:
            soft_cap = int(soft_cap * 1.18)
        if next_amt > soft_cap:
            continue

        session.current_bid_lakhs = next_amt
        session.highest_bidder = t
        session.lot_ends_at = timezone.now() + timedelta(seconds=random_timer_seconds())
        session.last_autobid_at = now
        session.save(update_fields=["current_bid_lakhs", "highest_bidder", "lot_ends_at", "last_autobid_at", "updated_at"])
        AuctionBidLog.objects.create(session=session, team=t, player=p, amount_lakhs=next_amt)
        return


class AuctionCreateAPI(APIView):
    """POST: league, user_team_code — create session + pool + teams."""

    def post(self, request):
        league = (request.data.get("league") or "ipl").lower()
        user_code = (request.data.get("user_team_code") or "").strip().upper()

        teams_src = IPL_TEAMS if league == AuctionSession.LEAGUE_IPL else PSL_TEAMS
        codes = {c for c, _ in teams_src}
        if user_code not in codes:
            return Response(
                {"error": "Invalid user_team_code for league", "valid": list(codes)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session = AuctionSession.objects.create(league=league, status=AuctionSession.STATUS_SETUP)

        for code, full in teams_src:
            strat = random.choice(
                [AuctionTeam.STRATEGY_AGGRESSIVE, AuctionTeam.STRATEGY_BALANCED, AuctionTeam.STRATEGY_DEFENSIVE]
            )
            AuctionTeam.objects.create(
                session=session,
                name=full,
                short_code=code,
                is_user=(code == user_code),
                strategy=strat,
                category_interest=_default_category_interest(),
                budget_lakhs=DEFAULT_BUDGET_LAKHS,
            )

        user_team = session.teams.filter(short_code=user_code).first()
        session.user_team = user_team
        session.save(update_fields=["user_team"])

        pool = _build_player_pool(league)
        for row in pool:
            AuctionPlayer.objects.create(session=session, **row)

        return Response(
            {
                "session_id": str(session.id),
                "league": league,
                "user_team": _serialize_team(user_team),
                "teams": [_serialize_team(x) for x in session.teams.all()],
                "player_count": session.players.count(),
            },
            status=status.HTTP_201_CREATED,
        )


class AuctionBeginAPI(APIView):
    """POST: start first lot."""

    def post(self, request, session_id):
        session = AuctionSession.objects.filter(id=session_id).first()
        if not session:
            return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)
        if session.status != AuctionSession.STATUS_SETUP:
            return Response({"error": "Already started or finished"}, status=status.HTTP_400_BAD_REQUEST)

        session.status = AuctionSession.STATUS_RUNNING
        session.current_player_index = 0
        session.save(update_fields=["status", "current_player_index"])
        _open_lot(session)
        return Response({"ok": True, "state": _full_state(session)})


class AuctionStateAPI(APIView):
    def get(self, request, session_id):
        session = AuctionSession.objects.filter(id=session_id).prefetch_related("teams", "players").first()
        if not session:
            return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)
        _resolve_lot_if_needed(session)
        session.refresh_from_db()
        if session.status == AuctionSession.STATUS_RUNNING:
            _maybe_autobid(session)
            _resolve_lot_if_needed(session)
            session.refresh_from_db()
        return Response(_full_state(session))


class AuctionBidAPI(APIView):
    """POST: team_id (user's team) places next bid."""

    def post(self, request, session_id):
        session = AuctionSession.objects.filter(id=session_id).prefetch_related("teams", "players").first()
        if not session:
            return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)
        if session.status != AuctionSession.STATUS_RUNNING:
            return Response({"error": "Auction not running"}, status=status.HTTP_400_BAD_REQUEST)

        _resolve_lot_if_needed(session)
        session.refresh_from_db()
        if session.status != AuctionSession.STATUS_RUNNING:
            return Response(_full_state(session))

        team_id = request.data.get("team_id")
        team = session.teams.filter(id=team_id).first() if team_id else None
        if not team:
            return Response({"error": "Invalid team_id"}, status=status.HTTP_400_BAD_REQUEST)
        if not team.is_user:
            return Response({"error": "Only user team can bid via this endpoint"}, status=status.HTTP_403_FORBIDDEN)

        players = list(session.players.order_by("order_index"))
        idx = session.current_player_index
        if idx >= len(players):
            return Response({"error": "No active lot"}, status=status.HTTP_400_BAD_REQUEST)
        p = players[idx]

        if session.highest_bidder_id is None and session.current_bid_lakhs != p.base_price_lakhs:
            session.current_bid_lakhs = p.base_price_lakhs
            session.save(update_fields=["current_bid_lakhs", "updated_at"])

        if session.highest_bidder is None:
            next_amt = next_bid_amount(p.base_price_lakhs)
        else:
            next_amt = next_bid_amount(session.current_bid_lakhs)

        if team.squad_count >= MAX_SQUAD:
            return Response({"error": "Squad full"}, status=status.HTTP_400_BAD_REQUEST)

        max_b = max_bid_allowed(team.budget_lakhs, team.squad_count)
        if max_b < next_amt:
            return Response(
                {"error": "Insufficient budget (must reserve for minimum squad)", "max_bid_lakhs": max_b, "next_bid_lakhs": next_amt},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if session.highest_bidder_id == team.id:
            return Response({"error": "Already highest bidder"}, status=status.HTTP_400_BAD_REQUEST)

        session.current_bid_lakhs = next_amt
        session.highest_bidder = team
        session.lot_ends_at = timezone.now() + timedelta(seconds=random_timer_seconds())
        session.last_autobid_at = timezone.now()
        session.save(update_fields=["current_bid_lakhs", "highest_bidder", "lot_ends_at", "last_autobid_at", "updated_at"])
        AuctionBidLog.objects.create(session=session, team=team, player=p, amount_lakhs=next_amt)

        return Response(_full_state(session))


def _full_state(session: AuctionSession) -> dict:
    session.refresh_from_db()
    teams = [_serialize_team(t) for t in session.teams.all()]
    players = [_serialize_player(p) for p in session.players.all().order_by("order_index")]
    current = None
    if session.status in (AuctionSession.STATUS_RUNNING, AuctionSession.STATUS_PAUSED):
        plist = [p for p in session.players.all().order_by("order_index")]
        if session.current_player_index < len(plist):
            cp = plist[session.current_player_index]
            if cp.status == AuctionPlayer.STATUS_PENDING:
                if session.highest_bidder_id is None:
                    table_lakhs = cp.base_price_lakhs
                    next_amt = next_bid_amount(cp.base_price_lakhs)
                else:
                    table_lakhs = session.current_bid_lakhs
                    next_amt = next_bid_amount(session.current_bid_lakhs)
                sec_left = 0
                if session.lot_ends_at and session.status == AuctionSession.STATUS_RUNNING:
                    sec_left = max(
                        0,
                        int((session.lot_ends_at - timezone.now()).total_seconds()),
                    )
                current = {
                    "player": _serialize_player(cp),
                    "current_bid_lakhs": table_lakhs,
                    "next_bid_lakhs": next_amt,
                    "highest_bidder_id": str(session.highest_bidder_id) if session.highest_bidder_id else None,
                    "lot_ends_at": session.lot_ends_at.isoformat() if session.lot_ends_at else None,
                    "seconds_left": sec_left,
                    "paused": session.status == AuctionSession.STATUS_PAUSED,
                }

    user_team = session.user_team
    squads = {}
    for t in session.teams.all():
        squads[str(t.id)] = [_serialize_player(x) for x in session.players.filter(sold_to=t).order_by("order_index")]

    return {
        "session_id": str(session.id),
        "league": session.league,
        "status": session.status,
        "round_number": session.round_number,
        "current_player_index": session.current_player_index,
        "teams": teams,
        "players": players,
        "squads": squads,
        "current_lot": current,
        "user_team_id": str(user_team.id) if user_team else None,
        "rules": {
            "budget_crores": DEFAULT_BUDGET_LAKHS / 100,
            "min_squad": MIN_SQUAD,
            "max_squad": MAX_SQUAD,
            "player_base_min_lakhs": PLAYER_MIN_LAKHS,
            "player_base_max_lakhs": PLAYER_MAX_LAKHS,
            "allowed_base_price_lakhs": list(ALLOWED_BASE_PRICE_LAKHS),
            "auction_window_size": AUCTION_WINDOW_SIZE,
            "window_unsold_min": WINDOW_UNSOLD_MIN,
            "window_unsold_max": WINDOW_UNSOLD_MAX,
            "window_unsold_count": session.window_unsold_count,
        },
    }


class AuctionPoolPreviewAPI(APIView):
    """
    GET ?league=ipl|psl
    Canonical player names/categories from the same source as auction pool creation
    (`ipl_players_data` / `psl_players_data`).
    """

    def get(self, request):
        league = (request.query_params.get("league") or "ipl").lower()
        if league == AuctionSession.LEAGUE_IPL:
            rows = get_ipl_player_rows()
        elif league == AuctionSession.LEAGUE_PSL:
            rows = get_psl_player_rows()
        else:
            return Response({"error": "Invalid league"}, status=status.HTTP_400_BAD_REQUEST)

        if league == AuctionSession.LEAGUE_IPL:
            players = [
                {
                    "name": r["name"],
                    "category": r["category"],
                    "base_price_lakhs": resolve_ipl_base_price_lakhs(r["name"]),
                }
                for r in rows
            ]
        else:
            players = [
                {
                    "name": r["name"],
                    "category": r["category"],
                    "base_price_lakhs": resolve_psl_base_price_lakhs(r["name"]),
                }
                for r in rows
            ]
        return Response({"league": league, "count": len(players), "players": players})


class AuctionStopAPI(APIView):
    """POST: pause the auction (timer frozen, no autobids)."""

    def post(self, request, session_id):
        session = AuctionSession.objects.filter(id=session_id).first()
        if not session:
            return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)
        if session.status != AuctionSession.STATUS_RUNNING:
            return Response({"error": "Auction is not running"}, status=status.HTTP_400_BAD_REQUEST)
        session.status = AuctionSession.STATUS_PAUSED
        session.lot_ends_at = None
        session.save(update_fields=["status", "lot_ends_at", "updated_at"])
        return Response({"ok": True, "state": _full_state(session)})


class AuctionResumeAPI(APIView):
    """POST: resume a paused auction."""

    def post(self, request, session_id):
        session = AuctionSession.objects.filter(id=session_id).first()
        if not session:
            return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)
        if session.status != AuctionSession.STATUS_PAUSED:
            return Response({"error": "Auction is not paused"}, status=status.HTTP_400_BAD_REQUEST)
        session.status = AuctionSession.STATUS_RUNNING
        session.lot_ends_at = timezone.now() + timedelta(seconds=random_timer_seconds())
        session.save(update_fields=["status", "lot_ends_at", "updated_at"])
        return Response({"ok": True, "state": _full_state(session)})


class AuctionRestartAPI(APIView):
    """
    POST: reset session to setup with a fresh player pool and full budgets.
    Same teams; user must call begin again to start.
    """

    def post(self, request, session_id):
        session = AuctionSession.objects.filter(id=session_id).prefetch_related("teams").first()
        if not session:
            return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)

        AuctionBidLog.objects.filter(session=session).delete()
        session.players.all().delete()

        for t in session.teams.all():
            t.budget_lakhs = DEFAULT_BUDGET_LAKHS
            t.squad_count = 0
            t.save(update_fields=["budget_lakhs", "squad_count"])

        league = session.league
        pool = _build_player_pool(league)
        for row in pool:
            AuctionPlayer.objects.create(session=session, **row)

        session.status = AuctionSession.STATUS_SETUP
        session.current_player_index = 0
        session.current_bid_lakhs = 0
        session.highest_bidder = None
        session.lot_ends_at = None
        session.last_autobid_at = None
        session.window_unsold_count = 0
        session.save(
            update_fields=[
                "status",
                "current_player_index",
                "current_bid_lakhs",
                "highest_bidder",
                "lot_ends_at",
                "last_autobid_at",
                "window_unsold_count",
                "updated_at",
            ]
        )
        return Response({"ok": True, "state": _full_state(session)})
