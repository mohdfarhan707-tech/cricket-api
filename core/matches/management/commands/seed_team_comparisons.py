from django.core.management.base import BaseCommand

from matches.models import TeamComparisonStat


class Command(BaseCommand):
    help = "Seed manually curated Team Comparison stats (IPL last 10)."

    def handle(self, *args, **options):
        rows = [
            # RCB vs SRH
            dict(
                team_a="RCB",
                team_b="SRH",
                scope=TeamComparisonStat.SCOPE_OVERALL,
                last_n=10,
                matches_played_a=10,
                matches_played_b=10,
                win_pct_a=80,
                win_pct_b=50,
                avg_score_a=172,
                avg_score_b=188,
                highest_score_a=230,
                highest_score_b=278,
                lowest_score_a=95,
                lowest_score_b=120,
            ),
            # MI vs KKR
            dict(
                team_a="MI",
                team_b="KKR",
                scope=TeamComparisonStat.SCOPE_OVERALL,
                last_n=10,
                matches_played_a=10,
                matches_played_b=10,
                win_pct_a=70,
                win_pct_b=40,
                avg_score_a=187,
                avg_score_b=166,
                highest_score_a=228,
                highest_score_b=234,
                lowest_score_a=146,
                lowest_score_b=95,
            ),
            # RR vs CSK
            dict(
                team_a="RR",
                team_b="CSK",
                scope=TeamComparisonStat.SCOPE_OVERALL,
                last_n=10,
                matches_played_a=10,
                matches_played_b=10,
                win_pct_a=20,
                win_pct_b=30,
                avg_score_a=182,
                avg_score_b=180,
                highest_score_a=212,
                highest_score_b=230,
                lowest_score_a=117,
                lowest_score_b=103,
            ),
            # PBKS vs GT
            dict(
                team_a="PBKS",
                team_b="GT",
                scope=TeamComparisonStat.SCOPE_OVERALL,
                last_n=10,
                matches_played_a=10,
                matches_played_b=10,
                win_pct_a=60,
                win_pct_b=50,
                avg_score_a=178,
                avg_score_b=192,
                highest_score_a=236,
                highest_score_b=224,
                lowest_score_a=98,
                lowest_score_b=147,
            ),
            # LSG vs DC
            dict(
                team_a="LSG",
                team_b="DC",
                scope=TeamComparisonStat.SCOPE_OVERALL,
                last_n=10,
                matches_played_a=10,
                matches_played_b=10,
                win_pct_a=40,
                win_pct_b=40,
                avg_score_a=195,
                avg_score_b=179,
                highest_score_a=238,
                highest_score_b=208,
                lowest_score_a=159,
                lowest_score_b=121,
            ),
        ]

        upserted = 0
        for r in rows:
            obj, _created = TeamComparisonStat.objects.update_or_create(
                team_a=r["team_a"],
                team_b=r["team_b"],
                scope=r["scope"],
                defaults=r,
            )
            upserted += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded/updated {upserted} team comparison rows."))

