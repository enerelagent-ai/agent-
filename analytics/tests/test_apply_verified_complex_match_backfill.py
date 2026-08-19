import pytest

from analytics.complexes import COMPLEX_EXTRACTOR_VERSION
from scripts.apply_verified_complex_match_backfill import (
    SCRIPT_NOTE,
    apply_rows,
    eligible_rows,
    prepare_rows,
)


def test_expected_count_is_a_hard_apply_gate(cur) -> None:
    with pytest.raises(ValueError, match="eligible count changed"):
        eligible_rows(cur, expected_count=-1)


def test_prepare_and_apply_verified_match_is_idempotent(cur) -> None:
    cur.execute("SELECT id FROM complexes WHERE canonical_name = 'Нархан'")
    complex_id = cur.fetchone()["id"]
    cur.execute(
        """
        INSERT INTO listings
            (source, source_url, title, dedup_hash, district, complex_id, is_active)
        VALUES
            ('unegui', 'test://legacy-match-apply', 'Нархан хотхонд 2 өрөө байр',
             'legacy-match-apply', 'Хан-Уул', %s, true)
        RETURNING id
        """,
        (complex_id,),
    )
    listing_id = cur.fetchone()["id"]
    row = {
        "listing_id": listing_id,
        "assigned_complex_id": complex_id,
        "matched_alias": "Нархан",
        "relation": "unit",
        "confidence": 0.99,
        "evidence_text": "Нархан хотхонд 2 өрөө байр",
        "extractor_version": COMPLEX_EXTRACTOR_VERSION,
    }

    prepared, skipped = prepare_rows(cur, [row])
    assert skipped == 0
    assert apply_rows(cur, prepared) == 1
    prepared_again, skipped_again = prepare_rows(cur, [row])
    assert prepared_again == []
    assert skipped_again == 1

    cur.execute(
        """
        SELECT relation, review_status, reviewer_note, reviewed_at, is_current
        FROM listing_complex_matches
        WHERE listing_id = %s
        """,
        (listing_id,),
    )
    match = cur.fetchone()
    assert match["relation"] == "unit"
    assert match["review_status"] == "approved"
    assert match["reviewer_note"] == SCRIPT_NOTE
    assert match["reviewed_at"] is not None
    assert match["is_current"] is True

