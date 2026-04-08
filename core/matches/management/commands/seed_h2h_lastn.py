from django.core.management.base import BaseCommand

from matches.models import TeamHeadToHeadStat


class Command(BaseCommand):
    help = "Seed manually curated IPL head-to-head last-N rows (played + wins)."

    def handle(self, *args, **options):
        # Provided by user (Team1, Team2, Matches, Team1_Wins, Team2_Wins)
        rows = [
            ("CSK", "MI", 10, 7, 3),
            ("CSK", "RCB", 10, 7, 3),
            ("CSK", "KKR", 10, 6, 4),
            ("CSK", "SRH", 10, 6, 4),
            ("CSK", "RR", 10, 4, 6),
            ("CSK", "DC", 10, 7, 3),
            ("CSK", "PBKS", 10, 5, 5),

            ("MI", "RCB", 10, 6, 4),
            ("MI", "KKR", 10, 9, 1),
            ("MI", "SRH", 10, 6, 4),
            ("MI", "RR", 10, 6, 4),
            ("MI", "DC", 10, 6, 4),
            ("MI", "PBKS", 10, 6, 4),

            ("RCB", "KKR", 10, 3, 7),
            ("RCB", "SRH", 10, 4, 6),
            ("RCB", "RR", 10, 6, 4),
            ("RCB", "DC", 10, 6, 4),
            ("RCB", "PBKS", 10, 5, 5),

            ("KKR", "SRH", 10, 6, 4),
            ("KKR", "RR", 10, 6, 4),
            ("KKR", "DC", 10, 5, 5),
            ("KKR", "PBKS", 10, 6, 4),

            ("SRH", "RR", 10, 5, 5),
            ("SRH", "DC", 10, 6, 4),
            ("SRH", "PBKS", 10, 6, 4),

            ("RR", "DC", 10, 6, 4),
            ("RR", "PBKS", 10, 6, 4),

            ("DC", "PBKS", 10, 5, 5),

            # Shorter sample sizes (not always last 10 available)
            ("PBKS", "GT", 5, 2, 3),

            ("GT", "MI", 10, 5, 5),
            ("GT", "CSK", 5, 2, 3),
            ("GT", "RCB", 5, 2, 3),

            ("LSG", "CSK", 6, 3, 2),
            ("LSG", "RCB", 6, 2, 4),
            ("LSG", "MI", 6, 5, 1),

            # Missing combos provided later
            ("GT", "KKR", 3, 2, 1),
            ("GT", "SRH", 4, 3, 1),
            ("GT", "RR", 5, 4, 1),
            ("GT", "DC", 5, 3, 2),
            ("GT", "PBKS", 5, 3, 2),

            ("LSG", "KKR", 5, 3, 2),
            ("LSG", "SRH", 4, 3, 1),
            ("LSG", "RR", 4, 1, 3),
            ("LSG", "DC", 5, 4, 1),
            ("LSG", "PBKS", 4, 3, 1),

            ("GT", "LSG", 4, 2, 2),
        ]

        upserted = 0
        for a, b, played, won_a, won_b in rows:
            a = (a or "").strip().upper()
            b = (b or "").strip().upper()
            if not a or not b or a == b:
                continue

            # Canonicalize ordering to avoid duplicate unique constraint conflicts.
            if a < b:
                team_a, team_b = a, b
                wa, wb = won_a, won_b
            else:
                team_a, team_b = b, a
                wa, wb = won_b, won_a

            TeamHeadToHeadStat.objects.update_or_create(
                team_a=team_a,
                team_b=team_b,
                scope=TeamHeadToHeadStat.SCOPE_OVERALL,
                defaults={
                    "played": int(played or 0),
                    "won_a": int(wa or 0),
                    "won_b": int(wb or 0),
                    # Other fields not provided in this dataset -> keep 0
                },
            )
            upserted += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded/updated {upserted} head-to-head rows."))

