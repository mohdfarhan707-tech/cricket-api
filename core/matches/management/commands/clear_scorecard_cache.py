"""Clear cached scorecard JSON for a match (CricAPI external id) in Match and LiveMatch."""

from django.core.management.base import BaseCommand, CommandError

from live.models import LiveMatch
from matches.models import Match


class Command(BaseCommand):
    help = (
        "Set scorecard_data to NULL for the given match id in both matches_match "
        "and live_livematch so the next API request refetches from CricAPI."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "match_id",
            type=str,
            help="CricAPI match external_id (UUID string).",
        )

    def handle(self, *args, **options):
        mid = (options["match_id"] or "").strip()
        if not mid:
            raise CommandError("match_id is required.")

        lc = LiveMatch.objects.filter(external_id=mid).update(scorecard_data=None)
        mc = Match.objects.filter(external_id=mid).update(scorecard_data=None)

        if lc == 0 and mc == 0:
            raise CommandError(f"No Match or LiveMatch row found for external_id={mid!r}.")

        self.stdout.write(
            self.style.SUCCESS(
                f"Cleared scorecard_data: LiveMatch rows={lc}, Match rows={mc} (id={mid})."
            )
        )
