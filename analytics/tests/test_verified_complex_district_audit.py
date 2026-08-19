"""Rendering contract for the verified-location read-only audit."""

from scripts.audit_verified_complex_districts import classify_mismatch, render_markdown


def test_render_markdown_includes_allowlist_and_mismatch_evidence() -> None:
    summary = [{
        "canonical_name": "Рапид",
        "allowed_districts": ["Хан-Уул"],
        "assigned_count": 2,
        "mismatch_count": 1,
    }]
    mismatches = [{
        "listing_id": 7,
        "assigned_complex": "Рапид",
        "allowed_districts": ["Хан-Уул"],
        "district": "Баянзүрх",
        "address": "Баянзүрх, Хороо 15",
        "title": "Рапид хороололд байр",
        "description": None,
        "is_active": True,
        "review_status": "unresolved",
    }]

    report = render_markdown(summary, mismatches, "2026-01-01T00:00:00+00:00")

    assert "READ-ONLY" in report
    assert "Рапид" in report
    assert "id=7" in report
    assert "Баянзүрх" in report


def test_classify_mismatch_accepts_explicit_verified_district_text() -> None:
    row = {
        "allowed_districts": ["Хан-Уул"],
        "title": "ХУД-15 хороо Рапид хотхонд байр",
        "description": "",
    }
    assert classify_mismatch(row) == "source_conflict_with_explicit_verified_text"
