import json
import os
import unittest

from pullthrough.models import Article, articles_from, narratives_from
from pullthrough.text import dismissed, hits, quoted_lines, strip_html


class TextTests(unittest.TestCase):
    def test_strip_html(self):
        self.assertEqual(strip_html("<p>Hello&nbsp;<b>world</b></p>"), "Hello&nbsp; world")

    def test_hits_are_word_bounded(self):
        self.assertEqual(hits("the disbursed tranche", ["disbursed"]), ["disbursed"])
        self.assertEqual(hits("undisbursed funds", ["disbursed"]), [])

    def test_hits_are_case_insensitive(self):
        self.assertEqual(hits("Ministry Leads", ["ministry"]), ["ministry"])

    def test_dismiss_near_keyword(self):
        self.assertTrue(dismissed("Ministry scraps the guarantee plan", ["guarantee"]))

    def test_dismiss_far_from_keyword_is_ignored(self):
        long_text = "the guarantee scheme continues " + ("filler " * 40) + "a separate programme was scrapped"
        self.assertFalse(dismissed(long_text, ["guarantee"]))

    def test_quoted_lines_touch_a_pillar(self):
        text = 'He said \u201cthe first tranche is disbursed\u201d and \u201cprices are falling\u201d.'
        self.assertEqual(quoted_lines(text, ["tranche"]), ["the first tranche is disbursed"])


class ModelTests(unittest.TestCase):
    def test_narratives_from_config(self):
        config = {"narratives": [{"id": "n1", "pillars": [{"id": "p1", "keywords": ["a"]}]}]}
        narratives = narratives_from(config)
        self.assertEqual(narratives[0].name, "n1")
        self.assertEqual(narratives[0].keywords, ["a"])

    def test_optional_pillar(self):
        config = {"narratives": [{"id": "n1", "pillars": [
            {"id": "p1", "keywords": ["a"]}, {"id": "p2", "keywords": ["b"], "required": False}]}]}
        self.assertFalse(narratives_from(config)[0].pillars[1].required)

    def test_article_key_prefers_url(self):
        self.assertEqual(Article(title="T", url="https://x/1").key, "https://x/1")
        self.assertEqual(Article(title="Title Only").key, "title only")

    def test_reads_coverage_radar_export(self):
        payload = {"stories": [{"lead_title": "A story", "url": "https://x/2", "outlets": ["Wire"],
                                "published": "2026-11-11T00:00:00+00:00"}]}
        path = os.path.join(os.path.dirname(__file__), "fixtures", "_stories.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        try:
            articles = articles_from(path)
        finally:
            os.remove(path)
        self.assertEqual(articles[0].title, "A story")
        self.assertEqual(articles[0].outlet, "Wire")

    def test_reads_article_list(self):
        path = os.path.join(os.path.dirname(__file__), "fixtures", "articles.json")
        self.assertEqual(len(articles_from(path)), 5)


if __name__ == "__main__":
    unittest.main()
