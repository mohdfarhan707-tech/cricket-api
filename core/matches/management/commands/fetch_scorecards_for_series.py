"""
Fetch and cache scorecards for matches within a selected series.

This is meant for targeted backfills (e.g. ICC Men's T20 World Cup) while staying
under CricAPI daily limits and avoiding repeated "blocked for 15 minutes" loops.
"""
import time

import requests
from django.core.management.base import BaseCommand

from matches.models import Match
from matches.scorecard_helpers import CRICAPI_KEY, apply_scorecard_to_match


def _fetch_scorecard_with_reason(match_id: str) -> tuple[dict | None, str | None]:
    url = f"https://api.cricapi.com/v1/match_scorecard?apikey={CRICAPI_KEY}&id={match_id}"
    try:
        resp = requests.get(url, timeout=12)
        payload = resp.json() if resp.content else {}
        if not isinstance(payload, dict):
            return None, "Invalid response"
        if payload.get("status") != "success":
            return None, str(payload.get("reason") or payload.get("message") or "Unknown failure")
        data = payload.get("data") or {}
        return (data if isinstance(data, dict) else {}), None
    except Exception as e:
        return None, str(e)


class Command(BaseCommand):
    help = "Fetch CricAPI scorecards for matches in a given series (by name contains)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--series-contains",
            type=str,
            default="ICC Men's T20 World Cup",
            help="Series name substring filter (default: ICC Men's T20 World Cup).",
        )
        parser.add_argument(
            "--only-missing",
            action="store_true",
            help="Only fetch matches with missing scorecard_data.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Max number of matches to fetch (default: all).",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=1.6,
            help="Seconds to wait between API calls (default: 1.6).",
        )

    def handle(self, *args, **options):
        needle = (options["series_contains"] or "").strip()
        only_missing = bool(options["only_missing"])
        limit = int(options["limit"] or 0)
        delay = float(options["delay"] or 0)

        qs = Match.objects.select_related("series").all()
        if needle:
            qs = qs.filter(series__name__icontains=needle)
        if only_missing:
            qs = qs.filter(scorecard_data__isnull=True)
        qs = qs.order_by("id")
        if limit:
            qs = qs[:limit]
        matches = list(qs)

        if not matches:
            self.stdout.write(self.style.WARNING("No matches found for selection."))
            return

        self.stdout.write(
            f"Fetching scorecards for {len(matches)} match(es) "
            f"(series contains='{needle}', only_missing={only_missing}, delay={delay}s)..."
        )

        ok = 0
        skipped = 0
        for i, m in enumerate(matches, 1):
            self.stdout.write(
                f"  [{i}/{len(matches)}] {m.team_home} vs {m.team_away} ({m.external_id})... ",
                ending="",
            )
            scorecard, reason = _fetch_scorecard_with_reason(m.external_id)
            if not scorecard:
                # If CricAPI blocks us, stop immediately to avoid wasting the daily quota.
                if reason and "blocked" in reason.lower():
                    self.stdout.write(self.style.ERROR(f"BLOCKED: {reason}"))
                    self.stdout.write(self.style.WARNING("Stop now and re-run after the block window expires."))
                    break
                self.stdout.write(self.style.WARNING(reason or "no data"))
                skipped += 1
            else:
                apply_scorecard_to_match(m, scorecard)
                self.stdout.write(self.style.SUCCESS("OK"))
                ok += 1

            if delay and i < len(matches):
                time.sleep(delay)

        self.stdout.write(self.style.SUCCESS(f"Done. Cached: {ok}, skipped/failed: {skipped}."))

