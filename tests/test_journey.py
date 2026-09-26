import unittest

from dashboard.journey import (JourneyDisambiguation, search_stations, fetch_journeys,
                               fetch_line_status, normalise_journeys)
from dashboard.journey_scene import render_journey_scene


class Response:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


class Session:
    def __init__(self, data):
        self.data = data
        self.calls = []

    def get(self, url, *, params, timeout):
        self.calls.append((url, params, timeout))
        return Response(self.data)


JOURNEYS = {"journeys": [{"duration": 12, "startDateTime": "2026-09-26T12:00:00+01:00",
    "arrivalDateTime": "2026-09-26T12:12:00+01:00", "legs": [{
        "mode": {"name": "tube"}, "routeOptions": [{"name": "District", "lineIdentifier": {"id": "district"}}],
        "departurePoint": {"commonName": "Westminster"}, "arrivalPoint": {"commonName": "Embankment"},
        "duration": 2, "instruction": {"summary": "Board the District line"},
        "path": {"stopPoints": [{"name": "Westminster"}, {"name": "Embankment"}]},
        "isDisrupted": False, "disruptions": [],
    }, {
        "mode": {"name": "walking"}, "departurePoint": {"commonName": "Embankment"},
        "arrivalPoint": {"commonName": "Charing Cross"}, "duration": 4,
        "disruptions": [{"description": "Avoid the south exit"}],
    }]}]}


class JourneyTests(unittest.TestCase):
    def test_station_lookup_uses_exact_ids_and_encodes_query(self):
        session = Session({"matches": [{"id": "940GZZLUWMS", "icsId": "1000266", "name": "Westminster"},
                                         {"id": "940GZZLUWMS", "name": "Westminster"},
                                         {"id": "", "name": "Invalid"}]})
        self.assertEqual(search_stations(" King's Cross ", session=session),
                         [{"id": "1000266", "name": "Westminster"}])
        self.assertIn("King%27s%20Cross", session.calls[0][0])
        self.assertEqual(session.calls[0][2], 10)
        self.assertIn("modes", session.calls[0][1])

    def test_journeys_and_disruption_are_normalised_without_guessing(self):
        session = Session(JOURNEYS)
        routes, retrieved = fetch_journeys("940GZZLUWMS", "940GZZLUBNK", session=session)
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["changes"], 0)
        self.assertTrue(routes[0]["disrupted"])
        self.assertEqual(routes[0]["legs"][0]["stops"], ["Westminster", "Embankment"])
        self.assertEqual(routes[0]["legs"][0]["line_id"], "district")
        self.assertEqual(routes[0]["legs"][1]["alerts"], ["Avoid the south exit"])
        self.assertTrue(retrieved.tzinfo)
        self.assertEqual(session.calls[0][2], 15)
        self.assertIn("/940GZZLUWMS/to/940GZZLUBNK", session.calls[0][0])

    def test_disambiguation_and_invalid_ids_are_explicit(self):
        with self.assertRaises(JourneyDisambiguation) as context:
            normalise_journeys({"fromLocationDisambiguation": {"disambiguationOptions": [
                {"parameterValue": "51.501,-0.123", "place": {"commonName": "Westminster Underground Station", "placeType": "StopPoint"}}
            ]}})
        self.assertEqual(context.exception.from_options[0]["name"], "Westminster Underground Station")
        self.assertEqual(context.exception.from_options[0]["value"], "51.501,-0.123")
        with self.assertRaises(ValueError):
            fetch_journeys("../admin", "940GZZLUBNK", session=Session(JOURNEYS))
        with self.assertRaises(ValueError):
            fetch_journeys("940GZZLUBNK", "940GZZLUBNK", session=Session(JOURNEYS))

    def test_line_status_and_scene_escape(self):
        session = Session([{"id": "district", "lineStatuses": [{"statusSeverityDescription": "Minor Delays",
                              "reason": "Signal fault"}]}])
        status = fetch_line_status(["district", "../bad"], session=session)
        self.assertEqual(status["district"]["status"], "Minor Delays")
        self.assertNotIn("bad", session.calls[0][0])
        route = normalise_journeys(JOURNEYS)[0]
        route["legs"][0]["instruction"] = "</script><img src=x>"
        route["legs"][0]["from"] = "</script><img src=x>"
        html = render_journey_scene(route, colours={"District": "#00782a"})
        self.assertNotIn("</script><img", html)
        self.assertIn("\\u003c/script\\u003e", html)
        self.assertIn("not a live train position", html)


if __name__ == "__main__":
    unittest.main()
