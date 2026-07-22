"""Unit tests for the two-stage duplicate scorer, including the labeled fixture."""

import json
from pathlib import Path

from scraper.dedup import (
    are_candidates,
    classify_pair,
    normalize_title_tokens,
    photo_count_similarity,
    price_proximity,
    score_pair,
    title_similarity,
)

FIXTURE = Path(__file__).parent / "fixtures" / "labeled_pairs.json"


def test_title_normalization_unifies_area_units_and_lookalikes() -> None:
    assert normalize_title_tokens("213мкв байр") == {"213м2"}
    assert normalize_title_tokens("213м² х 213мк х 213m2") == {"213м2", "х"}
    assert normalize_title_tokens("55,8мкв") == {"55.8м2"}
    # latin lookalikes fold onto cyrillic: "xopoo" (latin) == "хороо" (cyrillic)
    assert normalize_title_tokens("6-p xopoo") == normalize_title_tokens("6-р хороо")


def test_title_similarity_on_real_repost_titles() -> None:
    sim = title_similarity(
        "Худ river plaza 213мкв 5 өрөө",
        "River plaza 5 өрөө 213мк орон сууц",
    )
    assert sim >= 0.7  # word order and filler words must not matter


def test_price_proximity_edges() -> None:
    assert price_proximity(100.0, 100.0) == 1.0
    assert price_proximity(100.0, 120.0) == 0.0  # beyond 15% gap
    assert price_proximity(None, 100.0) == 0.5  # missing -> neutral


def test_photo_count_similarity_edges() -> None:
    assert photo_count_similarity(8, 16) == 0.5
    assert photo_count_similarity(None, 7) == 0.5


def test_blocking_rules() -> None:
    base = {
        "listing_type": "rent", "property_type": "Орон сууц түрээслүүлнэ",
        "district": "Баянзүрх", "rooms": 2, "area_sqm": 50.0,
    }
    assert are_candidates(base, dict(base, area_sqm=51.0))  # rounding survives
    assert not are_candidates(base, dict(base, area_sqm=70.0))  # different unit
    assert not are_candidates(base, dict(base, rooms=3))
    assert not are_candidates(base, dict(base, district="Хан-Уул"))
    assert not are_candidates(base, dict(base, listing_type="sale"))
    # unknown rooms on one side must not block (specs vary by listing type)
    assert are_candidates(dict(base, rooms=None), base)


def test_labeled_fixture_is_classified_perfectly() -> None:
    pairs = json.loads(FIXTURE.read_text())
    assert len(pairs) >= 14
    for pair in pairs:
        verdict = classify_pair(pair["a"], pair["b"])
        assert verdict == pair["label"], (
            f"misclassified: {pair['note']} "
            f"(scores={score_pair(pair['a'], pair['b'])})"
        )


def test_duplicates_and_distinct_are_separated_with_margin() -> None:
    """The closest distinct candidate must stay clearly below the weakest duplicate."""
    pairs = json.loads(FIXTURE.read_text())
    dup_scores = [score_pair(p["a"], p["b"])["total"]
                  for p in pairs if p["label"] == "duplicate"]
    distinct_scores = [score_pair(p["a"], p["b"])["total"]
                       for p in pairs
                       if p["label"] == "distinct" and are_candidates(p["a"], p["b"])]
    assert min(dup_scores) - max(distinct_scores) >= 0.2
