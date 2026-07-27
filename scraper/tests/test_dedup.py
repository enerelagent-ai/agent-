"""Unit tests for the two-stage duplicate scorer, including the labeled fixture."""

import json
from pathlib import Path

from scraper.dedup import (
    AUTO_RESOLVE_THRESHOLD,
    are_candidates,
    classify_pair,
    group_pairs,
    normalize_title_tokens,
    photo_count_similarity,
    pick_canonical,
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


def test_group_pairs_merges_transitively() -> None:
    groups = group_pairs([(1, 2), (2, 3), (5, 6)])
    assert sorted(groups, key=min) == [{1, 2, 3}, {5, 6}]
    assert group_pairs([]) == []


def test_pick_canonical_prefers_completeness_then_recency_then_id() -> None:
    complete = {"id": 1, "price": 1.0, "area_sqm": 50.0, "rooms": 2, "posted_at": "2026-07-01T00:00"}
    sparse_newer = {"id": 2, "price": 1.0, "area_sqm": None, "rooms": None, "posted_at": "2026-07-20T00:00"}
    assert pick_canonical([complete, sparse_newer]) == 1  # completeness beats recency

    older = dict(complete, id=3, posted_at="2026-06-01T00:00")
    assert pick_canonical([complete, older]) == 1  # equal completeness -> newer wins

    twin = dict(complete, id=9)
    assert pick_canonical([complete, twin]) == 9  # full tie -> highest id, deterministic


def test_true_distinct_pairs_are_never_auto_resolved() -> None:
    """No genuinely-distinct pair may reach the 'duplicate' (auto-resolve)
    tier — a false positive here silently merges two different listings.
    Landing in 'possible_duplicate' (human review) is acceptable."""
    pairs = json.loads(FIXTURE.read_text())
    for pair in pairs:
        if pair["label"] != "distinct":
            continue
        status = classify_pair(pair["a"], pair["b"])
        assert status != "duplicate", f"would wrongly auto-merge: {pair['note']}"


def test_true_duplicates_are_never_silently_lost() -> None:
    """No genuine duplicate may be classified 'distinct' — it must at least
    reach 'possible_duplicate' so a human can still catch it."""
    pairs = json.loads(FIXTURE.read_text())
    for pair in pairs:
        if pair["label"] != "duplicate":
            continue
        status = classify_pair(pair["a"], pair["b"])
        assert status != "distinct", f"lost a real duplicate: {pair['note']}"


def test_auto_resolve_tier_has_no_false_positives_in_fixture() -> None:
    """The >= AUTO_RESOLVE_THRESHOLD tier is acted on without review, so it
    must have perfect precision on the labeled set pulled from the real
    36,666-listing scrape."""
    pairs = json.loads(FIXTURE.read_text())
    auto_resolved = [p for p in pairs if classify_pair(p["a"], p["b"]) == "duplicate"]
    assert auto_resolved, "fixture should contain some auto-resolve-tier pairs"
    wrong = [p for p in auto_resolved if p["label"] != "duplicate"]
    assert not wrong, f"auto-resolve tier has false positives: {[p['note'] for p in wrong]}"


def test_possible_duplicate_tier_is_where_precision_is_lowest() -> None:
    """Sanity check on the tier design: false positives in the fixture
    should score below AUTO_RESOLVE_THRESHOLD (i.e. land in review, not
    auto-resolve) — confirms 0.80 is a meaningful cut point, not arbitrary."""
    pairs = json.loads(FIXTURE.read_text())
    false_positive_scores = [
        score_pair(p["a"], p["b"])["total"] for p in pairs
        if p["label"] == "distinct" and are_candidates(p["a"], p["b"])
    ]
    assert false_positive_scores, "fixture should contain blocked-past false positives"
    assert max(false_positive_scores) < AUTO_RESOLVE_THRESHOLD
