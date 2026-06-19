from app.services.segmentation.basic import segment_document_pages, segment_page, provisions_to_csv


def test_segment_page_detects_article_heading() -> None:
    text = """
Article 1: Cooperation
The Parties shall cooperate on critical raw materials supply chains, including
mapping, investment facilitation, environmental standards, and research partnerships.

Article 2: Review
The Parties will meet annually to review progress under this memorandum and identify
new areas for implementation.
"""

    provisions = segment_page("doc1", 1, text)

    assert len(provisions) == 2
    assert provisions[0]["article_number"] == "1"
    assert provisions[0]["section_title"] == "Cooperation"
    assert provisions[0]["page_start"] == 1


def test_segment_document_pages_and_export_csv() -> None:
    record = {
        "document_id": "doc1",
        "pages": [
            {
                "page_number": 1,
                "text": (
                    "The Parties intend to establish a working group on critical minerals. "
                    "The working group will prepare a roadmap and monitor implementation."
                ),
            }
        ],
    }

    provisions = segment_document_pages(record)
    csv_text = provisions_to_csv(provisions)

    assert len(provisions) == 1
    assert provisions[0]["segmentation_method"] == "paragraph"
    assert "crm_candidate" not in csv_text
    assert "working group" in csv_text
