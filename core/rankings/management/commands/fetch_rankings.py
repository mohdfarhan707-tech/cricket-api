from django.core.management.base import BaseCommand

from rankings.models import TeamRanking, BatterRanking, BowlerRanking, AllRounderRanking
from rankings.rapidapi_client import fetch_rankings


def _safe_int(v, default=0):
    try:
        if default is None and v is None:
            return None
        return int(v)
    except Exception:
        return default


def _extract_list(payload: dict) -> list[dict]:
    """Normalize RapidAPI / Cricbuzz-style ranking payloads to a list of row dicts."""
    if not payload or not isinstance(payload, dict):
        return []

    def from_obj(obj) -> list[dict]:
        if isinstance(obj, list) and obj and isinstance(obj[0], dict):
            return obj
        return []

    for key in ("rank", "rankings", "data", "list", "rankList", "playerList", "teamList", "statsList"):
        val = payload.get(key)
        if isinstance(val, list) and val:
            if isinstance(val[0], dict):
                return val

    data = payload.get("data")
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data
    if isinstance(data, dict):
        for key in ("rank", "rankings", "list", "rankList", "playerList", "teamList"):
            val = data.get(key)
            if isinstance(val, list) and val and isinstance(val[0], dict):
                return val

    # Some APIs nest under typeRankings etc.
    for _k, v in payload.items():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            if any(x in _k.lower() for x in ("rank", "player", "team", "list")):
                return v

    return from_obj(payload.get("body"))


class Command(BaseCommand):
    help = "Fetch Cricbuzz rankings via RapidAPI and cache in DB. Set RAPIDAPI_KEY in environment."

    def add_arguments(self, parser):
        parser.add_argument(
            "--kind",
            type=str,
            default="teams",
            help="teams | batsmen | bowlers | allrounders",
        )
        parser.add_argument(
            "--format",
            type=str,
            default="t20",
            help="t20 | odi | test",
        )

    def handle(self, *args, **options):
        kind = (options["kind"] or "").strip().lower()
        fmt = (options["format"] or "").strip().lower()

        payload = fetch_rankings(kind, fmt)
        if not payload:
            self.stderr.write(
                self.style.ERROR(
                    "Failed to fetch rankings (check RAPIDAPI_KEY / network / RapidAPI subscription)."
                )
            )
            return

        rows = _extract_list(payload)
        if not rows:
            self.stderr.write(
                self.style.WARNING(
                    f"Fetched payload but could not find rankings list. Top-level keys: {list(payload.keys())[:12]}"
                )
            )
            return

        if kind == "teams":
            for r in rows:
                team = (r.get("team") or r.get("name") or r.get("teamName") or "").strip()
                code = (r.get("teamId") or r.get("shortName") or r.get("teamCode") or "").strip()
                rank = _safe_int(r.get("rank") or r.get("position") or 0)
                rating = _safe_int(r.get("rating") or r.get("points") or r.get("value") or 0)
                if not team or rank <= 0:
                    continue
                TeamRanking.objects.update_or_create(
                    team_name=team,
                    format_type=fmt,
                    defaults={"team_code": str(code)[:10], "rank": rank, "rating": rating},
                )
        elif kind == "batsmen":
            for r in rows:
                name = (r.get("name") or r.get("player") or r.get("playerName") or "").strip()
                country = (r.get("country") or r.get("team") or r.get("countryName") or "").strip()
                rank = _safe_int(r.get("rank") or r.get("position") or 0)
                rating = _safe_int(r.get("rating") or r.get("value") or 0)
                best = r.get("bestRating") or r.get("careerBest") or None
                if not name or rank <= 0:
                    continue
                BatterRanking.objects.update_or_create(
                    player_name=name,
                    format_type=fmt,
                    defaults={
                        "country": country[:100],
                        "rank": rank,
                        "rating": rating,
                        "career_best_rating": _safe_int(best, None) if best is not None else None,
                    },
                )
        elif kind == "bowlers":
            for r in rows:
                name = (r.get("name") or r.get("player") or r.get("playerName") or "").strip()
                country = (r.get("country") or r.get("team") or r.get("countryName") or "").strip()
                rank = _safe_int(r.get("rank") or r.get("position") or 0)
                rating = _safe_int(r.get("rating") or r.get("value") or 0)
                best = r.get("bestRating") or r.get("careerBest") or None
                if not name or rank <= 0:
                    continue
                BowlerRanking.objects.update_or_create(
                    player_name=name,
                    format_type=fmt,
                    defaults={
                        "country": country[:100],
                        "rank": rank,
                        "rating": rating,
                        "career_best_rating": _safe_int(best, None) if best is not None else None,
                    },
                )
        elif kind == "allrounders":
            for r in rows:
                name = (r.get("name") or r.get("player") or r.get("playerName") or "").strip()
                country = (r.get("country") or r.get("team") or r.get("countryName") or "").strip()
                rank = _safe_int(r.get("rank") or r.get("position") or 0)
                rating = _safe_int(r.get("rating") or r.get("value") or 0)
                best = r.get("bestRating") or r.get("careerBest") or None
                if not name or rank <= 0:
                    continue
                AllRounderRanking.objects.update_or_create(
                    player_name=name,
                    format_type=fmt,
                    defaults={
                        "country": country[:100],
                        "rank": rank,
                        "rating": rating,
                        "career_best_rating": _safe_int(best, None) if best is not None else None,
                    },
                )
        else:
            self.stderr.write(self.style.ERROR("Unknown kind. Use teams|batsmen|bowlers|allrounders"))
            return

        self.stdout.write(self.style.SUCCESS(f"Cached {kind} {fmt} rankings into DB ({len(rows)} rows in API response)."))
