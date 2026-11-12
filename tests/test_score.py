import unittest

from pullthrough.models import Article, narratives_from
from pullthrough.score import read

CONFIG = {
    "narratives": [{
        "id": "delivery",
        "name": "The money reaches the ground",
        "pillars": [
            {"id": "disbursed", "keywords": ["disbursed", "first tranche"]},
            {"id": "beneficiaries", "keywords": ["households", "farmers"]},
            {"id": "timeline", "keywords": ["on schedule"]},
        ],
    }]
}


class ScoreTests(unittest.TestCase):
    def setUp(self):
        self.narrative = narratives_from(CONFIG)[0]

    def article(self, title, summary=""):
        return Article(title=title, outlet="Wire", url="https://x/1", summary=summary)

    def test_absent_when_no_pillar(self):
        reading = read(self.article("Cotton prices fall"), self.narrative)
        self.assertEqual(reading.state, "absent")

    def test_conveyed_when_all_pillars_and_no_reversal(self):
        reading = read(self.article(
            "First tranche disbursed to farming households on schedule",
            "Officials confirmed the money reached cooperatives."), self.narrative)
        self.assertEqual(reading.state, "conveyed")
        self.assertTrue(reading.in_title)
        self.assertEqual(reading.pillars_missing, [])

    def test_mentioned_when_a_required_pillar_is_missing(self):
        reading = read(self.article("Disbursed at last", "The first tranche arrived."), self.narrative)
        self.assertEqual(reading.state, "mentioned")
        self.assertIn("beneficiaries", reading.pillars_missing)

    def test_distorted_when_reversal_sits_beside_a_pillar(self):
        reading = read(self.article(
            "Ministry scraps plan after first tranche disbursed"), self.narrative)
        self.assertEqual(reading.state, "distorted")

    def test_single_pillar_is_not_conveyance(self):
        config = {"narratives": [{"id": "n", "pillars": [{"id": "p", "keywords": ["disbursed"]}]}]}
        reading = read(self.article("Disbursed, finally"), narratives_from(config)[0])
        self.assertEqual(reading.state, "mentioned")
        self.assertTrue(any("at least two" in r for r in reading.reasons))

    def test_reasons_are_always_printed(self):
        reading = read(self.article("First tranche disbursed to farming households on schedule"),
                       self.narrative)
        self.assertGreaterEqual(len(reading.reasons), 2)

    def test_prominence_doubles_weight(self):
        """A message in the headline counts for more than the same words in paragraph nine."""
        with_title = read(self.article("First tranche disbursed to farming households on schedule"),
                          self.narrative)
        body_only = read(self.article("Aid update", "The first tranche was disbursed to farming households on schedule"),
                         self.narrative)
        self.assertEqual(with_title.state, "conveyed")
        self.assertEqual(body_only.state, "conveyed")
        self.assertEqual(with_title.weight, 2 * body_only.weight)


if __name__ == "__main__":
    unittest.main()
