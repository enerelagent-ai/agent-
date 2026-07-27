"""Second-stage duplicate scoring for candidate listing pairs.

Two-stage design (validated on the labeled fixture in tests/fixtures/):
stage 1 blocks obvious non-candidates on hard attributes; stage 2 scores the
survivors on soft signals. Deliberately excluded as evidence:

- contact_phone: real duplicates are posted by different agents, while one
  agent posts many distinct properties (verified both ways on live data).
- exact coordinates: sellers who skip the map get a shared per-khoroo
  default pin, so identical coords occur on unrelated buildings.
"""

import re
from datetime import datetime
from typing import Any, Literal

# Sellers mix latin lookalikes into cyrillic words ("13-p xopoo"); folding
# them keeps token comparison consistent. Purely-latin words are folded on
# both sides equally, so their similarity is unaffected.
_LOOKALIKE_FOLD = str.maketrans("abcehkmoptxy", "авсенкмортху")

# High-frequency filler words that carry no identity information.
_TITLE_STOPWORDS = {
    "зарна", "худалдана", "түрээслүүлнэ", "хөлслүүлнэ", "хөлслүүлэнэ",
    "орон", "сууц", "байр", "өрөө", "хотхон", "хотхонд", "хотхоны",
}

_AREA_UNIT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:мкв|мкб|м²|м2|мк\b|m2)")
_DECIMAL_COMMA_RE = re.compile(r"(\d+),(\d+)")
_NON_WORD_RE = re.compile(r"[^\w.]+")

# Stage-1 blocking: areas further apart than this are different units.
AREA_BAND = 0.10
# Stage-2 signal scales, tuned on the labeled fixture.
PRICE_FULL_MISMATCH = 0.15   # relative price gap treated as "completely different"
DATE_FULL_MISMATCH_DAYS = 30.0
WEIGHTS = {"title": 0.45, "price": 0.35, "photos": 0.08, "posted": 0.12}

# Confidence tiers (Week 4 spec, item A.1). Below CANDIDATE_THRESHOLD a pair
# is not a match at all. Validated on 20 pairs pulled from the full
# 36,666-listing / 48,855-match scrape (2026-07-27, see tests/fixtures/
# labeled_pairs.json): the [0.90, 1.0] band was 10/10 genuine duplicates,
# while [0.60, 0.70) was only ~8/10 — false positives cluster near the old
# single threshold, so scores there are surfaced for human review rather
# than auto-merged.
CANDIDATE_THRESHOLD = 0.60
AUTO_RESOLVE_THRESHOLD = 0.80

# Kept as an alias: matches.py's recording cutoff is "is this worth storing
# as a candidate at all", which is CANDIDATE_THRESHOLD, not the auto-resolve
# bar.
DUPLICATE_THRESHOLD = CANDIDATE_THRESHOLD

MatchStatus = Literal["duplicate", "possible_duplicate", "distinct"]


def normalize_title_tokens(title: str | None) -> set[str]:
    """Tokenize a title for comparison: lowercase, fold latin lookalikes,
    unify area spellings (мкв/м²/мк -> м2), drop punctuation and stopwords."""
    if not title:
        return set()
    text = title.lower().translate(_LOOKALIKE_FOLD)
    text = _DECIMAL_COMMA_RE.sub(r"\1.\2", text)
    text = _AREA_UNIT_RE.sub(r"\1м2", text)
    text = _NON_WORD_RE.sub(" ", text)
    return {t for t in text.split() if t and t not in _TITLE_STOPWORDS}


def title_similarity(a: str | None, b: str | None) -> float:
    """Jaccard similarity of normalized title tokens (0..1)."""
    ta, tb = normalize_title_tokens(a), normalize_title_tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def price_proximity(a: float | None, b: float | None) -> float:
    """1.0 for equal prices, falling to 0.0 at PRICE_FULL_MISMATCH relative gap.

    Missing prices give a neutral 0.5 rather than pretending either extreme.
    """
    if not a or not b:
        return 0.5
    gap = abs(a - b) / max(a, b)
    return max(0.0, 1.0 - gap / PRICE_FULL_MISMATCH)


def photo_count_similarity(a: int | None, b: int | None) -> float:
    """Ratio of photo counts (0..1); weak evidence — agents shoot their own
    photos of the same unit, so counts legitimately differ between reposts."""
    if not a or not b:
        return 0.5
    return min(a, b) / max(a, b)


def posted_date_proximity(a: str | None, b: str | None) -> float:
    """1.0 for same-day posts, falling to 0.0 at DATE_FULL_MISMATCH_DAYS apart."""
    if not a or not b:
        return 0.5
    try:
        da, db = datetime.fromisoformat(a), datetime.fromisoformat(b)
    except ValueError:
        return 0.5
    days = abs((da - db).total_seconds()) / 86400.0
    return max(0.0, 1.0 - days / DATE_FULL_MISMATCH_DAYS)


def are_candidates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Stage-1 blocking on hard attributes.

    listing_type, property_type and district must match; rooms must match
    when both are known; areas must lie within AREA_BAND when both are known
    (loose enough to survive seller rounding like 51 vs 50).
    """
    for field in ("listing_type", "property_type", "district"):
        if a.get(field) != b.get(field) or a.get(field) is None:
            return False
    if a.get("rooms") is not None and b.get("rooms") is not None and a["rooms"] != b["rooms"]:
        return False
    area_a, area_b = a.get("area_sqm"), b.get("area_sqm")
    if area_a and area_b and abs(area_a - area_b) / max(area_a, area_b) > AREA_BAND:
        return False
    return True


def score_pair(a: dict[str, Any], b: dict[str, Any]) -> dict[str, float]:
    """Stage-2 soft-signal scores for a candidate pair, plus the weighted total."""
    signals = {
        "title": title_similarity(a.get("title"), b.get("title")),
        "price": price_proximity(a.get("price"), b.get("price")),
        "photos": photo_count_similarity(a.get("n_photos"), b.get("n_photos")),
        "posted": posted_date_proximity(a.get("posted_at"), b.get("posted_at")),
    }
    signals["total"] = sum(WEIGHTS[k] * v for k, v in signals.items() if k in WEIGHTS)
    return signals


def match_status(score: float) -> MatchStatus:
    """Confidence tier for an already-computed score (Week 4 spec A.1).

    >= AUTO_RESOLVE_THRESHOLD: safe to auto-resolve as a Duplicate.
    [CANDIDATE_THRESHOLD, AUTO_RESOLVE_THRESHOLD): Possible Duplicate — a
    human review candidate, not auto-merged (this is where false positives
    concentrate; see the module-level note on the fixture validation).
    Below CANDIDATE_THRESHOLD: distinct.
    """
    if score >= AUTO_RESOLVE_THRESHOLD:
        return "duplicate"
    if score >= CANDIDATE_THRESHOLD:
        return "possible_duplicate"
    return "distinct"


def classify_pair(a: dict[str, Any], b: dict[str, Any]) -> MatchStatus:
    """Full pipeline for one pair: block, then tier the score."""
    if not are_candidates(a, b):
        return "distinct"
    return match_status(score_pair(a, b)["total"])


# Fields whose presence makes a listing more useful to analytics; used to
# choose the canonical member of a duplicate group.
_COMPLETENESS_FIELDS = ("price", "area_sqm", "rooms")


def group_pairs(pairs: list[tuple[int, int]]) -> list[set[int]]:
    """Merge matched pairs into duplicate groups (connected components),
    so A~B and B~C land in one {A, B, C} group."""
    parent: dict[int, int] = {}

    def find(x: int) -> int:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in pairs:
        parent[find(a)] = find(b)
    groups: dict[int, set[int]] = {}
    for node in parent:
        groups.setdefault(find(node), set()).add(node)
    return list(groups.values())


def pick_canonical(rows: list[dict[str, Any]]) -> int:
    """Pick the listing analytics should keep from one duplicate group.

    Order of preference: most complete data (non-null price/area/rooms),
    then most recently posted, then highest id — deterministic so repeated
    runs agree.
    """
    def preference(row: dict[str, Any]) -> tuple[int, str, int]:
        completeness = sum(row.get(f) is not None for f in _COMPLETENESS_FIELDS)
        return (completeness, row.get("posted_at") or "", row["id"])

    return max(rows, key=preference)["id"]
