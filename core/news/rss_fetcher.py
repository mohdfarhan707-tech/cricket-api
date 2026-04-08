import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests

# Multiple ESPNcricinfo regional feeds + global stories for broader coverage.
DEFAULT_FEEDS: list[dict[str, str]] = [
    {"url": "https://www.espncricinfo.com/rss/content/story/feeds/0.xml", "source": "ESPNcricinfo (Global)"},
    {"url": "https://www.espncricinfo.com/rss/content/story/feeds/6.xml", "source": "ESPNcricinfo (India)"},
    {"url": "https://www.espncricinfo.com/rss/content/story/feeds/1.xml", "source": "ESPNcricinfo (England)"},
    {"url": "https://www.espncricinfo.com/rss/content/story/feeds/2.xml", "source": "ESPNcricinfo (Australia)"},
    {"url": "https://www.espncricinfo.com/rss/content/story/feeds/7.xml", "source": "ESPNcricinfo (Pakistan)"},
]


def _strip_html(s: str) -> str:
    s = s or ""
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _parse_pub_date(s: str) -> datetime | None:
    """Parse RSS/Atom-style date headers (RFC 822 / 2822)."""
    raw = (s or "").strip()
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        pass
    try:
        dt = datetime.strptime(raw, "%a, %d %b %Y %H:%M:%S %Z")
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _find_image_url(item: ET.Element) -> str:
    """Best-effort image from RSS (media RSS, enclosure, thumbnail)."""
    # Yahoo media namespace (common on ESPN)
    for enc in item.findall("{http://search.yahoo.com/mrss/}content"):
        u = enc.attrib.get("url") or ""
        if u:
            return u
    for thumb in item.findall("{http://search.yahoo.com/mrss/}thumbnail"):
        u = thumb.attrib.get("url") or ""
        if u:
            return u
    # Generic enclosure (image/*)
    enc_el = item.find("enclosure")
    if enc_el is not None:
        t = (enc_el.attrib.get("type") or "").lower()
        if t.startswith("image/"):
            return enc_el.attrib.get("url") or ""
    return ""


def fetch_rss_items(feed_url: str) -> list[dict]:
    """Return a list of parsed RSS <item> dicts."""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; projectcricket/2.0; +https://github.com/)",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }
    resp = requests.get(feed_url, timeout=18, headers=headers)
    resp.raise_for_status()
    text = resp.text
    # Some feeds declare entities; ElementTree may choke — strip common problematic bits
    root = ET.fromstring(text)

    items = []
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = item.findtext("description") or item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded") or ""
        pub_date = (item.findtext("pubDate") or item.findtext("{http://purl.org/dc/elements/1.1/}date") or "").strip()

        image_url = _find_image_url(item)

        items.append(
            {
                "title": title,
                "link": link,
                "summary": _strip_html(description),
                "published_at": _parse_pub_date(pub_date),
                "image_url": image_url,
            }
        )

    return items
