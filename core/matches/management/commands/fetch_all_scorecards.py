"""
Fetch and cache scorecards for all matches that don't have one yet.
Uses 1 CricAPI request per match; use --limit and --delay to stay under daily limits.
"""
import time
from django.core.management.base import BaseCommand
from matches.models import Match
from matches.scorecard_helpers import fetch_scorecard, apply_scorecard_to_match


class Command(BaseCommand):
    help = "Fetch scorecards from CricAPI for all matches missing scorecard_data (scores + result)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Max number of matches to fetch (default: all). Use e.g. 30 to stay under 100/day.",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=1.5,
            help="Seconds to wait between API calls (default: 1.5).",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        delay = options["delay"]

        qs = Match.objects.filter(scorecard_data__isnull=True).order_by("id")
        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS("All matches already have scorecards."))
            return

        if limit:
            qs = qs[:limit]
        to_fetch = list(qs)

        self.stdout.write(f"Fetching scorecards for {len(to_fetch)} match(es) (delay={delay}s)...")

        ok = 0
        fail = 0
        for i, match in enumerate(to_fetch, 1):
            self.stdout.write(f"  [{i}/{len(to_fetch)}] {match.team_home} vs {match.team_away} ({match.external_id})... ", ending="")
            scorecard = fetch_scorecard(match.external_id)
            if scorecard and scorecard.get("score"):
                apply_scorecard_to_match(match, scorecard)
                self.stdout.write(self.style.SUCCESS("OK"))
                ok += 1
            else:
                self.stdout.write(self.style.WARNING("no data"))
                fail += 1
            if i < len(to_fetch):
                time.sleep(delay)

        self.stdout.write(self.style.SUCCESS(f"Done. Cached: {ok}, failed/skipped: {fail}."))
        if total > len(to_fetch):
            self.stdout.write(f"Run again to fetch remaining {total - len(to_fetch)} match(es).")
