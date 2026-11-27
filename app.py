# File: app.py
import base64
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import importlib
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, Response, render_template, request, jsonify, make_response
import requests
from config import HEADERS, TARGETS

app = Flask(__name__)

# Timezone setup
TZ = ZoneInfo("Asia/Tokyo")

from pathlib import Path
from flask import Flask, Response

# If `app` is already created elsewhere in your module, remove these 2 lines.
app = Flask(__name__)

ICONS_DIR = Path(__file__).resolve().parent / "icons"

FAVICON_PNG = (ICONS_DIR / "favicon.png").read_bytes()
ICON_192_PNG = (ICONS_DIR / "icon-192.png").read_bytes()
ICON_512_PNG = (ICONS_DIR / "icon-512.png").read_bytes()


@app.route("/icon-192.png")
def icon_192():
    return Response(ICON_192_PNG, mimetype="image/png", headers={"Cache-Control": "public, max-age=86400"})


@app.route("/icon-512.png")
def icon_512():
    return Response(ICON_512_PNG, mimetype="image/png", headers={"Cache-Control": "public, max-age=86400"})


@app.route("/favicon.ico")
def favicon():
    return Response(FAVICON_PNG, mimetype="image/png", headers={"Cache-Control": "public, max-age=86400"})


def get_month_str():
    ym = request.args.get("month")
    if ym and len(ym) == 6 and ym.isdigit():
        return ym
    return datetime.now(TZ).strftime("%Y%m")


def calculate_nav_months(ym_str: str):
    curr_date = datetime.strptime(ym_str, "%Y%m").replace(tzinfo=TZ)
    prev_date = (curr_date.replace(day=1) - timedelta(days=1))
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
    
    # Calculate timestamp in JST
    dt_jst = datetime(int(year), month_int, 1, tzinfo=TZ)
    from_ms = int(dt_jst.timestamp() * 1000)

    target_url = target["url"]
    url = target_url.format(
        year=year, month=month_int, month_z=month_z, ym=ym_str, from_ms=from_ms,
    )

    req_headers = dict(HEADERS)
    if "timetreeapp.com/api/" in url:
        req_headers["Accept"] = "application/json"
        req_headers["X-TimeTreeA"] = "web/2.1.0/ja"

    try:
        res = requests.get(url, headers=req_headers, timeout=8)
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


def get_events_for_month(ym_str: str):
    """Fetches all targets in parallel for a specific month."""
    all_events = []
    with ThreadPoolExecutor(max_workers=len(TARGETS)) as executor:
        futures = [executor.submit(fetch_target_events, t, ym_str) for t in TARGETS]
        for future in futures:
            try:
                all_events.extend(future.result())
            except Exception as e:
                print(f"[Error] Thread execution failed: {e}")
    
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
        
    return all_events


@app.route("/")
def index():
    ym_str = get_month_str()
    nav = calculate_nav_months(ym_str)
    all_events = get_events_for_month(ym_str)

    response = make_response(render_template(
        "index.html",
        events=all_events,
        now=datetime.now(TZ).strftime("%H:%M:%S"),
        nav=nav,
    ))
    # Cache the HTML page at the Edge/CDN for 5 minutes
    response.headers["Cache-Control"] = "public, s-maxage=600, stale-while-revalidate=120"
    return response


@app.route("/api/prefetch")
def api_prefetch():
    """API endpoint for client-side prefetching. Returns JSON to be lighter than HTML."""
    ym_str = request.args.get("month")
    if not ym_str or len(ym_str) != 6:
        return jsonify({"error": "Invalid month"}), 400
    
    events = get_events_for_month(ym_str)
    
    response = jsonify({"month": ym_str, "count": len(events)})
    # Cache API responses aggressively so subsequent visits are instant
    response.headers["Cache-Control"] = "public, s-maxage=600, stale-while-revalidate=120"
    return response


if __name__ == "__main__":
    app.run(debug=True, port=5000)
