"""No-network tests for DISI book marketing draft workflow."""
from __future__ import annotations
from datetime import date, timedelta
from pathlib import Path
import sys
import tempfile
import unittest
from copy import deepcopy

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "disi-book-marketing"))
from marketing import (load_catalog, plan_campaigns, campaign_url,
                       site, export, start_monday)


class DISIBookMarketingTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_catalog()

    def test_books_metadata_and_links(self):
        titles = {x["slug"]: x for x in self.catalog["books"]}
        self.assertEqual(set(titles), {"alepo", "jartum"})
        self.assertEqual(titles["alepo"]["edition_ids"][0]["isbn13"], "9798167321427")
        self.assertIn("9781326492946", [e["isbn13"] for e in titles["jartum"]["edition_ids"]])
        self.assertIn("lulu.com", titles["jartum"]["purchase_links"][0]["url"])

    def test_unsafe_store_rejected(self):
        book = deepcopy(self.catalog)
        book["books"][0]["purchase_links"][0]["url"] = "https://evil.example/checkout"
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "catalog.json"
            import json
            path.write_text(json.dumps(book), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_catalog(path)

    def test_four_weeks_and_no_duplicate_post(self):
        plans = plan_campaigns(self.catalog, date(2026, 11, 16))
        self.assertEqual(len(plans), 28)
        self.assertEqual(len({p["id"] for p in plans}), 28)
        self.assertEqual({p["book"] for p in plans}, {"alepo", "jartum"})
        self.assertEqual({p["platform"] for p in plans},
                         {"linkedin", "facebook", "youtube", "tiktok", "instagram", "x", "pinterest"})
        self.assertTrue(all(p["status"] == "DRAFT_REVIEW_ONLY" for p in plans))
        self.assertTrue(all(p["publication_enabled"] is False for p in plans))
        self.assertTrue(all(p["sales"] is None and p["revenue_eur"] is None for p in plans))

    def test_video_requires_ten_languages_and_outro(self):
        plans = plan_campaigns(self.catalog, date(2026, 11, 16))
        video = [p for p in plans if p["format"] == "video"]
        self.assertEqual(len(video), 12)
        self.assertTrue(all("10 real voice tracks" in p["media_requirement"] for p in video))
        self.assertTrue(all("10 synced subtitles" in p["media_requirement"] for p in video))
        self.assertTrue(all("V6 outro" in p["media_requirement"] for p in video))

    def test_x_copy_max_length(self):
        plans = plan_campaigns(self.catalog, date(2026, 11, 16))
        self.assertTrue(all(len(p["copy_es"]) <= 280 for p in plans if p["platform"] == "x"))

    def test_link_tracking_only_when_real_site_url_supplied(self):
        url = campaign_url("https://books.example.org/landing?src=x", "youtube", "alepo", "w1-2")
        self.assertIn("utm_source=youtube", url)
        self.assertIn("utm_content=alepo_w1-2", url)
        self.assertIn("src=x", url)
        with self.assertRaises(ValueError):
            plan_campaigns(self.catalog, date(2026, 11, 16), "http://not-secure.site")
        plans = plan_campaigns(self.catalog, date(2026, 11, 16))
        self.assertFalse(any("utm_campaign" in p["destination_url"] for p in plans))

    def test_monday_start_and_28_day_bound(self):
        self.assertEqual(start_monday(date(2026, 11, 11)), date(2026, 11, 16))
        self.assertEqual(start_monday(date(2026, 11, 16)), date(2026, 11, 16))
        plans = plan_campaigns(self.catalog, date(2026, 11, 16))
        self.assertTrue(all(date(2026, 11, 16) <= date.fromisoformat(p["date_local"])
                            < date(2026, 11, 16) + timedelta(days=28) for p in plans))
        with self.assertRaises(ValueError):
            plan_campaigns(self.catalog, date(2026, 11, 17))

    def test_site_and_campaign_export_no_network(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            site(self.catalog, root / "site")
            plans = plan_campaigns(self.catalog, date(2026, 11, 16))
            export(plans, root / "campaigns")
            html = (root / "site" / "index.html").read_text(encoding="utf-8")
            self.assertIn("ALEPO", html)
            self.assertIn("JARTUM", html)
            self.assertIn("www.lulu.com", html)
            self.assertIn("https://www.amazon.es/dp/B0HQ58WM3Y", html)
            self.assertNotIn("google-analytics", html)
            self.assertTrue((root / "site" / "_headers").exists())
            import json
            bundle = json.loads((root / "campaigns" / "campaigns.json").read_text(encoding="utf-8"))
            self.assertEqual(bundle["total_drafts"], 28)
            self.assertFalse(bundle["autopublish"])
            self.assertEqual(bundle["sale_metrics"], "UNKNOWN_NOT_ZERO")


if __name__ == "__main__":
    unittest.main()
