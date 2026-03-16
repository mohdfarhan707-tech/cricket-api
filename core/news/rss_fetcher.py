import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import requests


DEFAULT_FEEDS = [
    "https://www.espncricinfo.com/rss/content/story/feeds/0.xml",
]


def _strip_html(s: str) -> str:
    s = s or ""
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _parse_rfc822_date(s: str) -> datetime | None:
    if not s:
        return None
    try:
        # Example: "Sun, 16 Mar 2026 10:30:00 GMT"
        dt = datetime.strptime(s, "%a, %d %b %Y %H:%M:%S %Z")
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def fetch_rss_items(feed_url: str) -> list[dict]:
    """Return a list of parsed RSS <item> dicts."""
    resp = requests.get(feed_url, timeout=12, headers={"User-Agent": "projectcricket/1.0"})
    resp.raise_for_status()
    root = ET.fromstring(resp.text)

    items = []
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = item.findtext("description") or ""
        pub_date = (item.findtext("pubDate") or "").strip()

        # Try RSS media namespace for images
        image_url = ""
        for enc in item.findall("{http://search.yahoo.com/mrss/}content"):
            image_url = enc.attrib.get("url") or ""
            if image_url:
                break

        items.append(
            {
                "title": title,
                "link": link,
                "summary": _strip_html(description),
                "published_at": _parse_rfc822_date(pub_date),
                "image_url": image_url,
            }
        )

    return items

