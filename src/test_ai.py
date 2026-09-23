import os
import requests


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def main():
    api_key = os.environ.get("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set.")

    print("Testing OpenRouter connection...", flush=True)
    print("Sending a tiny test request...", flush=True)

    response = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Buglord10/TerraBrief",
            "X-Title": "TerraBrief connectivity test",
        },
        json={
            "model": "openrouter/free",
            "messages": [
                {
                    "role": "user",
                    "content": "Reply with exactly: TERRABRIEF AI TEST OK"
                }
            ],
            "temperature": 0,
            "max_tokens": 20,
        },
        timeout=30,
    )

    print(f"OpenRouter HTTP status: {response.status_code}", flush=True)

    if not response.ok:
        print("OpenRouter returned an error:", flush=True)
        print(response.text, flush=True)
        response.raise_for_status()

    data = response.json()
    reply = data["choices"][0]["message"]["content"]

    print(f"AI response: {reply}", flush=True)
    print("SUCCESS: TerraBrief can reach OpenRouter and receive an AI response.", flush=True)


if __name__ == "__main__":
    main()
