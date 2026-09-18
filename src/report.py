from datetime import datetime


def save_report(briefing):

    date = datetime.now().strftime("%Y-%m-%d")

    report = f"""# TerraBrief

**Date:** {date}

---

{briefing}

---

Generated automatically by TerraBrief.
"""

    filename = "briefing.md"

    with open(filename, "w", encoding="utf-8") as file:
        file.write(report)

    print(f"\nBriefing saved to {filename}")