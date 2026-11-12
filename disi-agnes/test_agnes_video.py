"""Offline tests: do not call Agnes APIs, spend credits, or publish."""
import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("agnes_video.py")
spec = importlib.util.spec_from_file_location("disi_agnes_bridge", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestAgnesBridge(unittest.TestCase):
    def test_model_is_free_only(self):
        self.assertEqual(mod.MODEL, "agnes-video-2.5-flash")

    def test_extract_task_id(self):
        self.assertEqual(mod.extract_video_id({"data": {"video_id": "abc123"}}), "abc123")
        with self.assertRaises(RuntimeError):
            mod.extract_video_id({})

    def test_completed_response_formats(self):
        self.assertEqual(mod.result_status({"status": "completed", "url": "https://cdn.example.com/v.mp4"}),
                         ("completed", "https://cdn.example.com/v.mp4"))
        self.assertEqual(mod.result_status({"data": {"status": "completed", "metadata": {"url": "https://cdn.example.com/v.mp4"}}})[0],
                         "completed")

    def test_body_error_even_when_http_was_200(self):
        with self.assertRaises(RuntimeError):
            mod.result_status({"status": "queued", "error": {"code": "video_queue_full"}})

    def test_download_url_security(self):
        for value in ("http://example.com/a.mp4", "https://127.0.0.1/a.mp4",
                      "https://localhost/a.mp4", "file:///etc/passwd"):
            with self.assertRaises(ValueError, msg=value):
                mod.public_https(value)
        self.assertEqual(mod.public_https("https://cdn.example.com/a.mp4"),
                         "https://cdn.example.com/a.mp4")

    def test_dry_run_no_key(self):
        env = os.environ.copy()
        env.pop("AGNES_API_KEY", None)
        env["VIDEO_PROMPT"] = "A cinematic aerial view of a fictional city at dawn"
        proc = subprocess.run([sys.executable, str(SCRIPT), "--dry-run", "--seconds", "5"],
                              env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["dry_run"])
        self.assertNotIn(env["VIDEO_PROMPT"], proc.stdout)

    def test_execute_requires_secret(self):
        env = os.environ.copy()
        env.pop("AGNES_API_KEY", None)
        env["VIDEO_PROMPT"] = "A cinematic aerial view of a fictional city at dawn"
        proc = subprocess.run([sys.executable, str(SCRIPT), "--execute", "--seconds", "5"],
                              env=env, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Missing AGNES_API_KEY", proc.stderr)


if __name__ == "__main__":
    unittest.main()
