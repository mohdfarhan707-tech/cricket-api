from django.core.management.base import BaseCommand
from django.utils import timezone

from news.models import NewsItem
from news.rss_fetcher import DEFAULT_FEEDS, fetch_rss_items


class Command(BaseCommand):
    help = "Fetch cricket news from ESPNcricinfo RSS and cache in DB."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50, help="Max items per feed to store.")

    def handle(self, *args, **options):
        limit = options["limit"]
        created = 0
        updated = 0
        for feed in DEFAULT_FEEDS:
            try:
                items = fetch_rss_items(feed)[:limit]
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed feed {feed}: {e}"))
                continue

            for it in items:
                if not it.get("link") or not it.get("title"):
                    continue
                obj, was_created = NewsItem.objects.update_or_create(
                    link=it["link"],
                    defaults={
                        "source": "ESPNcricinfo",
                        "title": it.get("title", "")[:500],
                        "summary": it.get("summary", ""),
                        "published_at": it.get("published_at") or timezone.now(),
                        "image_url": it.get("image_url", ""),
                    },
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(f"Done. created={created} updated={updated}"))

