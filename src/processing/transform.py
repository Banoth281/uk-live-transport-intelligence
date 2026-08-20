from src.processing.models import ArrivalEvent


def transform_arrival(raw: dict) -> ArrivalEvent:
    return ArrivalEvent(
        vehicle_id=raw.get("vehicleId"),
        line_id=raw.get("lineId"),
        line_name=raw.get("lineName"),
        station_id=raw.get("naptanId"),
        station_name=raw.get("stationName"),
        destination_name=raw.get("destinationName"),
        direction=raw.get("direction"),
        time_to_station=raw.get("timeToStation"),
        expected_arrival=raw.get("expectedArrival"),
        timestamp=raw.get("timestamp"),
        mode_name=raw.get("modeName"),
        platform_name=raw.get("platformName"),
    )