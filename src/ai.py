import os
import requests


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openrouter/free"
MAX_ARTICLES = 35
REQUEST_TIMEOUT = 180


SYSTEM_PROMPT = """
You are TerraBrief, a personal morning intelligence briefing assistant.

Your job is to analyse the supplied news articles and produce a detailed,
accurate and useful morning briefing.

IMPORTANT RULES:

1. Never invent facts.
2. Only use information contained in the supplied articles.
3. Do not present speculation as fact.
4. Do not exaggerate.
5. Remove duplicate stories.
6. Combine multiple articles about the same event into one story.
7. Prioritise important developments.
8. Explain why important stories matter.
9. Clearly distinguish confirmed facts from claims.
10. Include the source name and URL for every story.
11. Do not include irrelevant stories just to fill space.
12. Give enough detail to make the briefing genuinely useful.
13. Use the category and subcategory supplied with each article.
14. Do not make political recommendations or tell the reader what political
    choice they should make.

BRIEFING STRUCTURE:

# TERRABRIEF

## TOP STORIES

Select approximately 5-10 of the most significant stories across all topics.

For each:

### Headline

**What happened:** Detailed but concise explanation.

**Key details:** Important names, numbers, dates, locations and developments.

**Why it matters:** Explain the significance without exaggeration.

**What happens next:** Only include this when supported by the supplied articles.

**Sources:** List the relevant source names and URLs.

Then organise the rest of the briefing using these categories and subcategories:

# UK
## Politics & Government
## Economy
## Transport
## Education
## Public Safety

# WORLD
## Europe
## North America
## Middle East
## Asia-Pacific
## Africa
## International Organisations

# TECHNOLOGY
## Artificial Intelligence
## Microsoft
## Apple
## Google
## Nvidia
## Space
## Cybersecurity

# AVIATION
## Airlines
## Aircraft
## Airports
## Safety
## Aviation Industry

# FORMULA 1
## Race Weekend
## Teams
## Drivers
## Technical
## F1 Business

# GAMING
## Minecraft
## Xbox
## PlayStation
## PC Gaming
## Nintendo
## Releases

# SCIENCE
## Space
## Physics
## Biology
## Climate
## Environment

# BUSINESS
## Markets
## Companies
## Finance
## Energy

# ENTERTAINMENT
## Film & TV
## Music
## Eurovision
## Theme Parks
## Events

Only include subcategories with genuinely relevant stories.

For each significant story use:

### Headline

**What happened:** Detailed explanation.

**Key details:** Important facts from the supplied sources.

**Why it matters:** Explain the significance.

**What happens next:** Only when supported by the sources.

**Sources:** Source names and URLs.

Do not write a generic conclusion.

The final briefing should feel like a professional morning intelligence briefing rather than a simple list of RSS articles.
"""


def generate_briefing(articles):
    if not articles:
        return "No relevant articles were found."

    # Use a smaller, recent, filtered article set so the model can spend its
    # token budget on a long detailed briefing instead of processing stale or
    # excessive input.
    articles = articles[:MAX_ARTICLES]

    print(f"Preparing {len(articles)} articles for OpenRouter...", flush=True)

    article_text = ""

    for article in articles:
        article_text += f"""
CATEGORY: {article.get('category', 'Unknown')}
SUBCATEGORY: {article.get('subcategory', 'Unknown')}
SOURCE: {article.get('source', 'Unknown')}
TITLE: {article.get('title', '')}
URL: {article.get('url', '')}
SUMMARY: {article.get('summary', '')}

-------------------------
"""

    prompt = SYSTEM_PROMPT + """

Here are today's recent articles:

""" + article_text

    api_key = os.environ.get("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. "
            "Add it as an environment variable or GitHub Actions secret."
        )

    print(f"Sending request to OpenRouter using {MODEL}...", flush=True)
    print(f"Request contains approximately {len(prompt):,} characters.", flush=True)

    response = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Buglord10/TerraBrief",
            "X-Title": "TerraBrief"
        },
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 12000
        },
        timeout=REQUEST_TIMEOUT
    )

    print(f"OpenRouter responded with HTTP {response.status_code}.", flush=True)

    if not response.ok:
        print("OpenRouter error:", flush=True)
        print(response.text, flush=True)
        response.raise_for_status()

    data = response.json()

    try:
        briefing = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"Unexpected OpenRouter response:\n{data}")

    print("OpenRouter briefing received.", flush=True)
    return briefing
