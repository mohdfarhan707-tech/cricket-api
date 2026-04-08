from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = (
        "Fetch all ICC-style rankings (teams, batsmen, bowlers, allrounders) for T20, ODI, and Test. "
        "Requires RAPIDAPI_KEY."
    )

    def handle(self, *args, **options):
        kinds = ("teams", "batsmen", "bowlers", "allrounders")
        formats = ("t20", "odi", "test")
        for fmt in formats:
            for kind in kinds:
                self.stdout.write(f"Fetching {kind} / {fmt}…")
                call_command("fetch_rankings", kind=kind, format=fmt)
        self.stdout.write(self.style.SUCCESS("fetch_all_rankings finished."))
