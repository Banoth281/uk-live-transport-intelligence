"""Small, independent TfL live feed for the public Streamlit demo."""
from datetime import datetime, timezone
import math

TFL_URL = "https://api.tfl.gov.uk/Line/{line_id}/Arrivals"
LINES = {
    "Victoria": "victoria",
    "Northern": "northern",
    "Central": "central",
    "Piccadilly": "piccadilly",
    "Jubilee": "jubilee",
}


def normalise_arrivals(payload, *, now=None):
    """Keep usable predictions; do not treat a prediction as an actual arrival."""
    if not isinstance(payload, list):
        raise ValueError("TfL returned an unexpected response.")
    now = now or datetime.now(timezone.utc)
    result = []
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
        result.append({
            "station": station.strip(),
            "destination": str(item.get("destinationName") or "Not supplied"),
            "platform": str(item.get("platformName") or "Not supplied"),
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
