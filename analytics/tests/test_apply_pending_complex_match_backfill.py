import pytest

from analytics.complexes import COMPLEX_EXTRACTOR_VERSION
from scripts.apply_pending_complex_match_backfill import (
    SCRIPT_NOTE_PREFIX,
    apply_rows,
    pending_rows,
    prepare_rows,
)


def test_pending_counts_are_a_hard_apply_gate(cur) -> None:
    with pytest.raises(ValueError, match="pending bucket counts changed"):
        pending_rows(cur, expected_unit_unregistered=-1, expected_landmark=-1)


def test_pending_evidence_is_idempotent_and_never_approved(cur) -> None:
    cur.execute("SELECT id FROM complexes WHERE canonical_name = 'Home Plaza'")
    complex_id = cur.fetchone()["id"]
    cur.execute(
        """
        INSERT INTO listings
            (source, source_url, title, dedup_hash, district, complex_id, is_active)
        VALUES
            ('unegui', 'test://pending-match-apply', 'Home Plaza хойно байр',
             'pending-match-apply', 'Хан-Уул', %s, true)
        RETURNING id
        """,
        (complex_id,),
    )
    listing_id = cur.fetchone()["id"]
    row = {
        "listing_id": listing_id,
        "assigned_complex_id": complex_id,
        "matched_alias": "Home Plaza",
        "relation": "landmark",
        "confidence": 0.55,
        "evidence_text": "Home Plaza хойно байр",
        "extractor_version": COMPLEX_EXTRACTOR_VERSION,
        "bucket": "landmark_manual_review",
    }

    prepared, skipped = prepare_rows(cur, [row])
    assert skipped == 0
    assert apply_rows(cur, prepared) == 1
    prepared_again, skipped_again = prepare_rows(cur, [row])
    assert prepared_again == []
    assert skipped_again == 1

    cur.execute(
        """
        SELECT review_status, reviewer_note, reviewed_at, is_current
        FROM listing_complex_matches WHERE listing_id = %s
        """,
        (listing_id,),
    )
    match = cur.fetchone()
    assert match["review_status"] == "pending"
    assert match["reviewer_note"] == SCRIPT_NOTE_PREFIX + row["bucket"]
    assert match["reviewed_at"] is None
    assert match["is_current"] is True

