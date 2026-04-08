from django.core.management.base import BaseCommand
from django.utils import timezone

from upcoming.models import LeagueStandingsCache
from upcoming.points_table_builder import (
    SERIES_ID_IPL,
    SERIES_ID_PSL,
    build_standings_rows,
    series_name_from_payload,
)
from upcoming.rapidapi_client import fetch_series_raw


class Command(BaseCommand):
    help = "Refresh IPL/PSL points tables from Cricbuzz series API (RapidAPI key in rapidapi_client)."

    def handle(self, *args, **options):
        now = timezone.now()
        for league, series_id in (("ipl", SERIES_ID_IPL), ("psl", SERIES_ID_PSL)):
            raw = fetch_series_raw(series_id)
            if not raw:
                self.stdout.write(self.style.WARNING(f"No data for {league} (series {series_id})"))
                continue
            rows = build_standings_rows(raw)
            label = series_name_from_payload(raw)
            payload = {
                "league": league,
                "series_id": series_id,
                "series_name": label,
                "rows": rows,
                "fetched_at": now.isoformat(),
            }
            LeagueStandingsCache.objects.update_or_create(
                league=league,
                defaults={"series_id": series_id, "data": payload},
            )
            self.stdout.write(self.style.SUCCESS(f"{league.upper()}: cached {len(rows)} teams ({label or series_id})"))
