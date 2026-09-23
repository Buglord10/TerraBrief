import os
import requests
from collect import collect_articles
from filter import filter_articles

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def main():
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set.")

    print("Collecting news for AI test...", flush=True)
    articles = collect_articles()
    print("Filtering news for AI test...", flush=True)
    articles = filter_articles(articles)

    if not articles:
        raise RuntimeError("No relevant articles were found.")

    articles = articles[:5]
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

    prompt = """You are TerraBrief, a news briefing assistant.

Using ONLY the supplied articles, write a short test briefing.

Rules:
- Do not invent facts.
- Use only the supplied information.
- Give a short summary of each article.
- Include the source and URL.
- Keep the response under 500 words.

Articles:

""" + article_text

    print(f"Testing OpenRouter with {len(articles)} articles.", flush=True)
    print(f"Request size: approximately {len(prompt):,} characters.", flush=True)
    print("Sending request...", flush=True)

    response = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Buglord10/TerraBrief",
            "X-Title": "TerraBrief full-pipeline test",
        },
        json={
            "model": "openrouter/free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 1000,
        },
        timeout=60,
    )

    print(f"OpenRouter HTTP status: {response.status_code}", flush=True)
    if not response.ok:
        print(response.text, flush=True)
        response.raise_for_status()

    data = response.json()
    reply = data["choices"][0]["message"]["content"]

    print("\n===== AI RESPONSE =====", flush=True)
    print(reply, flush=True)
    print("=======================", flush=True)
    print("SUCCESS: The full TerraBrief pipeline can send article data to OpenRouter.", flush=True)

if __name__ == "__main__":
    main()
