"""Offline unit tests for the Facebook page identity preflight."""
import io
import json
import unittest

from scripts.mn_facebook_page_check import verify_page


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


class FacebookPagePreflightTests(unittest.TestCase):
    def test_token_never_appears_in_url(self):
        def mocked(request, timeout):
            self.assertEqual(timeout, 20)
            self.assertNotIn("TOP_SECRET", request.full_url)
            self.assertEqual(
                request.get_header("Authorization"), "Bearer TOP_SECRET"
            )
            return Response(json.dumps({
                "id": "123456789", "name": "Media News HQ",
                "link": "https://www.facebook.com/medianewshq"
            }).encode())
        page = verify_page("TOP_SECRET", "123456789", opener=mocked)
        self.assertEqual(page["name"], "Media News HQ")

    def test_wrong_page_rejected(self):
        def mocked(request, timeout):
            return Response(b'{"id":"987654321","name":"Different Page"}')
        with self.assertRaisesRegex(RuntimeError, "do not match"):
            verify_page("FAKE", "123456789", opener=mocked)

    def test_missing_token_rejected(self):
        with self.assertRaisesRegex(ValueError, "FACEBOOK_PAGE_ACCESS_TOKEN"):
            verify_page("", "123456789")

    def test_non_numeric_id_rejected(self):
        with self.assertRaisesRegex(ValueError, "FACEBOOK_PAGE_ID"):
            verify_page("TOKEN", "medianewshq")


if __name__ == "__main__":
    unittest.main()
