from datetime import datetime
from pathlib import Path


def save_report(briefing):
    date = datetime.now().strftime("%Y-%m-%d")

    report = f"""# TerraBrief

**Date:** {date}

---

{briefing}

---

Generated automatically by TerraBrief.
"""

    filename = f"data/{date}.md"
    Path("data").mkdir(exist_ok=True)

    with open(filename, "w", encoding="utf-8") as file:
        file.write(report)

    with open("briefing.md", "w", encoding="utf-8") as file:
        file.write(report)

    print(f"\nBriefing saved to {filename}")
    print("Latest briefing saved to briefing.md")
