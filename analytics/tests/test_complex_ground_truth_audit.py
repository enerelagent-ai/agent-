"""Unit tests for the Phase 1 CSV ground-truth audit rules."""

from scripts.audit_complex_ground_truth import classify_row, normalize


LABELS = {"Akoya Residence", "Aqua Garden", "Buti Town", "Sky Garden Residence"}


def _row(label: str) -> dict[str, str]:
    return {"Хотхон": label, "Холбоос": f"https://example.test/{normalize(label)}"}


def test_normalize_handles_case_punctuation_and_unicode_width() -> None:
    assert normalize("Ocean's １０ Apartment") == "oceans10apartment"


def test_classify_row_confirms_canonical_name_in_title() -> None:
    result = classify_row(_row("Buti Town"), "BUTI-TOWN хотхонд 3 өрөө", LABELS)
    assert result["status"] == "confirmed_positive"
    assert result["evidence"] == "canonical_in_title"


def test_classify_row_confirms_reviewed_transliteration_alias() -> None:
    result = classify_row(_row("Buti Town"), "Бүти таун хотхонд 3 өрөө", LABELS)
    assert result["status"] == "confirmed_positive"
    assert result["evidence"] == "reviewed_alias_in_title"


def test_classify_row_detects_reused_url_naming_another_complex() -> None:
    result = classify_row(_row("Akoya Residence"), "Акуа гарден хотхонд 3 өрөө", LABELS)
    assert result["status"] == "reused_url_mismatch"


def test_classify_row_keeps_landmark_as_negative_not_complex() -> None:
    result = classify_row(
        _row("115-р сургуулийн хажууд"),
        "115-р сургуулийн хажууд 3 өрөө",
        LABELS,
    )
    assert result["status"] == "confirmed_negative"
    assert result["entity_type"] == "landmark"


def test_classify_row_excludes_insufficient_evidence_from_gold_set() -> None:
    result = classify_row(_row("Buti Town"), "ХУД 3 өрөө байр", LABELS)
    assert result["status"] == "excluded_insufficient_evidence"

