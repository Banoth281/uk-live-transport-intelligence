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


def normalise_arrivals(payload):
    """Keep usable predictions; do not treat a prediction as an actual arrival."""
    if not isinstance(payload, list):
        raise ValueError("TfL returned an unexpected response.")
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
        result.append({
            "station": station.strip(),
            "destination": str(item.get("destinationName") or "Not supplied"),
            "platform": str(item.get("platformName") or "Not supplied"),
            "minutes": round(seconds / 60, 1),
            "expected_arrival": item.get("expectedArrival") or "",
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
    rows = normalise_arrivals(response.json())
    retrieved_at = datetime.now(timezone.utc)
    return rows, retrieved_at
