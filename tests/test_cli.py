import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from pullthrough import cli


class CliTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.config = os.path.join(self.dir.name, "narratives.json")
        with open(self.config, "w", encoding="utf-8") as handle:
            json.dump({"narratives": [{"id": "delivery", "name": "Delivery", "pillars": [
                {"id": "disbursed", "keywords": ["disbursed"]},
                {"id": "beneficiaries", "keywords": ["households"]}]}]}, handle)
        self.articles = os.path.join(os.path.dirname(__file__), "fixtures", "articles.json")
        self.out = os.path.join(self.dir.name, "out")
        self.db = os.path.join(self.dir.name, "p.db")

    def tearDown(self):
        self.dir.cleanup()

    def run_cli(self, *args):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = cli.main(list(args))
        return code, buffer.getvalue()

    def test_run_writes_report_and_json(self):
        code, out = self.run_cli("run", "--config", self.config, "--articles", self.articles,
                                 "--out", self.out, "--db", self.db, "--day", "2026-11-12", "--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["day"], "2026-11-12")
        self.assertEqual(payload["articles"], 5)
        self.assertTrue(os.path.exists(os.path.join(self.out, "pullthrough.md")))

    def test_missing_config_exits_two(self):
        code, _ = self.run_cli("run", "--config", os.path.join(self.dir.name, "nope.json"),
                               "--articles", self.articles, "--db", self.db)
        self.assertEqual(code, 2)

    def test_trend_reads_the_archive(self):
        self.run_cli("run", "--config", self.config, "--articles", self.articles,
                     "--out", self.out, "--db", self.db, "--day", "2026-11-12")
        code, out = self.run_cli("trend", "--db", self.db, "--config", self.config)
        self.assertEqual(code, 0)
        self.assertIn("Delivery", out)


if __name__ == "__main__":
    unittest.main()
