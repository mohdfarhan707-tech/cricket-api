from django.core.management.base import BaseCommand
from matches.models import Match
from matches.scorecard_helpers import apply_scorecard_to_match


class Command(BaseCommand):
    help = (
        "Re-apply existing cached scorecard_data to Matches so that the "
        "batting-first team is stored as team_home (left) using the latest logic."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=5,
            help="Maximum number of matches to update (default: 5).",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        qs = (
            Match.objects.filter(scorecard_data__isnull=False)
            .order_by("id")
        )
        if limit > 0:
            qs = qs[:limit]

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.WARNING("No matches with cached scorecard_data found."))
            return

        self.stdout.write(f"Re-applying cached scorecards for {total} match(es)...")

        updated = 0
        for match in qs:
            data = match.scorecard_data
            if not data:
                continue
            apply_scorecard_to_match(match, data)
            updated += 1
            self.stdout.write(f"  - Updated match {match.id} ({match.external_id})")

        self.stdout.write(self.style.SUCCESS(f"Done. Updated {updated} match(es)."))

