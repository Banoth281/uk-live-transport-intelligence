import unittest

from dashboard.live_tfl import fetch_arrivals, normalise_arrivals


class LiveTfLTests(unittest.TestCase):
    def test_rejects_bad_predictions_and_sorts_by_station_then_wait(self):
        payload = [
            {"stationName": "Victoria", "timeToStation": 180, "destinationName": "Brixton"},
            {"stationName": "Victoria", "timeToStation": 60, "destinationName": "Brixton"},
            {"stationName": "Euston", "timeToStation": 90},
            {"stationName": "Victoria", "timeToStation": -10},
            {"stationName": "Victoria", "timeToStation": "soon"},
            {"stationName": "", "timeToStation": 10},
        ]
        rows = normalise_arrivals(payload)
        self.assertEqual([(r["station"], r["minutes"]) for r in rows],
                         [("Euston", 1.5), ("Victoria", 1.0), ("Victoria", 3.0)])
        self.assertEqual(rows[0]["platform"], "Not supplied")

    def test_requires_list_and_allowlisted_line(self):
        with self.assertRaises(ValueError):
            normalise_arrivals({"error": "unavailable"})
        with self.assertRaises(ValueError):
            fetch_arrivals("../other")

    def test_fetch_uses_timeout_and_records_retrieval_time(self):
        class Response:
            def raise_for_status(self):
                pass

            def json(self):
                return [{"stationName": "Pimlico", "timeToStation": 120}]

        class Session:
            def get(self, url, params, timeout):
                self_url = url
                assert self_url.endswith("/Line/victoria/Arrivals")
                assert params is None
                assert timeout == 10
                return Response()

        rows, retrieved_at = fetch_arrivals("victoria", session=Session())
        self.assertEqual(rows[0]["minutes"], 2)
        self.assertIsNotNone(retrieved_at.tzinfo)


if __name__ == "__main__":
    unittest.main()
