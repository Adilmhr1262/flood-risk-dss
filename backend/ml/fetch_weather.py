"""Fetch daily ERA5 reanalysis weather for study districts from the Open-Meteo archive API.

Covers 2010-01-01 to 2024-12-31, one request per district. Raw JSON cached under
datasets/raw/weather/<district>.json. Run: .venv/bin/python backend/ml/fetch_weather.py
"""
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

DISTRICTS = [
    ("Badin", 24.66, 68.84),
    ("Dadu", 26.73, 67.78),
    ("Dera Ghazi Khan", 30.06, 70.64),
    ("Ghotki", 28.00, 69.32),
    ("Hyderabad", 25.40, 68.37),
    ("Jacobabad", 28.28, 68.44),
    ("Karachi", 24.86, 67.01),
    ("Larkana", 27.56, 68.21),
    ("Rajanpur", 29.10, 70.32),
    ("Shikarpur", 27.96, 68.64),
    ("Sukkur", 27.70, 68.86),
    ("Thatta", 24.75, 67.92),
]

OUT = Path(__file__).resolve().parent.parent.parent / "datasets" / "raw" / "weather"
OUT.mkdir(parents=True, exist_ok=True)


def fetch(name, lat, lon):
    params = urllib.parse.urlencode({
        "latitude": lat,
        "longitude": lon,
        "start_date": "2010-01-01",
        "end_date": "2024-12-31",
        "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min,relative_humidity_2m_mean",
        "timezone": "UTC",
    })
    url = f"https://archive-api.open-meteo.com/v1/archive?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "flood-risk-dss-research/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())
    n = len(data["daily"]["time"])
    path = OUT / f"{name}.json"
    path.write_text(json.dumps(data))
    return n


def main():
    for i, (name, lat, lon) in enumerate(DISTRICTS):
        n = fetch(name, lat, lon)
        print(f"{name}: {n} days cached", flush=True)
        if i < len(DISTRICTS) - 1:
            time.sleep(2)  # be polite to the free API


if __name__ == "__main__":
    main()
