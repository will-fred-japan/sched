# File: parsers/group_1.py

import re
from bs4 import BeautifulSoup


def parse(html_content: str, target_month: str = None) -> list[dict]:
    soup = BeautifulSoup(html_content, "html.parser")
    events = []

    if target_month and len(target_month) == 6:
        year = int(target_month[:4])
        month = int(target_month[4:])
    else:
        year, month = 2026, 9

    pattern = re.compile(
        r"(\d{1,2})\s*日\s*([月火水木金土日])\s*(.*?)(?=\d{1,2}\s*日\s*[月火水木金土日]|$)",
        re.DOTALL,
    )

    page_text = soup.get_text()
    matches = pattern.findall(page_text)

    if matches:
        for day_str, weekday, content in matches:
            day_num = int(day_str)
            clean_content = re.sub(r"\s+", " ", content).strip()

            if "OFFICIAL FAN CLUB" in clean_content:
                clean_content = clean_content.split("OFFICIAL FAN CLUB")[0].strip()

            if not clean_content or len(clean_content) < 2:
                continue

            date_str = f"{year}.{month:02d}.{day_num:02d} ({weekday})"

            venue = ""
            if "@" in clean_content:
                parts = clean_content.split("@")
                venue = "@" + parts[1].split()[0]

            events.append(
                {
                    "date": date_str,
                    "title": clean_content,
                    "venue": venue,
                }
            )

    return events