"""No-network tests of the MN Short YouTube uploader."""
from unittest.mock import MagicMock, patch

import pytest

from scripts.mn_short_youtube_direct import (
    get_access_token, upload_one_unlisted, validate_upload_url,
)


def test_refresh_access_token(monkeypatch):
    for name in ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN"):
        monkeypatch.setenv(name, "test_only")
    session = MagicMock()
    session.post.return_value.status_code = 200
    session.post.return_value.json.return_value = {"access_token": "placeholder"}
    assert get_access_token(session) == "placeholder"
    assert session.post.call_args.kwargs["data"]["grant_type"] == "refresh_token"


def test_upload_url_rejects_non_google_hosts():
    with pytest.raises(RuntimeError):
        validate_upload_url("https://example.com/upload/youtube/v3/videos?upload_id=abc")


def test_upload_is_unlisted(tmp_path):
    video = tmp_path / "test.mp4"
    video.write_bytes(b"example MP4 bytes")
    session = MagicMock()
    start = MagicMock(status_code=200)
    start.headers = {"Location": "https://www.googleapis.com/upload/youtube/v3/videos?upload_id=abc"}
    finish = MagicMock(status_code=200)
    finish.json.return_value = {"id": "example123"}
    session.post.return_value = start
    session.put.return_value = finish
    with patch("scripts.mn_short_youtube_direct.get_access_token", return_value="placeholder"):
        video_id = upload_one_unlisted(
            session, video, title="MN Short test", description="Test only"
        )
    assert video_id == "example123"
    assert session.post.call_args.kwargs["json"]["status"]["privacyStatus"] == "unlisted"
    assert session.put.call_args.kwargs["headers"]["Content-Type"] == "video/mp4"
