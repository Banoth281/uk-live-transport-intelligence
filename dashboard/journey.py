"""TfL station lookup and rail journey planning for the public dashboard."""
from datetime import datetime, timezone
from urllib.parse import quote

API = "https://api.tfl.gov.uk"
RAIL_MODES = "tube,dlr,overground,elizabeth-line,tram"


def _client(session):
    if session is None:
        import requests
        return requests
    return session


def _params(api_key):
    return {"app_key": api_key} if api_key else {}


def search_stations(query, *, api_key=None, session=None):
    query = query.strip()
    if not 2 <= len(query) <= 60:
        raise ValueError("Enter 2 to 60 characters for each station.")
    response = _client(session).get(
        f"{API}/StopPoint/Search/{quote(query, safe='')}",
        params={**_params(api_key), "modes": RAIL_MODES, "maxResults": 25},
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict) or not isinstance(payload.get("matches"), list):
        raise ValueError("TfL returned unexpected station search results.")
    stations, seen = [], set()
    for match in payload["matches"]:
        if not isinstance(match, dict):
            continue
        station_id, name = match.get("id"), match.get("name")
        if (not isinstance(station_id, str) or not isinstance(name, str)
                or not station_id or not name or station_id in seen):
            continue
        seen.add(station_id)
        stations.append({"id": station_id, "name": name})
    return stations


def normalise_journeys(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("journeys"), list):
        raise ValueError("TfL did not return journey options for those stations.")
    result = []
    for journey in payload["journeys"][:5]:
        if not isinstance(journey, dict) or not isinstance(journey.get("legs"), list):
            continue
        legs = []
        for leg in journey["legs"]:
            if not isinstance(leg, dict):
                continue
            route_options = leg.get("routeOptions") or []
            route = route_options[0] if route_options and isinstance(route_options[0], dict) else {}
            mode = leg.get("mode") or {}
            instruction = leg.get("instruction") or {}
            departure = leg.get("departurePoint") or {}
            arrival = leg.get("arrivalPoint") or {}
            path = leg.get("path") or {}
            stops = path.get("stopPoints") or []
            disruptions = leg.get("disruptions") or []
            works = leg.get("plannedWorks") or []
            legs.append({
                "mode": str(mode.get("name") or "Travel"),
                "line": str(route.get("name") or ""),
                "line_id": str((route.get("lineIdentifier") or {}).get("id") or ""),
                "from": str(departure.get("commonName") or departure.get("name") or "Start"),
                "to": str(arrival.get("commonName") or arrival.get("name") or "Destination"),
                "duration": leg.get("duration") if isinstance(leg.get("duration"), int) else None,
                "instruction": str(instruction.get("summary") or ""),
                "stops": [str(p.get("name")) for p in stops if isinstance(p, dict) and p.get("name")][:30],
                "disrupted": bool(leg.get("isDisrupted") or disruptions or works),
                "alerts": [str(d.get("description") or d.get("summary")) for d in disruptions
                           if isinstance(d, dict) and (d.get("description") or d.get("summary"))][:3]
                          + [str(w.get("description")) for w in works
                             if isinstance(w, dict) and w.get("description")][:2],
            })
        if not legs:
            continue
        rail_legs = [leg for leg in legs if leg["mode"].lower() != "walking"]
        result.append({
            "duration": journey.get("duration") if isinstance(journey.get("duration"), int) else None,
            "departure": journey.get("startDateTime"),
            "arrival": journey.get("arrivalDateTime"),
            "changes": max(0, len(rail_legs) - 1),
            "disrupted": any(leg["disrupted"] for leg in legs),
            "legs": legs,
        })
    return result


def fetch_journeys(from_id, to_id, *, api_key=None, session=None):
    # Only station IDs from the search result should be sent here.
    if not all(isinstance(value, str) and 2 <= len(value) <= 60
               and value.replace("-", "").isalnum() for value in (from_id, to_id)):
        raise ValueError("Choose stations from the search results.")
    if from_id == to_id:
        raise ValueError("Choose two different stations.")
    response = _client(session).get(
        f"{API}/Journey/JourneyResults/{quote(from_id, safe='')}/to/{quote(to_id, safe='')}",
        params={**_params(api_key), "mode": RAIL_MODES},
        timeout=15,
    )
    response.raise_for_status()
    retrieved_at = datetime.now(timezone.utc)
    return normalise_journeys(response.json()), retrieved_at


def fetch_line_status(line_ids, *, api_key=None, session=None):
    allowed = sorted({line_id for line_id in line_ids if isinstance(line_id, str)
                      and 1 <= len(line_id) <= 30 and line_id.replace("-", "").isalnum()})
    if not allowed:
        return {}
    response = _client(session).get(
        f"{API}/Line/{','.join(allowed)}/Status",
        params=_params(api_key), timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError("TfL returned unexpected line status data.")
    statuses = {}
    for item in payload:
        if not isinstance(item, dict) or item.get("id") not in allowed:
            continue
        descriptions = [str(s.get("statusSeverityDescription")) for s in item.get("lineStatuses", [])
                        if isinstance(s, dict) and s.get("statusSeverityDescription")]
        reasons = [str(s.get("reason")) for s in item.get("lineStatuses", [])
                   if isinstance(s, dict) and s.get("reason")]
        statuses[item["id"]] = {"status": ", ".join(dict.fromkeys(descriptions)) or "Unknown",
                                "reason": " ".join(dict.fromkeys(reasons))}
    return statuses
