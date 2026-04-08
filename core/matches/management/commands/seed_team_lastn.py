from django.core.management.base import BaseCommand

from matches.models import TeamLastNStat


class Command(BaseCommand):
    help = "Seed manually curated Team Last-N stats (IPL last 10 overall)."

    def handle(self, *args, **options):
        rows = [
            # Extracted from your screenshots (Team Comparison -> vs all teams -> Overall)
            dict(team="RCB", scope=TeamLastNStat.SCOPE_OVERALL, last_n=10, matches_played=10, win_pct=80, avg_score=172, highest_score=230, lowest_score=95),
            dict(team="SRH", scope=TeamLastNStat.SCOPE_OVERALL, last_n=10, matches_played=10, win_pct=50, avg_score=188, highest_score=278, lowest_score=120),
            dict(team="MI", scope=TeamLastNStat.SCOPE_OVERALL, last_n=10, matches_played=10, win_pct=70, avg_score=187, highest_score=228, lowest_score=146),
            dict(team="KKR", scope=TeamLastNStat.SCOPE_OVERALL, last_n=10, matches_played=10, win_pct=40, avg_score=166, highest_score=234, lowest_score=95),
            dict(team="RR", scope=TeamLastNStat.SCOPE_OVERALL, last_n=10, matches_played=10, win_pct=20, avg_score=182, highest_score=212, lowest_score=117),
            dict(team="CSK", scope=TeamLastNStat.SCOPE_OVERALL, last_n=10, matches_played=10, win_pct=30, avg_score=180, highest_score=230, lowest_score=103),
            dict(team="PBKS", scope=TeamLastNStat.SCOPE_OVERALL, last_n=10, matches_played=10, win_pct=60, avg_score=178, highest_score=236, lowest_score=98),
            dict(team="GT", scope=TeamLastNStat.SCOPE_OVERALL, last_n=10, matches_played=10, win_pct=50, avg_score=192, highest_score=224, lowest_score=147),
            dict(team="LSG", scope=TeamLastNStat.SCOPE_OVERALL, last_n=10, matches_played=10, win_pct=40, avg_score=195, highest_score=238, lowest_score=159),
            dict(team="DC", scope=TeamLastNStat.SCOPE_OVERALL, last_n=10, matches_played=10, win_pct=40, avg_score=179, highest_score=208, lowest_score=121),
        ]

        upserted = 0
        for r in rows:
            TeamLastNStat.objects.update_or_create(
                team=r["team"],
                scope=r["scope"],
                defaults=r,
            )
            upserted += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded/updated {upserted} team last-N rows."))

