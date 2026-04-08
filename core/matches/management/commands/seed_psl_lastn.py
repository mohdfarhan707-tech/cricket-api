from django.core.management.base import BaseCommand

from matches.models import TeamLastNStat


class Command(BaseCommand):
    help = "Seed manually curated PSL team last-10 stats (overall)."

    def handle(self, *args, **options):
        # From user screenshots:
        # QTG vs KRK: (70%,169,263,90) vs (50%,169,237,128)
        # MS  vs ISU: (10%,157,234,89)  vs (40%,161,251,107)
        # PSZ vs LHQ: (40%,149,227,110) vs (70%,182,209,129)
        # Two new teams not provided -> NIL
        rows = [
            dict(team="QTG", scope=TeamLastNStat.SCOPE_OVERALL, last_n=10, matches_played=10, win_pct=70, avg_score=169, highest_score=263, lowest_score=90),
            dict(team="KRK", scope=TeamLastNStat.SCOPE_OVERALL, last_n=10, matches_played=10, win_pct=50, avg_score=169, highest_score=237, lowest_score=128),
            dict(team="MS", scope=TeamLastNStat.SCOPE_OVERALL, last_n=10, matches_played=10, win_pct=10, avg_score=157, highest_score=234, lowest_score=89),
            dict(team="ISU", scope=TeamLastNStat.SCOPE_OVERALL, last_n=10, matches_played=10, win_pct=40, avg_score=161, highest_score=251, lowest_score=107),
            dict(team="PSZ", scope=TeamLastNStat.SCOPE_OVERALL, last_n=10, matches_played=10, win_pct=40, avg_score=149, highest_score=227, lowest_score=110),
            dict(team="LHQ", scope=TeamLastNStat.SCOPE_OVERALL, last_n=10, matches_played=10, win_pct=70, avg_score=182, highest_score=209, lowest_score=129),
            # New teams (nil)
            dict(team="HKS", scope=TeamLastNStat.SCOPE_OVERALL, last_n=10, matches_played=0, win_pct=0, avg_score=0, highest_score=0, lowest_score=0),
            dict(team="PND", scope=TeamLastNStat.SCOPE_OVERALL, last_n=10, matches_played=0, win_pct=0, avg_score=0, highest_score=0, lowest_score=0),
        ]

        upserted = 0
        for r in rows:
            TeamLastNStat.objects.update_or_create(
                team=r["team"],
                scope=r["scope"],
                defaults=r,
            )
            upserted += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded/updated {upserted} PSL last-10 rows."))

