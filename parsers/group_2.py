# File: parsers/group_2.py

import json
import unicodedata
from datetime import datetime, timedelta, timezone

# Japan Standard Time (UTC+9)
JST = timezone(timedelta(hours=9))
WEEKDAYS_JA = ["月", "火", "水", "木", "金", "土", "日"]


def _clean_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return unicodedata.normalize("NFC", value).strip()


def parse(html_content: str | bytes, target_month: str = None) -> list[dict]:
    events = []

    if target_month and len(target_month) == 6:
        year = int(target_month[:4])
        month = int(target_month[4:])
    else:
        year, month = 2026, 8
        target_month = f"{year}{month:02d}"

    if isinstance(html_content, bytes):
        html_content = html_content.decode("utf-8", errors="replace")

    try:
        data = json.loads(html_content)
    except Exception as e:
        print(f"[group_2] JSON parse failed: {e}")
        return []

    items = data.get("public_events") or []
    if not isinstance(items, list):
        return []

    seen = set()

    for item in items:
        if not isinstance(item, dict):
            continue

        title = _clean_text(item.get("title"))
        start_at = item.get("start_at")
        if not title or not start_at:
            continue

        end_at = item.get("end_at") or start_at

        venue = _clean_text(item.get("location_name"))
        if not venue and "＠" in title:
            venue = _clean_text(title.split("＠", 1)[-1])
        elif not venue and "@" in title:
            venue = _clean_text(title.split("@", 1)[-1])

        try:
            # Convert timestamps strictly in JST (UTC+9)
            dt_start = datetime.fromtimestamp(start_at / 1000, tz=JST)
            dt_end = datetime.fromtimestamp(end_at / 1000, tz=JST)

            # If end_at falls on midnight at the start of the next day, adjust boundary by 1 second
            if dt_end > dt_start and dt_end.hour == 0 and dt_end.minute == 0 and dt_end.second == 0:
                dt_end -= timedelta(seconds=1)

            start_date = dt_start.date()
            end_date = max(start_date, dt_end.date())

            current_date = start_date
            while current_date <= end_date:
                if current_date.strftime("%Y%m") == target_month:
                    weekday = WEEKDAYS_JA[current_date.weekday()]
                    date_str = f"{current_date.year}.{current_date.month:02d}.{current_date.day:02d} ({weekday})"

                    key = f"{date_str}_{title}"
                    if key not in seen:
                        seen.add(key)
                        events.append(
                            {
                                "date": date_str,
                                "title": title,
                                "venue": venue,
                            }
                        )

                current_date += timedelta(days=1)

        except Exception as e:
            print(f"[group_2] date error for {title}: {e}")
            continue

    events.sort(key=lambda x: x["date"])
    return events