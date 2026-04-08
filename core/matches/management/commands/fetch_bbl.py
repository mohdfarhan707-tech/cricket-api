"""
Fetch and cache Big Bash League (or any CricAPI series) into our Matches DB.

Usage example (once you know the CricAPI series id for BBL 2025‑26):

  python manage.py fetch_bbl --series-id=<CRICAPI_SERIES_ID> --name="Big Bash League 2025-26" --with-scorecards

This will:
  - Create/Update a `Series` row with the given external_id and name.
  - Create/Update all `Match` rows from the series_info `matchList`.
  - Optionally fetch full scorecards for each match and cache them on the Match.
"""

import time
import requests

from django.core.management.base import BaseCommand, CommandError

from matches.models import Series, Match
from matches.scorecard_helpers import CRICAPI_KEY, fetch_scorecard, apply_scorecard_to_match
from matches.updater import _extract_scores_from_match, _fetch_match_score


class Command(BaseCommand):
  help = "Fetch BBL 2025-26 (or any CricAPI series) matches + scorecards into DB."

  def add_arguments(self, parser):
    parser.add_argument(
      "--series-id",
      type=str,
      required=True,
      help="CricAPI series/tournament id for BBL (from your CricAPI dashboard).",
    )
    parser.add_argument(
      "--name",
      type=str,
      default="Big Bash League 2025-26",
      help="Series name to store in DB (default: Big Bash League 2025-26).",
    )
    parser.add_argument(
      "--with-scorecards",
      action="store_true",
      help="If set, also fetch and cache full scorecards for each match (respects CricAPI limits).",
    )
    parser.add_argument(
      "--delay",
      type=float,
      default=1.6,
      help="Seconds to wait between scorecard API calls when --with-scorecards is used (default: 1.6).",
    )

  def handle(self, *args, **options):
    series_id = (options["series_id"] or "").strip()
    if not series_id:
      raise CommandError("You must provide --series-id (CricAPI tournament/series id).")

    series_name = (options["name"] or "").strip() or "Big Bash League 2025-26"
    with_scorecards = bool(options["with_scorecards"])
    delay = float(options["delay"] or 0)

    url = f"https://api.cricapi.com/v1/series_info?apikey={CRICAPI_KEY}&id={series_id}"
    self.stdout.write(f"Fetching CricAPI series_info for id={series_id} ...")
    try:
      resp = requests.get(url, timeout=12)
      root = resp.json() if resp.content else {}
    except Exception as e:
      raise CommandError(f"Failed to call CricAPI series_info: {e}")

    if not isinstance(root, dict):
      raise CommandError("Invalid response from CricAPI (not a dict).")
    if root.get("status") == "failure":
      reason = root.get("reason") or root.get("message") or "Unknown failure"
      raise CommandError(f"CricAPI series_info returned failure: {reason}")

    data = root.get("data") or root
    if not isinstance(data, dict) or not data:
      raise CommandError("CricAPI series_info contained no data payload.")

    info_name = (data.get("info", {}) or {}).get("name") or series_name
    series_obj, _ = Series.objects.update_or_create(
      external_id=series_id,
      defaults={"name": info_name},
    )
    self.stdout.write(self.style.SUCCESS(f"Series synced: {series_obj.name} ({series_obj.external_id})"))

    match_list = data.get("matchList") or []
    if not isinstance(match_list, list) or not match_list:
      self.stdout.write(self.style.WARNING("No matchList items found in series_info. Nothing to sync."))
      return

    created = 0
    updated = 0
    for m in match_list:
      if not isinstance(m, dict):
        continue
      match_id = m.get("id")
      if not match_id:
        continue

      team_home = (m.get("teams") or [None, None])[0]
      team_away = (m.get("teams") or [None, None])[1]
      home_score = None
      away_score = None

      # Try to use the same embedded-score extraction as the main updater.
      hs, as_ = _extract_scores_from_match(m)
      home_score = hs or home_score
      away_score = as_ or away_score

      status_text = (m.get("status") or "").lower()
      if (not home_score or not away_score) and ("live" in status_text or "completed" in status_text or "result" in status_text):
        t1, t2, t1s, t2s = _fetch_match_score(match_id, CRICAPI_KEY)
        if t1s or t2s:
          home_score = t1s or home_score
          away_score = t2s or away_score
        if t1 and t2:
          team_home = t1
          team_away = t2

      obj, was_created = Match.objects.update_or_create(
        external_id=match_id,
        defaults={
          "series": series_obj,
          "name": m.get("name") or "",
          "status": m.get("status", "Upcoming"),
          "team_home": team_home or "",
          "team_away": team_away or "",
          "home_score": home_score or "",
          "away_score": away_score or "",
        },
      )
      created += int(was_created)
      updated += int(not was_created)

    self.stdout.write(self.style.SUCCESS(f"Synced {len(match_list)} matches (created={created}, updated={updated})."))

    if not with_scorecards:
      return

    # Optional scorecard enrichment for all matches in this series.
    self.stdout.write("Fetching scorecards for series matches (this uses CricAPI daily quota)...")
    qs = Match.objects.filter(series=series_obj).order_by("id")
    total = qs.count()
    ok = 0
    skipped = 0
    for idx, match in enumerate(qs, 1):
      self.stdout.write(
        f"  [{idx}/{total}] {match.team_home} vs {match.team_away} ({match.external_id})... ",
        ending="",
      )
      scorecard = fetch_scorecard(match.external_id)
      if not scorecard:
        self.stdout.write(self.style.WARNING("no scorecard / failed"))
        skipped += 1
      else:
        apply_scorecard_to_match(match, scorecard)
        self.stdout.write(self.style.SUCCESS("OK"))
        ok += 1

      if delay and idx < total:
        time.sleep(delay)

    self.stdout.write(self.style.SUCCESS(f"Scorecards done. Cached={ok}, skipped/failed={skipped}."))

