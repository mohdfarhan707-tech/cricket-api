import threading

from django.core.cache import cache
from django.core.management import call_command
from django.db.models import Max
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import NewsItem
from .serializers import NewsItemSerializer

_NEWS_BG_COOLDOWN_SEC = 45 * 60  # at most one background sync per 45 minutes
_NEWS_STALE_HOURS = 8  # trigger background sync if newest article older than this


def _maybe_background_sync_news() -> None:
    """If the cached news looks stale, refresh in a daemon thread (non-blocking for the client)."""
    if cache.get("news_bg_sync_lock"):
        return
    if not cache.add("news_bg_sync_lock", 1, 120):
        return

    def _run() -> None:
        try:
            now = timezone.now()
            cnt = NewsItem.objects.count()
            latest = NewsItem.objects.aggregate(m=Max("published_at"))["m"]
            stale = False
            if cnt < 5:
                stale = True
            elif latest and (now - latest).total_seconds() > _NEWS_STALE_HOURS * 3600:
                stale = True
            if not stale:
                return
            if cache.get("news_bg_cooldown"):
                return
            cache.set("news_bg_cooldown", 1, _NEWS_BG_COOLDOWN_SEC)
            call_command("fetch_news", limit=50)
        except Exception:
            pass
        finally:
            cache.delete("news_bg_sync_lock")

    threading.Thread(target=_run, daemon=True).start()


class NewsAPI(APIView):
    def get(self, request):
        _maybe_background_sync_news()
        qs = NewsItem.objects.order_by("-published_at", "-id")[:80]
        serializer = NewsItemSerializer(qs, many=True)
        return Response(serializer.data)
