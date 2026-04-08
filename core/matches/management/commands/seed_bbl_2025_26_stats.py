from django.core.management.base import BaseCommand

from matches.models import SeriesStatsCache


class Command(BaseCommand):
    help = "Seed Big Bash League 2025/26 stats into SeriesStatsCache."

    def handle(self, *args, **options):
        # Values sourced from ESPNcricinfo:
        # https://www.espncricinfo.com/series/big-bash-league-2025-26-1490534/stats
        data = {
            "topRunScorers": [
                {"name": "Finn Allen", "teamShort": "PS", "runs": 466, "innings": 11, "average": 42.36},
                {"name": "David Warner", "teamShort": "ST", "runs": 433, "innings": 8, "average": 86.60},
                {"name": "Sam Harper", "teamShort": "MS", "runs": 381, "innings": 10, "average": 54.42},
            ],
            "topWicketTakers": [
                {"name": "Haris Rauf", "teamShort": "MS", "wickets": 20, "innings": 11, "average": 16.75},
                {"name": "Jack Edwards", "teamShort": "SS", "wickets": 19, "innings": 12, "average": 18.47},
                {"name": "Gurinder Sandhu", "teamShort": "MR", "wickets": 18, "innings": 9, "average": 18.05},
            ],
            "bestBattingStrikeRates": [
                {"name": "Mitchell Owen", "teamShort": "HH", "strikeRate": 195.29, "innings": 11, "average": 15.09},
                {"name": "Tom Curran", "teamShort": "MS", "strikeRate": 187.50, "innings": 5, "average": 20.00},
                {"name": "Finn Allen", "teamShort": "PS", "strikeRate": 184.18, "innings": 11, "average": 42.36},
            ],
            "bestBowlingEconomy": [
                {"name": "Tabraiz Shamsi", "teamShort": "AS", "economy": 5.66, "innings": 4, "average": 10.50},
                {"name": "Ben Manenti", "teamShort": "SS", "economy": 5.94, "innings": 7, "average": 31.66},
                {"name": "Joel Davies", "teamShort": "SS", "economy": 6.23, "innings": 11, "average": 13.35},
            ],
            "smartStatsTotalImpact": [
                {"name": "Cooper Connolly", "teamShort": "PS", "impactPts": 586.01, "runs": 209, "wickets": 15},
                {"name": "Finn Allen", "teamShort": "PS", "impactPts": 562.48, "runs": 466, "wickets": None},
                {"name": "Aaron Hardie", "teamShort": "PS", "impactPts": 547.55, "runs": 339, "wickets": 12},
            ],
        }

        row, created = SeriesStatsCache.objects.update_or_create(
            series_external_id="1490534",
            defaults={"series_name": "Big Bash League 2025/26", "data": data},
        )

        msg = "created" if created else "updated"
        self.stdout.write(self.style.SUCCESS(f"BBL stats {msg} for series_external_id=1490534"))

