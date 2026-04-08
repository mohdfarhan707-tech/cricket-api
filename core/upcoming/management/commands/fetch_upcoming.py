from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from upcoming.models import UpcomingMatch
from upcoming.rapidapi_client import fetch_series_raw, fetch_upcoming_raw

# When Cricbuzz omits seriesName on scheduled rows, keep league filters working (frontend + API).
CRICBUZZ_SERIES_DEFAULT_NAME = {
    "9241": "Indian Premier League 2026",
    "11537": "Pakistan Super League 2026",
    "10289": "Big Bash League 2025-26",
    "11671": "Legends League Cricket 2026",
}


class Command(BaseCommand):
    help = "Fetch upcoming matches from RapidAPI Cricbuzz and cache in DB (UTC times)."

    def _start_dt_from_cricbuzz(self, raw) -> datetime | None:
        if raw is None:
            return None
        try:
            ts = int(raw)
        except (TypeError, ValueError):
            return None
        # Cricbuzz usually uses ms since epoch (13 digits); some payloads use seconds.
        if ts < 10**11:
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        return datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc)

    def _parse_matchinfo(self, m: dict) -> dict | None:
        match_id = str(m.get("matchId") or m.get("id") or "")
        if not match_id:
            return None

        start_raw = m.get("startDate") or m.get("startTime")
        start_dt = self._start_dt_from_cricbuzz(start_raw)
        if not start_dt:
            return None

        team_home = (m.get("team1", {}) or {}).get("teamName") or ""
        team_away = (m.get("team2", {}) or {}).get("teamName") or ""
        series_name = (m.get("seriesName") or m.get("series") or "") or ""
        venue = (m.get("venueInfo", {}) or {}).get("ground") or ""
        status = m.get("status") or ""
        return {
            "match_id": match_id,
            "start_dt": start_dt,
            "team_home": team_home,
            "team_away": team_away,
            "series_name": series_name,
            "venue": venue,
            "status": status,
        }

    def _resolve_series_name(self, raw: str, match_id: str, series_id: str | None) -> str:
        """Never downgrade to blank: use API text, series default, or previous DB row."""
        sn = (raw or "").strip()
        if sn:
            return sn
        if series_id and series_id in CRICBUZZ_SERIES_DEFAULT_NAME:
            return CRICBUZZ_SERIES_DEFAULT_NAME[series_id]
        prev = UpcomingMatch.objects.filter(external_id=match_id).first()
        return (prev.series_name or "").strip() if prev else ""

    def _iter_upcoming_endpoint(self, data: dict):
        # matches/v1/upcoming -> typeMatches -> seriesMatches -> seriesAdWrapper -> matches -> matchInfo
        for tm in (data.get("typeMatches") or []):
            for sm in tm.get("seriesMatches", []):
                wrapper = sm.get("seriesAdWrapper") or {}
                for match in wrapper.get("matches", []):
                    m = match.get("matchInfo") or {}
                    if isinstance(m, dict) and m:
                        yield m

    def _iter_series_endpoint(self, data: dict):
        # series/v1/<id> -> matchDetails -> matchDetailsMap -> match[] -> matchInfo
        for md in (data.get("matchDetails") or []):
            mdm = (md.get("matchDetailsMap") or {})
            for match in (mdm.get("match") or []):
                m = match.get("matchInfo") or {}
                if isinstance(m, dict) and m:
                    yield m

    def handle(self, *args, **options):
        created = 0
        now = datetime.now(timezone.utc)

        # 1) Global upcoming endpoint
        data = fetch_upcoming_raw()
        if data:
            for m in self._iter_upcoming_endpoint(data):
                parsed = self._parse_matchinfo(m)
                if not parsed:
                    continue
                if parsed["start_dt"] <= now:
                    continue
                raw_series = parsed["series_name"] or (m.get("seriesName") or "")
                cz_sid = m.get("seriesId")
                sid_key = str(cz_sid).strip() if cz_sid is not None and str(cz_sid).strip() else None
                series_name = self._resolve_series_name(raw_series, parsed["match_id"], sid_key)
                UpcomingMatch.objects.update_or_create(
                    external_id=parsed["match_id"],
                    defaults={
                        "team_home": parsed["team_home"],
                        "team_away": parsed["team_away"],
                        "series_name": series_name,
                        "venue": parsed["venue"],
                        "start_time_utc": parsed["start_dt"],
                        "status": parsed["status"],
                    },
                )
                created += 1

        # 2) Specific series: LLC 2026, PSL 2026, IPL 2026, BBL 2025/26 (Cricbuzz series id 10289)
        for sid in ["11671", "11537", "9241", "10289"]:
            sdata = fetch_series_raw(sid)
            if not sdata:
                continue
            for m in self._iter_series_endpoint(sdata):
                parsed = self._parse_matchinfo(m)
                if not parsed:
                    continue
                # Only cache future fixtures in this table; allow any non-finished state
                # (Cricbuzz may use labels other than "upcoming" for scheduled games).
                if parsed["start_dt"] <= now:
                    continue
                state = (m.get("state") or "").lower()
                if state in ("complete", "completed", "result", "abandoned"):
                    continue
                raw_series = parsed["series_name"] or (m.get("seriesName") or "")
                series_name = self._resolve_series_name(raw_series, parsed["match_id"], sid)
                UpcomingMatch.objects.update_or_create(
                    external_id=parsed["match_id"],
                    defaults={
                        "team_home": parsed["team_home"],
                        "team_away": parsed["team_away"],
                        "series_name": series_name,
                        "venue": parsed["venue"],
                        "start_time_utc": parsed["start_dt"],
                        "status": parsed["status"],
                    },
                )
                created += 1

        # Also cleanup any old upcoming matches that are now in the past
        UpcomingMatch.objects.filter(start_time_utc__lte=now).delete()

        self.stdout.write(self.style.SUCCESS(f"Cached {created} upcoming matches."))

