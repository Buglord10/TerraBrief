import feedparser
import yaml
from urllib.request import Request, urlopen


FEED_TIMEOUT = 10


def load_sources():
    with open("config/sources.yml", "r", encoding="utf-8") as file:
        return yaml.safe_load(file)["sources"]


def collect_articles():
    articles = []
    sources = load_sources()

    print(f"Found {len(sources)} news sources.")

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

            count = 0
            for item in feed.entries:
                articles.append({
                    "source": name,
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "summary": item.get("summary", "")
                })
                count += 1

            print(f"  Added {count} articles.", flush=True)

        except Exception as error:
            print(f"  Skipped {name}: {error}", flush=True)

    print(f"Collected {len(articles)} articles from {len(sources)} sources.", flush=True)
    return articles
