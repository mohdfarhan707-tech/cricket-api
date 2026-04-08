from django.core.management.base import BaseCommand
from django.utils import timezone

from news.models import NewsItem
from news.rss_fetcher import DEFAULT_FEEDS, fetch_rss_items


class Command(BaseCommand):
    help = "Fetch cricket news from ESPNcricinfo RSS feeds and cache in DB."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=40, help="Max items to process per feed.")
        parser.add_argument(
            "--feed-url",
            type=str,
            default="",
            help="Optional single feed URL (uses source label 'Custom RSS').",
        )

    def handle(self, *args, **options):
        limit = max(1, int(options["limit"] or 40))
        custom = (options.get("feed_url") or "").strip()
        created = 0
        updated = 0

        feeds: list[tuple[str, str]] = []
        if custom:
            feeds.append((custom, "Custom RSS"))
        else:
            for f in DEFAULT_FEEDS:
                feeds.append((f["url"], f["source"]))

        for feed_url, source_label in feeds:
            try:
                items = fetch_rss_items(feed_url)[:limit]
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed feed {feed_url}: {e}"))
                continue

            for it in items:
                if not it.get("link") or not it.get("title"):
                    continue
                obj, was_created = NewsItem.objects.update_or_create(
                    link=it["link"],
                    defaults={
                        "source": source_label[:100],
                        "title": it.get("title", "")[:500],
                        "summary": it.get("summary", ""),
                        "published_at": it.get("published_at") or timezone.now(),
                        "image_url": (it.get("image_url") or "")[:200],
                    },
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(f"Done. created={created} updated={updated}"))
