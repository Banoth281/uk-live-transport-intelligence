import os

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.tfl.gov.uk"
API_KEY = os.getenv("TFL_API_KEY")


def get_line_arrivals(line_id: str):
    """Fetch live arrival predictions for a TfL line."""

    url = f"{BASE_URL}/Line/{line_id}/Arrivals"

    params = {
        "app_key": API_KEY
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()

from src.processing.transform import transform_arrival

if __name__ == "__main__":
    arrivals = get_line_arrivals("victoria")

    print(f"\nReceived {len(arrivals)} live arrival predictions\n")

    validated = []

    for raw in arrivals:
        try:
            event = transform_arrival(raw)
            validated.append(event)
        except Exception as exc:
            print(f"Validation failed: {exc}")

    print(f"Validated {len(validated)} arrival events\n")

    for event in validated[:10]:
        print(
            f"{event.line_name} | "
            f"{event.station_name} | "
            f"{event.destination_name} | "
            f"{event.time_to_station}s"
        )