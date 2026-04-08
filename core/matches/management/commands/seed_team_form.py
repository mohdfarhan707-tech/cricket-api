from django.core.management.base import BaseCommand

from matches.models import TeamFormStat


class Command(BaseCommand):
    help = "Seed manually curated IPL team form (last 5 matches)."

    def handle(self, *args, **options):
        # Extracted from user screenshots (Team Form - Last 5 matches)
        rows = [
            ("RCB", 5, "WWWLW"),
            ("SRH", 5, "WWWLW"),
            ("MI", 5, "LWLWL"),
            ("KKR", 5, "LLWWL"),
            ("RR", 5, "WLLLW"),
            ("CSK", 5, "WLWLL"),
            ("PBKS", 5, "LWLWL"),
            ("GT", 5, "LLLWW"),
            ("LSG", 5, "LWLLL"),
            ("DC", 5, "WLLLL"),
        ]

        upserted = 0
        for team, last_n, form in rows:
            TeamFormStat.objects.update_or_create(
                team=team,
                last_n=last_n,
                defaults={"form": form},
            )
            upserted += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded/updated {upserted} team form rows."))

