import os
import time
import requests


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openrouter/free"

# Keep the AI input small enough for consistent response times while retaining
# enough articles for a detailed briefing.
MAX_ARTICLES = 30

# A single slow free-model route should not hold the workflow for several
# minutes. Failed/time-out requests are retried automatically.
REQUEST_TIMEOUT = 75
MAX_ATTEMPTS = 2


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

    # The collector already limits articles to the last 48 hours. Limit the AI
    # input further so the model spends its time generating the briefing rather
    # than processing excessive input.
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

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 12000
    }

    last_error = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            print(
                f"OpenRouter attempt {attempt}/{MAX_ATTEMPTS} "
                f"(timeout: {REQUEST_TIMEOUT}s)...",
                flush=True
            )

            response = requests.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/Buglord10/TerraBrief",
                    "X-Title": "TerraBrief"
                },
                json=payload,
                timeout=REQUEST_TIMEOUT
            )

            print(
                f"OpenRouter responded with HTTP {response.status_code}.",
                flush=True
            )

            if response.ok:
                data = response.json()

                try:
                    briefing = data["choices"][0]["message"]["content"]
                except (KeyError, IndexError, TypeError):
                    raise RuntimeError(
                        f"Unexpected OpenRouter response:\n{data}"
                    )

                print("OpenRouter briefing received.", flush=True)
                return briefing

            last_error = RuntimeError(
                f"OpenRouter returned HTTP {response.status_code}: "
                f"{response.text[:1000]}"
            )
            print(f"OpenRouter error: {last_error}", flush=True)

        except requests.exceptions.Timeout as error:
            last_error = error
            print(
                f"OpenRouter attempt {attempt} timed out after "
                f"{REQUEST_TIMEOUT} seconds.",
                flush=True
            )

        except requests.exceptions.RequestException as error:
            last_error = error
            print(f"OpenRouter request failed: {error}", flush=True)

        if attempt < MAX_ATTEMPTS:
            print("Retrying with a fresh OpenRouter route in 3 seconds...", flush=True)
            time.sleep(3)

    raise RuntimeError(
        f"OpenRouter failed after {MAX_ATTEMPTS} attempts: {last_error}"
    )
