import random

from django.core.management.base import BaseCommand

from matches.models import TeamFormStat, TeamHeadToHeadStat


class Command(BaseCommand):
    help = "Seed PSL team form (last 5) and head-to-head (last 10 / given played)."

    def handle(self, *args, **options):
        # PSL team codes used in frontend:
        # QTG, KRK, ISU, LHQ, MS, PSZ, HKS (new), PND (new)
        form_rows = [
            ("MS", 5, "LLLLL"),
            ("ISU", 5, "LLWLL"),
            ("QTG", 5, "LWWWW"),
            ("KRK", 5, "LLWWW"),
            ("PSZ", 5, "LLWWL"),
            ("LHQ", 5, "WWWWL"),
            ("HKS", 5, ""),  # N/A
            ("PND", 5, ""),  # N/A
        ]

        form_upserted = 0
        for team, last_n, form in form_rows:
            TeamFormStat.objects.update_or_create(
                team=team,
                last_n=last_n,
                defaults={"form": form},
            )
            form_upserted += 1

        # Head-to-head rows visible in user screenshots (Played assumed 10 unless said otherwise).
        provided_h2h = {
            ("MS", "ISU"): (10, 5, 5),
            ("QTG", "KRK"): (10, 6, 4),
            ("PSZ", "LHQ"): (10, 4, 6),
            ("LHQ", "KRK"): (10, 3, 7),
            ("ISU", "QTG"): (10, 5, 5),
        }

        teams_existing = ["QTG", "KRK", "ISU", "LHQ", "MS", "PSZ"]
        teams_new = ["HKS", "PND"]
        all_teams = teams_existing + teams_new

        def canon(a: str, b: str):
            a = a.upper()
            b = b.upper()
            if a < b:
                return a, b, False
            return b, a, True

        h2h_upserted = 0
        for i in range(len(all_teams)):
            for j in range(i + 1, len(all_teams)):
                a = all_teams[i]
                b = all_teams[j]

                # New teams have not played anyone yet.
                if a in teams_new or b in teams_new:
                    played, wa, wb = 0, 0, 0
                else:
                    key = (a, b)
                    if key in provided_h2h:
                        played, wa, wb = provided_h2h[key]
                    elif (b, a) in provided_h2h:
                        played, wb, wa = provided_h2h[(b, a)]
                    else:
                        played = 10
                        wa = random.randint(0, played)
                        wb = played - wa

                team_a, team_b, swapped = canon(a, b)
                if swapped:
                    wa, wb = wb, wa

                TeamHeadToHeadStat.objects.update_or_create(
                    team_a=team_a,
                    team_b=team_b,
                    scope=TeamHeadToHeadStat.SCOPE_OVERALL,
                    defaults={
                        "played": played,
                        "won_a": wa,
                        "won_b": wb,
                    },
                )
                h2h_upserted += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded/updated PSL form rows: {form_upserted}"))
        self.stdout.write(self.style.SUCCESS(f"Seeded/updated PSL h2h rows: {h2h_upserted}"))

