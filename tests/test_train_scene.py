import unittest
from datetime import datetime, timezone

from dashboard.train_scene import render_train_scene


class TrainSceneTests(unittest.TestCase):
    def test_escapes_untrusted_tfl_text_and_uses_expected_time(self):
        scene = render_train_scene("Victoria", "<script>alert(1)</script>", [{
            "destination": "</script><img src=x onerror=alert(1)>",
            "platform": "Southbound",
            "expected_arrival": "2026-09-26T20:00:00Z",
            "minutes": 2.0,
        }], datetime(2026, 9, 26, 19, 58, tzinfo=timezone.utc))
        self.assertNotIn("</script><img", scene)
        self.assertNotIn("<script>alert(1)</script>", scene)
        self.assertIn("\\u003c/script\\u003e", scene)
        self.assertIn("2026-09-26T20:00:00Z", scene)
        self.assertIn("not GPS or actual train position", scene)


if __name__ == "__main__":
    unittest.main()
