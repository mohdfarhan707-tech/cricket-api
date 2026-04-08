"""
Fetch and cache Big Bash League 2025/26 matches (with scores) into the main Matches DB
using the Cricbuzz RapidAPI series endpoint.

This does NOT rely on CricAPI at all – it reads from:
  https://cricbuzz-cricket.p.rapidapi.com/series/v1/10289

Usage:
  python manage.py fetch_bbl_matches
  python manage.py fetch_bbl_matches --with-scorecards

After running this, the BBL 2025/26 series and all its matches (with summary scores)
will appear in the `/api/matches/` payload, so the frontend Results view can show
them like other finished series. With --with-scorecards, full scorecards are also
fetched and cached from Cricbuzz mcenter (/mcenter/v1/{matchId}/hscard).
"""

import time
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from django.core.management.base import BaseCommand

from upcoming.rapidapi_client import fetch_series_raw, fetch_mcenter_raw
from upcoming.cricbuzz_scorecard import transform_cricbuzz_to_scorecard
from matches.models import Series, Match
from matches.scorecard_helpers import apply_scorecard_to_match


def _safe_datetime(ms: Any) -> datetime | None:
    try:
        return datetime.fromtimestamp(int(ms) / 1000.0, tz=timezone.utc)
    except Exception:
        return None


def _format_innings_score(score: Dict[str, Any] | None) -> str:
    """
    Cricbuzz matchScore -> teamScore -> inngs1 looks like:
      { "runs": 180, "wickets": 6, "overs": "20.0" }
    We format "180/6" (ignoring overs for now, since our Match.home_score / away_score
    fields are simple strings like '180/6'.
    """
    if not isinstance(score, dict):
        return ""
    inngs = score.get("inngs1") or score.get("inngs2") or {}
    if not isinstance(inngs, dict):
        return ""
    runs = inngs.get("runs")
    wkts = inngs.get("wickets")
    if runs is None:
        return ""
    s = str(runs)
    if wkts is not None:
        s += f"/{wkts}"
    return s


def _extract_team_scores(match_block: Dict[str, Any]) -> Tuple[str, str]:
    """
    From a single match entry in series/v1/<id> -> matchDetailsMap -> match[],
    try to extract basic home/away scores using matchScore.team1Score / team2Score.
    """
    ms = match_block.get("matchScore") or {}
    if not isinstance(ms, dict):
        return "", ""
    team1_score = _format_innings_score(ms.get("team1Score"))
    team2_score = _format_innings_score(ms.get("team2Score"))
    return team1_score, team2_score


class Command(BaseCommand):
    help = "Fetch Big Bash League 2025/26 matches + summary scores into matches.Match via Cricbuzz series API."

    def add_arguments(self, parser):
        parser.add_argument(
            "--series-id",
            type=str,
            default="10289",
            help="Cricbuzz series id (default: 10289 for BBL 2025/26).",
        )
        parser.add_argument(
            "--series-name",
            type=str,
            default="Big Bash League 2025/26",
            help="Fallback series name for DB if API omits it.",
        )
        parser.add_argument(
            "--with-scorecards",
            action="store_true",
            help="Also fetch full scorecards from Cricbuzz mcenter and cache on each match.",
        )
        parser.add_argument(
            "--scorecard-delay",
            type=float,
            default=0.5,
            help="Seconds between scorecard API calls (default 0.5).",
        )
        parser.add_argument(
            "--force-scorecards",
            action="store_true",
            help="Re-fetch scorecards even when cached (overwrites empty or stale cache).",
        )

    def handle(self, *args, **options):
        series_id = (options["series_id"] or "").strip()
        series_name_fallback = (options["series_name"] or "").strip() or "Big Bash League 2025/26"

        self.stdout.write(f"Fetching Cricbuzz series data for id={series_id} ...")
        data = fetch_series_raw(series_id)
        if not data:
            self.stdout.write(self.style.ERROR("Failed to fetch series data from Cricbuzz."))
            return

        # Top-level name lives under seriesName for this endpoint.
        series_name = (
            (data.get("seriesName") or data.get("name") or series_name_fallback)
            if isinstance(data, dict)
            else series_name_fallback
        )

        series_obj, _ = Series.objects.update_or_create(
            external_id=f"cricbuzz-{series_id}",
            defaults={"name": series_name},
        )
        self.stdout.write(self.style.SUCCESS(f"Series synced: {series_obj.name} ({series_obj.external_id})"))

        # Series endpoint layout:
        #  matchDetails[] -> matchDetailsMap{} -> match[] -> matchInfo + matchScore
        details = data.get("matchDetails") or []
        if not isinstance(details, list) or not details:
            self.stdout.write(self.style.WARNING("No matchDetails found in series data."))
            return

        created = 0
        updated = 0
        match_objs = []

        for md in details:
            if not isinstance(md, dict):
                continue
            mdm = md.get("matchDetailsMap") or {}
            # matchDetailsMap can have keys like "Group A", "" etc; each value may have "match" array
            matches_in_mdm = []
            if isinstance(mdm.get("match"), list):
                matches_in_mdm = mdm["match"]
            else:
                for group_val in (mdm.values() if isinstance(mdm, dict) else []):
                    if isinstance(group_val, dict) and isinstance(group_val.get("match"), list):
                        matches_in_mdm.extend(group_val["match"])
            for m in matches_in_mdm:
                if not isinstance(m, dict):
                    continue
                info = m.get("matchInfo") or {}
                if not isinstance(info, dict):
                    continue

                match_id = str(info.get("matchId") or info.get("id") or "").strip()
                if not match_id:
                    continue

                team1 = ((info.get("team1") or {}) or {}).get("teamName") or ""
                team2 = ((info.get("team2") or {}) or {}).get("teamName") or ""
                status = info.get("status") or ""

                home_score, away_score = _extract_team_scores(m)

                # Use Cricbuzz matchId as external_id; keep any existing records updated.
                obj, was_created = Match.objects.update_or_create(
                    external_id=match_id,
                    defaults={
                        "series": series_obj,
                        "name": info.get("matchDesc") or info.get("matchType") or "",
                        "status": status,
                        "team_home": team1,
                        "team_away": team2,
                        "home_score": home_score,
                        "away_score": away_score,
                    },
                )
                created += int(was_created)
                updated += int(not was_created)

                # Ensure match date is available for Match Centre "Date" row.
                # Cricbuzz series payload provides `startDate` epoch-ms in matchInfo.
                start_dt = _safe_datetime(info.get("startDate") or info.get("startTime"))
                if start_dt:
                    sc = obj.scorecard_data if isinstance(obj.scorecard_data, dict) else {}
                    if not sc.get("date"):
                        sc = dict(sc)
                        sc["date"] = start_dt.date().isoformat()
                        obj.scorecard_data = sc
                        obj.save(update_fields=["scorecard_data"])

                match_objs.append(obj)

        self.stdout.write(
            self.style.SUCCESS(
                f"Synced BBL matches from Cricbuzz series {series_id}: created={created}, updated={updated}."
            )
        )

        if options.get("with_scorecards") and match_objs:
            delay = max(0.2, float(options.get("scorecard_delay") or 0.5))
            force = options.get("force_scorecards", False)
            self.stdout.write("Fetching scorecards from Cricbuzz mcenter...")
            scored = 0
            for obj in match_objs:
                # Skip only if we have valid cached data (non-empty score/scorecard) and not forcing
                if not force and obj.scorecard_data:
                    sc = obj.scorecard_data
                    if isinstance(sc, dict) and (sc.get("score") or sc.get("scorecard")):
                        continue
                raw = fetch_mcenter_raw(obj.external_id)
                time.sleep(delay)
                if raw:
                    scorecard = transform_cricbuzz_to_scorecard(raw, obj.external_id)
                    if scorecard and (scorecard.get("score") or scorecard.get("scorecard")):
                        apply_scorecard_to_match(obj, scorecard)
                        scored += 1
                        self.stdout.write(f"  Cached scorecard for {obj.external_id}")
            self.stdout.write(self.style.SUCCESS(f"Cached {scored} scorecard(s)."))

