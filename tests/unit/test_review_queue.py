from app.services.review.queue import build_decision_review_queue, build_uncoded_provision_queue


def test_review_queues_split_uncoded_and_pending_decisions() -> None:
    provisions = [{"provision_id": "p1"}, {"provision_id": "p2"}]
    decisions = [
        {"provision_id": "p1", "reviewer_status": "approved"},
        {"provision_id": "p3", "reviewer_status": "provisional"},
    ]

    uncoded = build_uncoded_provision_queue(provisions, decisions)
    pending = build_decision_review_queue(decisions)

    assert uncoded == [{"provision_id": "p2"}]
    assert pending == [{"provision_id": "p3", "reviewer_status": "provisional"}]
