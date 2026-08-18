"""Tests for category-independent complex extraction and normalization."""

import json
from pathlib import Path

from analytics.complexes import extract_complex, normalize_complex_name
from scripts.backfill_complexes import apply_backfill


FIXTURE = Path(__file__).parent / "fixtures" / "complex_ground_truth.json"
LANDMARK_FIXTURE = Path(__file__).parent / "fixtures" / "landmark_relabel_69.json"


def test_normalize_complex_name_unifies_case_spacing_and_punctuation() -> None:
    assert normalize_complex_name("  SKY-Garden  Residence ") == "sky garden residence"


def test_extracts_reviewed_cyrillic_alias_without_rooms() -> None:
    match = extract_complex("Худ бүти таун хотхонд худалдааны талбай")
    assert match is not None
    assert match.canonical_name == "Buti Town"
    assert match.relation == "unit"


def test_extracts_trigger_name_for_unknown_complex() -> None:
    match = extract_complex("ХУД Шинэ Өргөө хотхонд оффис")
    assert match is not None
    assert match.canonical_name == "Шинэ Өргөө"
    assert match.trigger.startswith("хотхон")


def test_numbered_neighbourhood_is_not_a_complex() -> None:
    assert extract_complex("БГД 3,4-р хороололд 2 өрөө") is None


def test_landmark_reference_is_not_a_unit_relation() -> None:
    match = extract_complex("Элеганс хотхоны баруун талд 2 айлын газар")
    assert match is not None
    assert match.relation == "landmark"


def test_session0_exception_aliases_select_the_actual_unit() -> None:
    romana = extract_complex("Төв цэнгэлдэхийн хойно романа резиденс 150мкв оффис")
    assert romana is not None
    assert romana.canonical_name == "Romana residence"
    assert romana.relation == "unit"

    dream = extract_complex(
        "Green house баруун талд humana-тай шинэ мөрөөдөл хотхонд 2 өрөө"
    )
    assert dream is not None
    assert dream.canonical_name == "Зайсан шинэ мөрөөдөл"
    assert dream.relation == "unit"


def test_ground_truth_metrics_are_reported_separately() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    positives = [row for row in fixture["rows"] if row["status"] == "confirmed_positive"]
    negatives = [row for row in fixture["rows"] if row["status"] == "confirmed_negative"]
    stale = [row for row in fixture["rows"] if row["status"] == "reused_url_mismatch"]

    correct = sum(
        (match := extract_complex(row["current_title"])) is not None
        and match.relation == "unit"
        and match.canonical_name == row["csv_label"]
        for row in positives
    )
    false_positives = sum(
        (match := extract_complex(row["current_title"])) is not None
        and match.relation == "unit"
        for row in negatives
    )
    stale_label_reused = sum(
        (match := extract_complex(row["current_title"])) is not None
        and match.canonical_name == row["csv_label"]
        for row in stale
    )

    # Phase 1 acceptance principle: favor precision and never learn a stale
    # URL's old label. Exact thresholds are regression gates, not claims over
    # the 597 source-unavailable CSV rows.
    assert correct / len(positives) >= 0.95
    assert false_positives == 0
    assert stale_label_reused == 0


def test_landmark_after_catches_the_69_session0_cue_words() -> None:
    """Regression fixture for the Session 0 audit (2026-08-17): 69 listings
    that were assigned complex_id via a unit match, but whose title was
    actually a landmark reference the old _LANDMARK_AFTER pattern missed
    ("хойно", "баруун/зvvн талд", a genitive suffix before the cue, ...).
    Manually labeled by reading every row (see the fixture's own file), not
    inferred from a majority vote -- that would be circular (Session 0.5's
    stated risk).

    label == "landmark_reassign": a different, already-canonical complex is
        named in the same title; the fixed extractor must resolve THAT one
        as the unit match (not just flag the old assignment as landmark).
    label == "landmark_none" / "ambiguous": no canonical complex names the
        real unit (a generic phrase, a building number, or a name not yet
        in CANONICAL_COMPLEXES); the fixed extractor must at least stop
        resolving it as a unit match of the wrongly-assigned complex.

    3 known remaining gaps (asserted as an explicit exception list, not
    silently skipped): missing alias entries unrelated to the landmark-cue
    fix itself (a Cyrillic transliteration, a short-form alias) -- tracked
    here so a future alias addition is expected to shrink this list, not
    grow it.
    """
    fixture = json.loads(LANDMARK_FIXTURE.read_text(encoding="utf-8"))
    known_remaining_gaps = {61758, 35527, 29890}  # missing-alias, not landmark-cue, gaps

    failures = []
    for row in fixture["rows"]:
        if row["listing_id"] in known_remaining_gaps:
            continue
        match = extract_complex(row["title"])
        now_relation = match.relation if match else None
        now_canonical = match.canonical_name if match else None
        if row["label"] == "landmark_reassign":
            ok = now_relation == "unit" and now_canonical == row["suggested_canonical"]
        else:
            ok = not (now_relation == "unit" and now_canonical == row["assigned_canonical"])
        if not ok:
            failures.append((row["listing_id"], row["label"], now_relation, now_canonical, row["title"]))

    assert not failures, f"{len(failures)} regression(s): {failures}"


def test_apply_backfill_links_listing_to_canonical_complex(cur) -> None:
    cur.execute(
        """
        INSERT INTO listings (source, source_url, title, dedup_hash)
        VALUES ('unegui', 'test://complex-backfill',
                'Бүти таун хотхонд худалдааны талбай', 'complex-test')
        RETURNING id
        """
    )
    listing_id = cur.fetchone()["id"]

    assert apply_backfill(cur, [(listing_id, "Buti Town")]) == 1
    cur.execute(
        """
        SELECT c.canonical_name
        FROM listings l JOIN complexes c ON c.id = l.complex_id
        WHERE l.id = %s
        """,
        (listing_id,),
    )
    assert cur.fetchone()["canonical_name"] == "Buti Town"
