"""Small, independent TfL live feed for the public Streamlit demo."""
from datetime import datetime, timezone
import math

TFL_URL = "https://api.tfl.gov.uk/Line/{line_id}/Arrivals"
# TfL rail service IDs. Keep one selector with a visible mode label in the app.
LINE_GROUPS = {
    "Bakerloo": "Underground", "Central": "Underground",
    "Circle": "Underground", "District": "Underground",
    "Hammersmith & City": "Underground", "Jubilee": "Underground",
    "Metropolitan": "Underground", "Northern": "Underground",
    "Piccadilly": "Underground", "Victoria": "Underground",
    "Waterloo & City": "Underground",
    "Elizabeth line": "Elizabeth line", "DLR": "DLR",
    "Lioness": "Overground", "Mildmay": "Overground",
    "Windrush": "Overground", "Weaver": "Overground",
    "Suffragette": "Overground", "Liberty": "Overground",
    "Tram": "Tram",
}
LINES = {
    "Bakerloo": "bakerloo", "Central": "central", "Circle": "circle",
    "District": "district", "Hammersmith & City": "hammersmith-city",
    "Jubilee": "jubilee", "Metropolitan": "metropolitan",
    "Northern": "northern", "Piccadilly": "piccadilly",
    "Victoria": "victoria", "Waterloo & City": "waterloo-city",
    "Elizabeth line": "elizabeth", "DLR": "dlr",
    "Lioness": "lioness", "Mildmay": "mildmay",
    "Windrush": "windrush", "Weaver": "weaver",
    "Suffragette": "suffragette", "Liberty": "liberty", "Tram": "tram",
}
# Illustrative accents inspired by the TfL network palette.
LINE_COLOURS = {
    "Bakerloo": "#b36305", "Central": "#e32017", "Circle": "#ffd300",
    "District": "#00782a", "Hammersmith & City": "#f3a9bb",
    "Jubilee": "#a0a5a9", "Metropolitan": "#9b0056",
    "Northern": "#babfc6", "Piccadilly": "#003688",
    "Victoria": "#0098d4", "Waterloo & City": "#95cdba",
    "Elizabeth line": "#6950a1", "DLR": "#00a4a7",
    "Lioness": "#f6c443", "Mildmay": "#438cca",
    "Windrush": "#e43c46", "Weaver": "#a54460",
    "Suffragette": "#4da68b", "Liberty": "#adb7c7", "Tram": "#71ad43",
}


def normalise_arrivals(payload, *, now=None):
    """Keep usable predictions; do not treat a prediction as an actual arrival."""
    if not isinstance(payload, list):
        raise ValueError("TfL returned an unexpected response.")
    now = now or datetime.now(timezone.utc)
    result = []
    seen = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        seconds = item.get("timeToStation")
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
            continue
        if not math.isfinite(seconds) or seconds < 0:
            continue
        station = item.get("stationName")
        if not isinstance(station, str) or not station.strip():
            continue
        expected = item.get("expectedArrival")
        if expected:
            try:
                arrival_time = datetime.fromisoformat(expected.replace("Z", "+00:00"))
                if arrival_time.tzinfo is None:
                    continue
                remaining = (arrival_time - now).total_seconds()
            except (AttributeError, TypeError, ValueError):
                continue
            if remaining <= 0:
                continue
            seconds = remaining
        destination = str(item.get("destinationName") or "Not supplied")
        platform = str(item.get("platformName") or "Not supplied")
        if expected:
            identity = (station.strip(), destination, platform, expected)
            if identity in seen:
                continue
            seen.add(identity)
        result.append({
            "station": station.strip(),
            "destination": destination,
            "platform": platform,
            "minutes": round(seconds / 60, 1),
            "expected_arrival": expected or "",
            "vehicle_id": str(item.get("vehicleId") or ""),
        })
    return sorted(result, key=lambda row: (row["station"], row["minutes"]))


def fetch_arrivals(line_id, *, api_key=None, session=None):
    if line_id not in LINES.values():
        raise ValueError("Select a supported line.")
    if session is None:
        import requests
        session = requests
    client = session
    params = {"app_key": api_key} if api_key else None
    response = client.get(TFL_URL.format(line_id=line_id), params=params, timeout=10)
    response.raise_for_status()
    retrieved_at = datetime.now(timezone.utc)
    rows = normalise_arrivals(response.json(), now=retrieved_at)
    return rows, retrieved_at
