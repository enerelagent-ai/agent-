"""Unit tests for the read-only Session 0 audit helpers."""

from scripts.audit_complex_district_distribution import (
    _assigned_landmark_evidence,
    _khoroo_from_address,
)


def test_khoroo_from_address_accepts_source_address_order() -> None:
    assert _khoroo_from_address("Хан-Уул, Хан-Уул, Хороо 15") == "15"


def test_khoroo_from_address_accepts_title_style_order() -> None:
    assert _khoroo_from_address("ХУД, 17-р хороо") == "17"
    assert _khoroo_from_address("БЗД 26 хороо") == "26"


def test_khoroo_from_address_returns_none_without_numbered_khoroo() -> None:
    assert _khoroo_from_address("Хан-Уул, River Garden") is None
    assert _khoroo_from_address(None) is None


def test_assigned_landmark_evidence_handles_genitive_suffix() -> None:
    assert (
        _assigned_landmark_evidence(
            "Сансар home plaza-ийн хажууд 46мкв оффис", "Home Plaza"
        )
        == "хажууд"
    )


def test_assigned_landmark_evidence_does_not_flag_unit_relation() -> None:
    assert _assigned_landmark_evidence("Home Plaza-д 3 өрөө байр", "Home Plaza") is None
