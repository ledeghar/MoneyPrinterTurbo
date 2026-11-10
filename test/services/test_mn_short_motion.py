"""Offline invariants of the ten-language motion-graphics compositor."""
import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.mn_short_motion import MOTION, VOICES, cue, named, split_sentences, boundary_to_timing, checked_commons_file


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

    def test_live_spanish_only_skips_nine_translations_and_tracks(self):
        from scripts import mn_short_motion as motion
        editorial = {
            "source": {
                "title": "Investigación tecnológica",
                "description": "La fuente describe una investigación tecnológica.",
                "publisher": "Ejemplo",
                "url": "https://example.org/report",
            },
            "generated": {
                "title_es": "Investigación tecnológica",
                "script_es": (
                    "La investigación aparece en una fuente publicada. "
                    "El informe describe sus resultados principales. "
                    "Todavía es necesario contrastar los datos."
                ),
                "visual_subjects": [],
            },
        }

        async def fake_voice(_text, _voice, path):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"fake audio for offline test")
            return [{"text": "Prueba", "start": 0.1, "end": 0.5}]

        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            with patch.object(motion, "PUBLIC", base / "public"), \
                    patch.object(motion, "PROPS", base / "props"), \
                    patch.object(motion, "OUTPUT", base / "output"), \
                    patch.object(motion, "synthesize", fake_voice), \
                    patch.object(motion, "voice_duration", return_value=1.5):
                asyncio.run(motion.build(editorial, "live", languages="es"))
                self.assertEqual(
                    sorted(p.name for p in motion.PROPS.glob("*.json")), ["es.json"]
                )
                contents = json.loads((motion.PROPS / "es.json").read_text(encoding="utf-8"))
                self.assertEqual(contents["language"], "es")
                self.assertEqual(len(contents["scenes"]), 3)
                metadata = json.loads(
                    (motion.OUTPUT / "editorial-y-creditos.json").read_text(encoding="utf-8")
                )
                self.assertEqual(metadata["languages"], ["es"])
                self.assertEqual(set(metadata["aligned_translations"]), {"es"})

    def test_edge_word_offsets_are_real_100ns_ticks_not_linear_averages(self):
        self.assertEqual(
            boundary_to_timing({"type": "WordBoundary", "text": "Huang", "offset": 12300000, "duration": 7000000}),
            {"text": "Huang", "start": 1.23, "end": 1.93}
        )
        self.assertIsNone(boundary_to_timing({"type": "audio", "data": b"MP3"}))

    def test_commons_licenses_and_full_name_are_required_for_actual_photograph(self):
        source = {
            "title": "File:Jensen Huang (cropped) (2024).jpg",
            "imageinfo": [{
                "thumburl": "https://upload.wikimedia.org/wikipedia/commons/thumb/jensen.jpg",
                "descriptionurl": "https://commons.wikimedia.org/wiki/File:Jensen_Huang_2024.jpg",
                "thumbwidth": 1000, "thumbheight": 1500,
                "extmetadata": {
                    "LicenseShortName": {"value": "CC BY 4.0"},
                    "Artist": {"value": "Peter Dasilva"},
                }
            }],
        }
        accepted = checked_commons_file(source, "Jensen Huang")
        self.assertEqual(accepted["identity_method"], "Commons exact-name filename")
        self.assertEqual(accepted["license"], "CC BY 4.0")
        self.assertIsNone(checked_commons_file(source, "Another Real Person"))
        bad = json.loads(json.dumps(source))
        bad["imageinfo"][0]["extmetadata"]["LicenseShortName"]["value"] = "All rights reserved"
        self.assertIsNone(checked_commons_file(bad, "Jensen Huang"))

    def test_named_person_without_verified_photo_stops_draft(self):
        from scripts import mn_short_motion as motion
        editorial = motion.demo_editorial()
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            with patch.object(motion, "PUBLIC", base / "public"), \
                    patch.object(motion, "PROPS", base / "props"), \
                    patch.object(motion, "OUTPUT", base / "output"), \
                    patch.object(motion, "save_commons_photo", return_value=None):
                with self.assertRaisesRegex(RuntimeError, "EDITORIAL PHOTO REQUIRED"):
                    asyncio.run(motion.build(editorial, "demo", languages="es"))

    def test_ten_audio_tracks_share_one_master_timeline_without_speed_changes(self):
        from scripts import mn_short_multiaudio as mux
        scenes = lambda durations: [
            {"kind":"headline","audio":"audio/sample.mp3","text":"La noticia.",
             "wordTimings":[{"text":"La","start":0.0,"end":0.1}],
             "durationFrames":int(d)} for d in durations
        ]
        packs = {
            lang: {"scenes": scenes([150,180] if lang == "de" else [120,170])}
            for lang, _iso, _name in mux.LANGS
        }
        self.assertEqual(mux.master_durations(packs), [150,180])
        self.assertEqual(mux.srt_clock(65.234), "00:01:05,234")
        with tempfile.TemporaryDirectory() as tmp:
            srt = Path(tmp) / "es.srt"
            mux.create_srt(packs["es"], [150,180], srt)
            lines = srt.read_text(encoding="utf-8-sig")
            self.assertIn("00:00:00,000 --> 00:00:05,000", lines)
            self.assertIn("00:00:05,000 --> 00:00:11,000", lines)
        self.assertEqual(len(mux.LANGS), 10)

    def test_canonical_narration_is_split_into_sentences(self):
        self.assertEqual(split_sentences("A factual statement. Another statement."), ["A factual statement.", "Another statement."])


if __name__ == "__main__":
    unittest.main()
