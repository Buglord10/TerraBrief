import yaml


def load_topics():
    with open("config/topics.yml", "r", encoding="utf-8") as file:
        return yaml.safe_load(file)["topics"]


def find_category(article):
    text = (
        str(article.get("title", "")) + " " +
        str(article.get("summary", ""))
    ).lower()

    topics = load_topics()

    for category_name, category in topics.items():
        for subcategory_name, keywords in category["subtopics"].items():
            for keyword in keywords:
                # YAML interprets keywords such as 737, 747 and 777 as integers.
                # Convert every keyword to a string before doing the comparison.
                if str(keyword).lower() in text:
                    return category_name, subcategory_name

    return None, None


def filter_articles(articles):
    filtered = []
    seen = set()

    for article in articles:
        category, subcategory = find_category(article)

        if not category:
            continue

        title = str(article.get("title", "")).strip().lower()

        if title in seen:
            continue

        seen.add(title)
        article["category"] = category
        article["subcategory"] = subcategory
        filtered.append(article)

    return filtered
