from scripts.mn_short_image_search import exact_subject_match, valid_public_url, words


def test_person_name_must_be_complete_and_contiguous():
    assert exact_subject_match("Jensen Huang at Nvidia GTC 2026", "Jensen Huang")
    assert exact_subject_match("Photographie de Jensén Huáng", "Jensen Huang")
    assert not exact_subject_match("Nvidia logo on a wall", "Jensen Huang")
    assert not exact_subject_match("Jensen on stage, Huang in audience", "Jensen Huang")
    assert not exact_subject_match("Jensen Ackles and Huang", "Jensen Huang")


def test_urls_must_be_https_and_external():
    assert valid_public_url("https://commons.wikimedia.org/wiki/File:example.jpg")
    assert not valid_public_url("http://example.com/photo.jpg")
    assert not valid_public_url("https://127.0.0.1/test.png")
    assert not valid_public_url("file:///etc/passwd")
