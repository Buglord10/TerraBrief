import os
import re
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


CATEGORIES = {
    "UK": ["Politics & Government", "Economy", "Transport", "Education", "Public Safety"],
    "WORLD": ["Europe", "North America", "Middle East", "Asia-Pacific", "Africa", "International Organisations"],
    "TECHNOLOGY": ["Artificial Intelligence", "Microsoft", "Apple", "Google", "Nvidia", "Space", "Cybersecurity"],
    "AVIATION": ["Airlines", "Aircraft", "Airports", "Safety", "Aviation Industry"],
    "FORMULA 1": ["Race Weekend", "Teams", "Drivers", "Technical", "F1 Business"],
    "GAMING": ["Minecraft", "Xbox", "PlayStation", "PC Gaming", "Nintendo", "Releases"],
    "SCIENCE": ["Space", "Physics", "Biology", "Climate", "Environment"],
    "BUSINESS": ["Markets", "Companies", "Finance", "Energy"],
    "ENTERTAINMENT": ["Film & TV", "Music", "Eurovision", "Theme Parks", "Events"],
}

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

STRICT OUTPUT FORMAT:

The report MUST contain these headings and ONLY these headings:

# TERRABRIEF
## TOP STORIES

Then use only these category headings when they contain relevant stories:

# UK
# WORLD
# TECHNOLOGY
# AVIATION
# FORMULA 1
# GAMING
# SCIENCE
# BUSINESS
# ENTERTAINMENT

Within a category, use ONLY its matching subcategory headings:

UK:
## Politics & Government
## Economy
## Transport
## Education
## Public Safety

WORLD:
## Europe
## North America
## Middle East
## Asia-Pacific
## Africa
## International Organisations

TECHNOLOGY:
## Artificial Intelligence
## Microsoft
## Apple
## Google
## Nvidia
## Space
## Cybersecurity

AVIATION:
## Airlines
## Aircraft
## Airports
## Safety
## Aviation Industry

FORMULA 1:
## Race Weekend
## Teams
## Drivers
## Technical
## F1 Business

GAMING:
## Minecraft
## Xbox
## PlayStation
## PC Gaming
## Nintendo
## Releases

SCIENCE:
## Space
## Physics
## Biology
## Climate
## Environment

BUSINESS:
## Markets
## Companies
## Finance
## Energy

ENTERTAINMENT:
## Film & TV
## Music
## Eurovision
## Theme Parks
## Events

Do NOT create any other #, ## or ### headings.
Do NOT repeat a category or subcategory.
Do NOT create standalone headings such as "HEALTH", "SPACE", "TRANSPORT",
"POLITICS & GOVERNMENT", "EUROVISION", etc. outside their parent category.
Do NOT create a second copy of a story merely because it fits multiple topics.
A story belongs in the single most appropriate category and subcategory.

TOP STORIES:

Select approximately 5-10 of the most significant stories across all topics.

For each:

### Headline

**What happened:** Detailed but concise explanation.

**Key details:** Important names, numbers, dates, locations and developments.

**Why it matters:** Explain the significance without exaggeration.

**What happens next:** Only include this when supported by the supplied articles.

**Sources:** List the relevant source names and URLs.

For category sections, use the same story format. Only include subcategories
with genuinely relevant stories.

Do not write a generic conclusion.

The final briefing should feel like a professional morning intelligence briefing
rather than a simple list of RSS articles.
"""


def sanitize_briefing(briefing):
    """
    Enforce TerraBrief's document structure after generation.

    Free models can occasionally invent extra headings or repeat sections.
    Keep valid content, remove unsupported headings, and discard repeated
    category/subcategory sections so the website always receives a clean report.
    """
    lines = briefing.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    valid_categories = {name.upper(): name for name in CATEGORIES}
    valid_subcategories = {
        sub.upper(): sub
        for subs in CATEGORIES.values()
        for sub in subs
    }

    output = []
    seen_categories = set()
    seen_subcategories = set()
    current_category = None
    current_subcategory = None
    skipping_duplicate = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("# ") and not stripped.startswith("## "):
            heading = stripped[2:].strip()
            key = heading.upper()

            if key == "TERRABRIEF":
                output.append("# TERRABRIEF")
                current_category = None
                current_subcategory = None
                skipping_duplicate = False
                continue

            if key in valid_categories:
                category = valid_categories[key]
                if category.upper() in seen_categories:
                    skipping_duplicate = True
                    current_category = category
                    current_subcategory = None
                    continue

                seen_categories.add(category.upper())
                output.append(f"# {category}")
                current_category = category
                current_subcategory = None
                skipping_duplicate = False
                continue

            # Unknown top-level heading: ignore it and its following content.
            skipping_duplicate = True
            current_category = None
            current_subcategory = None
            continue

        if stripped.startswith("## "):
            heading = stripped[3:].strip()
            key = heading.upper()

            if key == "TOP STORIES":
                if "TOP STORIES" in seen_subcategories:
                    skipping_duplicate = True
                else:
                    seen_subcategories.add("TOP STORIES")
                    output.append("## TOP STORIES")
                    current_category = None
                    current_subcategory = "TOP STORIES"
                    skipping_duplicate = False
                continue

            if current_category and key in {
                sub.upper() for sub in CATEGORIES[current_category]
            }:
                subcategory = valid_subcategories[key]
                unique_key = f"{current_category.upper()}::{subcategory.upper()}"

                if unique_key in seen_subcategories:
                    skipping_duplicate = True
                    current_subcategory = subcategory
                    continue

                seen_subcategories.add(unique_key)
                output.append(f"## {subcategory}")
                current_subcategory = subcategory
                skipping_duplicate = False
                continue

            # A known subcategory in the wrong place, or an unsupported heading.
            skipping_duplicate = True
            current_subcategory = None
            continue

        if stripped.startswith("### "):
            # Story headings are allowed only inside TOP STORIES or a valid
            # category/subcategory section.
            if current_subcategory:
                if not skipping_duplicate:
                    output.append(line)
            continue

        if not skipping_duplicate:
            output.append(line)

    # Remove excessive blank lines while preserving readable paragraph spacing.
    cleaned = []
    blank = False
    for line in output:
        if not line.strip():
            if not blank:
                cleaned.append("")
            blank = True
        else:
            cleaned.append(line)
            blank = False

    return "\n".join(cleaned).strip()


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

                briefing = sanitize_briefing(briefing)
                print("OpenRouter briefing received and structure validated.", flush=True)
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
