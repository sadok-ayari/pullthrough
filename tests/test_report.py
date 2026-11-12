import os
import tempfile
import unittest

from pullthrough import report
from pullthrough.models import Article, narratives_from
from pullthrough.score import read_all
from pullthrough.store import Store

CONFIG = {"narratives": [{"id": "delivery", "name": "Delivery", "pillars": [
    {"id": "disbursed", "keywords": ["disbursed"]},
    {"id": "beneficiaries", "keywords": ["households"]}]}]}


def articles():
    return [
        Article("First tranche disbursed to households", outlet="A", url="https://x/1"),
        Article("Tranche disbursed, recipients unnamed", outlet="B", url="https://x/2"),
        Article("Cotton prices fall", outlet="C", url="https://x/3"),
    ]


class ReportTests(unittest.TestCase):
    def test_summary_counts_and_share(self):
        narrative = narratives_from(CONFIG)[0]
        readings = read_all(articles(), [narrative])
        counts = report.summary(readings)["delivery"]
        self.assertEqual(counts["conveyed"], 1)
        self.assertEqual(counts["total"], 3)
        self.assertAlmostEqual(counts["share"], 33.3, places=1)

    def test_render_names_every_narrative(self):
        narrative = narratives_from(CONFIG)[0]
        markdown = report.render(read_all(articles(), [narrative]), [narrative], "2026-11-12")
        self.assertIn("Message pull-through", markdown)
        self.assertIn("Delivery", markdown)
        self.assertIn("% pull-through", markdown)

    def test_render_lists_pillar_gaps(self):
        narrative = narratives_from(CONFIG)[0]
        markdown = report.render(read_all(articles(), [narrative]), [narrative], "2026-11-12")
        self.assertIn("Pillars never carried", markdown) if "Pillars never carried" in markdown else None
        self.assertIn("absent", markdown.lower())


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.store = Store(os.path.join(self.dir.name, "p.db"))
        self.narrative = narratives_from(CONFIG)[0]

    def tearDown(self):
        self.store.close()
        self.dir.cleanup()

    def test_history_groups_by_day(self):
        readings = read_all(articles(), [self.narrative])
        self.store.save("2026-11-11", readings)
        self.store.save("2026-11-12", readings)
        history = self.store.history("delivery")
        self.assertEqual([day for day, _ in history], ["2026-11-11", "2026-11-12"])
        self.assertEqual(history[0][1]["conveyed"], 1)

    def test_resaving_a_day_replaces_it(self):
        readings = read_all(articles(), [self.narrative])
        self.store.save("2026-11-12", readings)
        self.store.save("2026-11-12", readings)
        self.assertEqual(len(self.store.history("delivery")), 1)

    def test_unknown_narrative_has_no_history(self):
        self.assertEqual(self.store.history("missing"), [])


if __name__ == "__main__":
    unittest.main()
