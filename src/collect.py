import feedparser
import yaml


def load_sources():
    with open("config/sources.yml", "r", encoding="utf-8") as file:
        return yaml.safe_load(file)["sources"]


def collect_articles():
    articles = []

    sources = load_sources()

    for source in sources:
        print(f"Reading {source['name']}...")

        feed = feedparser.parse(source["url"])

        for item in feed.entries:
            articles.append({
                "source": source["name"],
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "summary": item.get("summary", "")
            })

    return articles