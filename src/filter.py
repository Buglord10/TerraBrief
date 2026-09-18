import yaml


def load_topics():
    with open("config/topics.yml", "r", encoding="utf-8") as file:
        return yaml.safe_load(file)["topics"]


def find_category(article):
    text = (
        article["title"] + " " +
        article["summary"]
    ).lower()

    topics = load_topics()

    for category_name, category in topics.items():

        for keyword in category["topics"]:

            if keyword.lower() in text:
                return category_name

    return None


def filter_articles(articles):

    filtered = []

    for article in articles:

        category = find_category(article)

        if category:

            article["category"] = category

            filtered.append(article)

    return filtered