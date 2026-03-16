from django.core.management.base import BaseCommand
from django.db.models import Q

from matches.models import Match
from matches.scorecard_helpers import apply_scorecard_to_match


class Command(BaseCommand):
    help = (
        "Re-apply cached Match.scorecard_data for all matches (or a specific series) "
        "to update home/away batting order + scores from scorecard."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--series-id",
            type=str,
            default="",
            help="Optional Series.external_id to limit updates to one series.",
        )
        parser.add_argument(
            "--only-missing",
            action="store_true",
            help="Only update matches where home_score/away_score are empty.",
        )

    def handle(self, *args, **options):
        series_id = (options.get("series_id") or "").strip()
        only_missing = bool(options.get("only_missing"))

        qs = Match.objects.filter(scorecard_data__isnull=False)
        if series_id:
            qs = qs.filter(series__external_id=series_id)

        if only_missing:
            qs = qs.filter(Q(home_score__in=["", None]) | Q(away_score__in=["", None]))

        qs = qs.order_by("id")

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.WARNING("No matches with cached scorecard_data found for selection."))
            return

        self.stdout.write(f"Re-applying cached scorecards for {total} match(es)...")

        updated = 0
        for match in qs:
            data = match.scorecard_data
            if not data:
                continue
            apply_scorecard_to_match(match, data)
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"Done. Updated {updated} match(es)."))

