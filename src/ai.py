import requests


OLLAMA_URL = "http://localhost:11434/api/generate"

MODEL = "llama3.1"


SYSTEM_PROMPT = """
You are TerraBrief, a personal morning intelligence briefing assistant.

Your job is to analyse the supplied news articles and produce a concise,
accurate morning briefing.

Rules:

1. Never invent facts.
2. Only use information contained in the supplied articles.
3. Do not present speculation as fact.
4. Do not exaggerate.
5. Remove duplicate stories.
6. Prioritise significant developments.
7. Explain why important stories matter.
8. Clearly separate facts from claims.
9. Keep the briefing easy to read.
10. Include the source name and URL for every story.

Organise the briefing into:

UK
World
Technology
Aviation
Formula 1
Gaming

For each important story use:

### Headline

**What happened:** short explanation.

**Why it matters:** short explanation.

**Source:** source name and URL.

Only include sections where there are relevant stories.
"""


def generate_briefing(articles):

    article_text = ""

    for article in articles:

        article_text += f"""
CATEGORY: {article['category']}
SOURCE: {article['source']}
TITLE: {article['title']}
URL: {article['url']}
SUMMARY: {article['summary']}

-------------------------
"""

    prompt = SYSTEM_PROMPT + """

Here are today's articles:

""" + article_text

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=600
    )

    response.raise_for_status()

    return response.json()["response"]