from scripts.dry_run_verified_complex_match_backfill import classify_row


def _row(**overrides):
    row = {
        "listing_id": 1,
        "source_url": "test://legacy",
        "title": "Нархан хотхонд 2 өрөө байр",
        "description": None,
        "district": "Хан-Уул",
        "is_active": True,
        "assigned_complex_id": 10,
        "assigned_canonical": "Нархан",
        "allowed_districts": ["Хан-Уул"],
        "has_exact_override": False,
    }
    row.update(overrides)
    return row


def test_verified_unit_is_only_automatic_pilot_bucket() -> None:
    result = classify_row(_row())
    assert result["bucket"] == "eligible_approved_pilot"
    assert result["proposed_review_status"] == "approved"
    assert result["relation"] == "unit"


def test_unregistered_unit_stays_pending() -> None:
    result = classify_row(_row(allowed_districts=None))
    assert result["bucket"] == "unit_unregistered_manual_review"
    assert result["proposed_review_status"] == "pending"


def test_safe_inactive_assignment_is_separate_from_active_pilot() -> None:
    result = classify_row(_row(is_active=False))
    assert result["bucket"] == "eligible_inactive_history"
    assert result["proposed_review_status"] == "approved"


def test_district_mismatch_stays_pending_without_text_or_override() -> None:
    result = classify_row(_row(district="Баянзүрх"))
    assert result["bucket"] == "district_mismatch_manual_review"


def test_explicit_verified_district_text_passes_source_dropdown_conflict() -> None:
    result = classify_row(
        _row(district="Баянзүрх", description="ХУД-15-р хороонд байрлалтай")
    )
    assert result["bucket"] == "eligible_approved_pilot"


def test_landmark_and_extractor_disagreement_never_auto_approve() -> None:
    landmark = classify_row(_row(title="Нархан хойно байр зарна"))
    disagreement = classify_row(_row(title="Рапид хотхонд байр зарна"))
    assert landmark["bucket"] == "landmark_manual_review"
    assert disagreement["bucket"] == "extractor_disagrees_manual_review"
    assert landmark["proposed_review_status"] == "pending"
    assert disagreement["proposed_review_status"] == "pending"
