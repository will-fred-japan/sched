# File: parsers/team_1.py

import re
from bs4 import BeautifulSoup


def parse(html_content: str, target_month: str = None) -> list[dict]:
    soup = BeautifulSoup(html_content, "html.parser")
    events = []

    if target_month and len(target_month) == 6:
        year = int(target_month[:4])
        month = int(target_month[4:])
    else:
        year, month = 2026, 8

    for tr in soup.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if len(cells) < 3:
            continue

        day_raw = cells[0].get_text(strip=True)
        weekday = cells[1].get_text(strip=True)
        content = cells[2].get_text(" ", strip=True)

        day_match = re.search(r"^\d+", day_raw)
        if not day_match:
            continue

        day_num = int(day_match.group())

        # Skip empty, OFF, or private (非公開) entries
        if not content or "OFF" in content or "非公開" in content:
            continue

        clean_title = re.sub(r"\s+", " ", content).strip()
        date_str = f"{year}.{month:02d}.{day_num:02d} ({weekday})"

        events.append(
            {
                "date": date_str,
                "title": clean_title,
                "venue": "",
            }
        )

    return events