"""Offline invariants of the ten-language motion-graphics compositor."""
import json
import unittest
from pathlib import Path

from scripts.mn_short_motion import MOTION, VOICES, cue, named, split_sentences


class MotionPilotTests(unittest.TestCase):
    def test_video_branding_includes_disi_without_old_spacing(self):
        source = (MOTION / "src" / "NewsVideo.jsx").read_text(encoding="utf-8")
        index = (MOTION / "src" / "index.jsx").read_text(encoding="utf-8")
        self.assertIn('const PRODUCT_NAME = "MNShort";', source)
        self.assertIn('const EDITORIAL_SIGNATURE = "Media News by DISI";', source)
        self.assertIn("{EDITORIAL_SIGNATURE}", source)
        self.assertIn("{PRODUCT_NAME}", source)
        self.assertNotIn(">MN SHORT<", source)
        self.assertIn('storyTitle: "MNShort"', index)

    def test_exact_person_name_not_brand(self):
        self.assertTrue(named("The CEO Jensen Huang joined Nvidia", "Jensen Huang"))
        self.assertFalse(named("Nvidia launched a new chip", "Jensen Huang"))
        self.assertFalse(named("Jensen introduced one person named Huang", "Jensen Huang"))

    def test_ten_languages_have_same_demo_storyboard_size(self):
        demos = json.loads((MOTION / "demo_translations.json").read_text(encoding="utf-8"))
        self.assertEqual(set(demos), set(VOICES))
        self.assertEqual(len(demos["es"]), 8)
        for lang, sentences in demos.items():
            self.assertEqual(len(sentences), 8, lang)
            self.assertTrue(all(len(s) > 8 for s in sentences), lang)

    def test_demo_scenes_do_not_use_generic_portrait_for_named_person(self):
        original = json.loads((MOTION / "demo_translations.json").read_text(encoding="utf-8"))["es"]
        source = {"title": "Demostración", "description": "Demostración", "publisher": "Media News"}
        kinds = [cue(s, i, len(original), source, [], set(), demo=True)["kind"] for i,s in enumerate(original)]
        self.assertEqual(kinds, ["headline", "person", "source", "metric", "person", "place", "headline", "outro"])
        portrait = cue(original[1], 1, len(original), source, [], set(), demo=True)
        self.assertEqual(portrait["person"], "Jensen Huang")
        self.assertNotIn("image", portrait)

    def test_canonical_narration_is_split_into_sentences(self):
        self.assertEqual(split_sentences("A factual statement. Another statement."), ["A factual statement.", "Another statement."])


if __name__ == "__main__":
    unittest.main()
