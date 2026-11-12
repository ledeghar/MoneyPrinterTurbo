import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from copy import deepcopy
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "disi-book-marketing" / "acquisition"))
from acquisition import read_targets, pitch, build_pack


class BuyerAcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.targets = read_targets()

    def test_public_provenance_and_no_private_data(self):
        self.assertGreaterEqual(len(self.targets), 8)
        self.assertEqual(len({x["id"] for x in self.targets}), len(self.targets))
        self.assertTrue(all(x["url"].startswith("https://") and x["evidence"] for x in self.targets))

    def test_pitches_are_for_editorial_fit_not_paid_reviews(self):
        t = next(x for x in self.targets if x["id"] == "la-trinchera")
        text = pitch(t)
        self.assertIn("NO ENVIADO", text)
        self.assertIn("ALEPO", text)
        self.assertIn("JARTUM", text)
        self.assertIn("lulu.com", text)
        self.assertIn("previa aceptación", text)

    def test_community_onboarding_not_spam(self):
        t = next(x for x in self.targets if x["id"] == "goodreads-author")
        text = pitch(t)
        self.assertIn("TAREA DE ALTA EN PLATAFORMA", text)
        self.assertIn("titular", text)

    def test_unknown_contacts_fail_closed(self):
        path = Path(__file__).resolve().parents[1] / "disi-book-marketing" / "acquisition" / "targets.json"
        import json
        data = json.loads(path.read_text(encoding="utf8"))
        data["targets"][0]["contact"] = "automatic_dm_blast"
        with TemporaryDirectory() as temp:
            f = Path(temp) / "targets.json"
            f.write_text(json.dumps(data), encoding="utf8")
            with self.assertRaises(ValueError):
                read_targets(f)

    def test_outputs_uncontacted_and_no_sales_claims(self):
        with TemporaryDirectory() as tmp:
            folder = Path(tmp) / "prospects"
            stats = build_pack(self.targets, folder)
            self.assertEqual(stats["qualified_public_channels"], len(self.targets))
            self.assertEqual(stats["messages_sent"], 0)
            self.assertIsNone(stats["sales_attributed"])
            self.assertEqual(stats["status"], "MANUAL_APPROVAL_REQUIRED")
            csv_data = (folder / "qualified-prospects.csv").read_text(encoding="utf-8-sig")
            self.assertIn("NOT_CONTACTED", csv_data)
            self.assertNotIn("SENT", csv_data.replace("NOT_CONTACTED", ""))
            self.assertTrue((folder / "la-trinchera.txt").is_file())


if __name__ == "__main__":
    unittest.main()
