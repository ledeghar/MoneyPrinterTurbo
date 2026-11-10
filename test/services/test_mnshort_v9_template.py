import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location("v9","scripts/mnshort_v9_template.py")
v9=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v9)

class TemplateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.master=Path(self.temp.name)/"fixture.mp4"
        self.master.write_bytes(b"0"*100001)
        self.probe={
            "format":{"duration":"54.773"},
            "streams":(
                [{"codec_type":"video","codec_name":"h264","width":720,"height":1280}]
                + [{"codec_type":"audio","codec_name":"aac","tags":{"language":iso}}
                   for _,iso in v9.LANGS]
                + [{"codec_type":"subtitle","codec_name":"mov_text","tags":{"language":iso}}
                   for _,iso in v9.LANGS])
        }

    def test_approved_reference_codes(self):
        self.assertEqual(len(v9.LANGS),10)
        self.assertEqual(v9.MAX_SECONDS,59.0)

    def test_valid_master_passes(self):
        with patch.object(v9,"probe",return_value=self.probe):
            result=v9.validate(self.master,check_signal=False)
        self.assertEqual(result["duration_seconds"],54.773)
        self.assertEqual(result["audio"],10)
        self.assertEqual(result["subtitle"],10)

    def test_rejects_silent_placeholder_tracks(self):
        broken=json.loads(json.dumps(self.probe))
        broken["streams"]=[x for x in broken["streams"] if x["codec_type"]!="audio"][0:1]+[
            {"codec_type":"audio","codec_name":"aac","tags":{"language":"spa"}}]+[
            x for x in broken["streams"] if x["codec_type"]=="subtitle"]
        with patch.object(v9,"probe",return_value=broken):
            with self.assertRaisesRegex(ValueError,"Require 1 video, 10 audios"):
                v9.validate(self.master,check_signal=False)

    def test_language_mismatch_rejected(self):
        broken=json.loads(json.dumps(self.probe))
        broken["streams"][2]["tags"]["language"]="spa"
        with patch.object(v9,"probe",return_value=broken):
            with self.assertRaisesRegex(ValueError,"unexpected language"):
                v9.validate(self.master,check_signal=False)

    def test_over_duration_is_error(self):
        broken=json.loads(json.dumps(self.probe))
        broken["format"]["duration"]="59.01"
        with patch.object(v9,"probe",return_value=broken):
            with self.assertRaisesRegex(ValueError,"duration"):
                v9.validate(self.master,check_signal=False)

    def test_reference_hash_guard(self):
        with patch.object(v9,"probe",return_value=self.probe):
            with self.assertRaisesRegex(ValueError,"SHA256"):
                v9.validate(self.master,approved=True,check_signal=False)

    def test_rejects_wrong_aspect_ratio(self):
        broken=json.loads(json.dumps(self.probe))
        broken["streams"][0]["width"]=1920
        broken["streams"][0]["height"]=1080
        with patch.object(v9,"probe",return_value=broken):
            with self.assertRaisesRegex(ValueError,"9:16"):
                v9.validate(self.master,check_signal=False)

if __name__=="__main__":
    unittest.main()
