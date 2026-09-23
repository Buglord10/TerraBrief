from collect import collect_articles
from filter import filter_articles
from ai import generate_briefing
from report import save_report


def main():

    print("================================")
    print("        TERRABRIEF")
    print("     Morning Briefing AI")
    print("================================")
    print()

    print("Step 1: Collecting news...")
    articles = collect_articles()

    print(f"Collected {len(articles)} articles.")

    print()
    print("Step 2: Filtering articles...")
    articles = filter_articles(articles)

    print(f"Found {len(articles)} relevant articles.")

    if not articles:
        print("No relevant articles found.")
        return

    print()
    print("Step 3: Asking OpenRouter AI to analyse the news...")

    briefing = generate_briefing(articles)

    print()
    print("Step 4: Creating report...")

    save_report(briefing)

    print()
    print("================================")
    print("TerraBrief finished successfully.")
    print("================================")


if __name__ == "__main__":
    main()
