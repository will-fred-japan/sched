# File: app.py

import base64
from datetime import datetime, timedelta
import importlib
from flask import Flask, Response, render_template, request
import requests
from config import HEADERS, TARGETS

app = Flask(__name__)

# Valid 16x16 PNG icon (Green calendar square)
FAVICON_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAFUlEQVR42mNk+M9Qz0AEYB41ACMIABK3EACp57yLAAAAAElFTkSuQmCC"
FAVICON_PNG = base64.b64decode(FAVICON_PNG_B64)

@app.route("/icon-192.png")
def icon_192():
    """Serves the 192x192 PWA icon."""
    return Response(FAVICON_PNG, mimetype="image/png")

@app.route("/icon-512.png")
def icon_512():
    """Serves the 512x512 PWA icon."""
    return Response(FAVICON_PNG, mimetype="image/png")

@app.route("/favicon.ico")
def favicon():
    """Serves the favicon directly to satisfy browser root requests."""
    return Response(FAVICON_PNG, mimetype="image/png")

def get_month_str():
    """Returns YYYYMM string from request args, default to current month."""
    ym = request.args.get("month")
    if ym and len(ym) == 6 and ym.isdigit():
        return ym
    return datetime.now().strftime("%Y%m")


def calculate_nav_months(ym_str: str):
    """Calculates prev, current, and next YYYYMM strings."""
    curr_date = datetime.strptime(ym_str, "%Y%m")

    prev_date = curr_date.replace(day=1) - timedelta(days=1)
    next_date = (curr_date.replace(day=1) + timedelta(days=32)).replace(day=1)

    return {
        "prev": prev_date.strftime("%Y%m"),
        "curr": curr_date.strftime("%Y%m"),
        "next": next_date.strftime("%Y%m"),
        "display": curr_date.strftime("%Y年%m月"),
    }


def fetch_target_events(target: dict, ym_str: str) -> list[dict]:
    events = []

    year = ym_str[:4]
    month_int = int(ym_str[4:])
    month_z = ym_str[4:]
    from_ms = int(datetime(int(year), month_int, 1).timestamp() * 1000)

    target_url = target["url"]
    url = target_url.format(
        year=year,
        month=month_int,
        month_z=month_z,
        ym=ym_str,
        from_ms=from_ms,
    )

    req_headers = dict(HEADERS)
    if "timetreeapp.com/api/" in url:
        req_headers["Accept"] = "application/json"
        req_headers["X-TimeTreeA"] = "web/2.1.0/ja"

    try:
        res = requests.get(url, headers=req_headers, timeout=10)
        res.encoding = "utf-8"
        html = res.text if res.status_code == 200 else ""
    except Exception as e:
        print(f"[Error] Fetch failed for {target['name']}: {e}")
        html = ""

    if not html:
        return []

    try:
        module = importlib.import_module(target["parser_module"])
        parsed = module.parse(html, target_month=ym_str)
        for item in parsed:
            item["entity"] = target["name"]
            item["category"] = target["category"]
            events.append(item)
    except Exception as e:
        print(f"[Error] Parsing failed for {target['name']}: {e}")

    return events


@app.route("/")
def index():
    ym_str = get_month_str()
    nav = calculate_nav_months(ym_str)

    all_events = []
    for target in TARGETS:
        all_events.extend(fetch_target_events(target, ym_str))

    all_events.sort(key=lambda x: x.get("date", ""))

    current_date = None
    day_idx = 0
    for event in all_events:
        event_date = event.get("date", "")
        if event_date != current_date:
            if current_date is not None:
                day_idx += 1
            current_date = event_date
        event["day_idx"] = day_idx

    return render_template(
        "index.html",
        events=all_events,
        now=datetime.now().strftime("%H:%M:%S"),
        nav=nav,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
