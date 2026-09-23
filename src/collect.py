import feedparser
import yaml
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen


FEED_TIMEOUT = 10
MAX_ARTICLES_PER_SOURCE = 30
ARTICLE_MAX_AGE_HOURS = 48


def load_sources():
    with open("config/sources.yml", "r", encoding="utf-8") as file:
        return yaml.safe_load(file)["sources"]


def parse_entry_date(item):
    for field in ("published", "updated"):
        value = item.get(field)
        if value:
            try:
                dt = parsedate_to_datetime(value)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except (TypeError, ValueError, OverflowError):
                pass

    for field in ("published_parsed", "updated_parsed"):
        value = item.get(field)
        if value:
            try:
                from calendar import timegm
                return datetime.fromtimestamp(timegm(value), tz=timezone.utc)
            except (TypeError, ValueError, OverflowError):
                pass

    return None


def collect_articles():
    articles = []
    sources = load_sources()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=ARTICLE_MAX_AGE_HOURS)

    print(f"Found {len(sources)} news sources.")
    print(f"Keeping articles from the last {ARTICLE_MAX_AGE_HOURS} hours.", flush=True)

    for index, source in enumerate(sources, start=1):
        name = source["name"]
        url = source["url"]

        print(f"[{index}/{len(sources)}] Reading {name}...", flush=True)

        try:
            request = Request(
                url,
                headers={"User-Agent": "TerraBrief/1.0 (+https://github.com/Buglord10/TerraBrief)"}
            )

            with urlopen(request, timeout=FEED_TIMEOUT) as response:
                feed_data = response.read()

            feed = feedparser.parse(feed_data)

            if getattr(feed, "bozo", False) and not feed.entries:
                print(f"  Skipped {name}: invalid or empty feed.", flush=True)
                continue

            entries = feed.entries[:MAX_ARTICLES_PER_SOURCE]
            added = 0
            skipped_old = 0

            for item in entries:
                published = parse_entry_date(item)

                if published and published < cutoff:
                    skipped_old += 1
                    continue

                articles.append({
                    "source": name,
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "summary": item.get("summary", "")
                })
                added += 1

            print(
                f"  Added {added} recent articles"
                + (f"; skipped {skipped_old} older articles." if skipped_old else "."),
                flush=True
            )

        except Exception as error:
            print(f"  Skipped {name}: {error}", flush=True)

    print(f"Collected {len(articles)} recent articles from {len(sources)} sources.", flush=True)
    return articles
