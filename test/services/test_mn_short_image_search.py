from scripts.mn_short_image_search import editorial_subjects, exact_subject_match, valid_public_url


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


def test_editorial_subjects_are_dynamic_and_source_grounded():
    editorial = {
        "source": {"title": "Jensen Huang is the subject of Nvidia report",
                   "description": "The company Nvidia named Jensen Huang in its announcement."},
        "generated": {
            "script_es": "Jensen Huang aparece en una noticia sobre Nvidia.",
            "script_en": "Jensen Huang was named in an Nvidia report.",
            "visual_subjects": [
                {"name": "Jensen Huang", "kind": "person", "context": "Nvidia"},
                {"name": "Nvidia", "kind": "organization", "context": "chips"},
                {"name": "Elon Musk", "kind": "person", "context": "Tesla"},
                {"name": "businessman", "kind": "person", "context": "generic"},
            ],
        },
    }
    subjects = editorial_subjects(editorial)
    assert [s["name"] for s in subjects] == ["Jensen Huang", "Nvidia"]


def test_editorial_subjects_change_when_news_changes():
    editorial = {
        "source": {"title": "Satya Nadella announces Microsoft research",
                   "description": "Microsoft CEO Satya Nadella presented the research."},
        "generated": {
            "script_es": "Satya Nadella presenta la investigación de Microsoft.",
            "script_en": "Microsoft CEO Satya Nadella presented research.",
            "visual_subjects": [
                {"name": "Satya Nadella", "kind": "person", "context": "Microsoft"}
            ],
        },
    }
    assert editorial_subjects(editorial)[0]["name"] == "Satya Nadella"


def test_when_no_named_subject_is_grounded_search_headline_without_person_claim():
    editorial = {
        "source": {"title": "A strange spacecraft arrives", "publisher": "Example News"},
        "generated": {"script_es": "Un extraño vehículo espacial ha llegado.",
                      "script_en": "An unusual spacecraft has arrived.",
                      "visual_subjects": [
                          {"name": "Fictitious Person", "kind": "person", "context": ""}
                      ]},
    }
    subjects = editorial_subjects(editorial)
    assert len(subjects) == 1
    assert subjects[0]["kind"] == "event"
    assert subjects[0]["name"] == "A strange spacecraft arrives"
