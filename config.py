# File: config.py

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

TARGETS = [
    {
        "name": "川崎フロンターレ",
        "category": "スポーツ",
        "url": "https://www.frontale.co.jp/schedule/monthly.php?m={ym}",
        "parser_module": "parsers.team_1",
    },
    {
        "name": "ハルニシオン",
        "category": "音楽",
        "url": "https://harunision-official.boosty.app/schedules?month={month}&year={year}",
        "parser_module": "parsers.group_1",
    },
    {
        "name": "iLiFE!",
        "category": "音楽",
        "url": "https://timetreeapp.com/api/v2/public_calendars/ilife_official/public_events?from={from_ms}",
        "parser_module": "parsers.group_2",
    },
]