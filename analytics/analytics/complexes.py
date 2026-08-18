"""Conservative complex-name extraction from real-estate listing titles.

Known aliases win over trigger heuristics. The extractor is intentionally
category/room agnostic: Phase 1 found complex references in 14/15 canonical
property categories, including garages, offices, land, and retail listings.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable


COMPLEX_EXTRACTOR_VERSION = "complex-extractor-v2"


CANONICAL_COMPLEXES: tuple[str, ...] = (
    "Akoya Residence", "Alpha Zone", "Aqua Garden", "Arvai villa",
    "Buti Town", "Cozy Apartment", "Encanto Tower", "FLOWERS хотхон",
    "General Town", "Gerlug vista", "Global Town", "Hansvill",
    "Home Plaza", "Japan Town", "Jardin luxury residence", "KH apartment",
    "Khan Hills", "King Tower", "Mandal luxury residence", "Marshal Town",
    "Modun Town", "Nobles Residence", "Ocean's 10 apartment",
    "Pares Central Park", "Park Garden", "Regis Place", "River Tower",
    "River Plaza", "River Villa", "River Garden", "Romana residence",
    "Royal garden", "SS Garden", "Seven Star", "Silk road residence",
    "Sky Tower", "Sky Garden Residence", "Sn tower", "Solaris Residence",
    "Time Square", "Tokyo Town", "Vega City", "Winter Garden", "Агниста",
    "Академи 1", "Академи 2", "Гэгээнтэн", "Жаргалан",
    "Зайсан Green House", "Зайсан Энхжин", "Зайсан буянт",
    "Зайсан шинэ мөрөөдөл", "Ирээдүй", "Нархан", "Оддын хотхон",
    "Оргил Стар", "Рапид", "ТАЙЖ-12 апартмент", "Хүннү Плюс",
    "Хүннү 2222", "Цэнгэлдэх", "Цэцэг", "Шинэ туулын хөвөө хотхон",
    "Эрдэнийн Төгөл",
)

# Reviewed aliases from Phase 1. Canonical spelling is always included
# automatically, so only actual variants belong here.
COMPLEX_ALIASES: dict[str, tuple[str, ...]] = {
    "Akoya Residence": ("akoya tower", "akoyatower", "акояа тауэр", "акоя тауэр"),
    "Buti Town": ("бути таун", "бүти таун"),
    "Gerlug vista": ("гэрлүг виста",),
    "Global Town": ("глобал таун",),
    "Hansvill": ("хансвилл",),
    "Japan Town": ("жапан таун",),
    "Khan Hills": ("khan khills", "khankhills", "хан хиллс", "ханхиллс"),
    "King Tower": ("king taur", "кинг тауэр", "кинг таур"),
    "Marshal Town": ("marshall town", "маршал таун", "маршилл таун", "маршил таун"),
    "Modun Town": ("модун таун",),
    "Nobles Residence": ("nobles хотхон",),
    "Ocean's 10 apartment": ("ocean 10 apartment", "ocean 10 апартмент", "оcean 10 апартмент"),
    "Park Garden": ("парк гарден", "рark garden"),
    "Regis Place": ("regis palace", "рэжис плэйс"),
    "River Garden": ("ривер гарден",),
    "River Plaza": ("ривер плаза",),
    "River Villa": ("ривер вилла",),
    "Romana residence": ("романа резиденс",),
    "Sky Garden Residence": ("sky garden", "skygarden", "скай гарден"),
    "Sn tower": ("sn тауэр",),
    "Solaris Residence": ("solaris plus residence", "solaris plus"),
    "Tokyo Town": ("tokya town", "токио таун"),
    "Vega City": ("вега сити",),
    "Жаргалан": ("jargalan",),
    "Зайсан Green House": ("green house",),
    "Зайсан шинэ мөрөөдөл": ("шинэ мөрөөдөл",),
    "Зайсан Энхжин": ("энхжин хотхон",),
    "Рапид": ("хурд рапид", "хурд хороолол"),
    "Хүннү 2222": ("хүннү-2222", "хүннү-222", "hunnu 2222", "hunnu2222"),
    "Хүннү Плюс": ("хүннү plus", "хүннү пласт", "hunnu plus"),
}

# Session 0 audit (2026-08-17): the original two-branch pattern only
# reached "хажууд/ойролцоо/харалдаа" directly after an alias (branch 2) --
# missing "хойно", "баруун/зvvн талд", "баруун урд/хойд", "зvvн урд/хойд",
# "эсрэг талд", and a genitive suffix (-ын/-ийн/-ы/-ий/-ны/-ний) between the
# alias and the cue (e.g. "home plaza-ийн хойно"). Real-DB impact was
# severe, not cosmetic: 69/4,024 assigned listings were actually landmark
# references to a DIFFERENT complex or no complex at all, concentrated in
# a few names -- Home Plaza alone was 28/55 (51%) misclassified as unit
# because nearly every one of its landmark mentions used "хойно" or a
# "баруун/зvvн талд" variant this pattern didn't reach.
_LANDMARK_CUE = (
    r"(?:хажууд|ойролцоо|харалдаа|ард|урд|хойно|"
    r"баруун(?:\s+урд|\s+хойд|\s+талд)?|зүүн(?:\s+урд|\s+хойд|\s+талд)?|"
    r"эсрэг\s+талд|замын\s+эсрэг\s+талд)"
)
_LANDMARK_AFTER = re.compile(
    r"(?:"
    r"(?:хотхон|хороолол|residence|garden|town|apartment)(?:ы|ий|ын|ийн|оос|аас|ээс|д)?"
    r"\s+" + _LANDMARK_CUE +
    r"|\s*(?:(?:ын|ийн|ы|ий|ны|ний)\s+)?" + _LANDMARK_CUE +
    r")\b",
    re.IGNORECASE,
)
_NUMBERED_NEIGHBOURHOOD = re.compile(r"\b\d+(?:\s*[,/]\s*\d+)?\s*(?:-?р)?\s*хороолол", re.IGNORECASE)
_TRIGGER = re.compile(
    r"(?P<name>(?:[\w'-]+[ \t]+){1,4})"
    r"(?P<trigger>хотхон(?:д|ы|оос|доо|ууд)?|хороолол(?:д|ын|оос|той)?|"
    r"residences?|village|gardens?|town|apartments?|апартмент(?:ад|эд|д|ын)?)\b",
    re.IGNORECASE,
)
_PREFIX_NOISE = re.compile(
    r"^(?:(?:худ|бзд|бгд|сбд|схд|чд|нд)|\d+(?:-?р)?|хороо|зайсан)\s+",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ComplexMatch:
    """One extracted complex candidate and the evidence behind it."""

    canonical_name: str
    raw_name: str
    matched_alias: str | None
    trigger: str | None
    relation: str  # unit | landmark | unknown
    confidence: float


def normalize_complex_name(value: str) -> str:
    """Unicode/case/punctuation normalization shared by aliases and titles."""
    value = unicodedata.normalize("NFKC", value).casefold().replace("ё", "е")
    value = re.sub(r"[\W_]+", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def _compact(value: str) -> str:
    return normalize_complex_name(value).replace(" ", "")


def _alias_pattern(alias: str) -> re.Pattern[str]:
    """Compile one token-boundary alias pattern."""
    normalized_alias = normalize_complex_name(alias)
    suffix = r"(?:д|т|нд|ын|ийн|ы|ий|дээр|аас|ээс|оос|d)?"
    pattern = (
        r"(?<!\w)"
        + r"\s+".join(map(re.escape, normalized_alias.split()))
        + suffix
        + r"(?!\w)"
    )
    return re.compile(pattern, flags=re.UNICODE)


@lru_cache(maxsize=1)
def _compiled_aliases() -> tuple[tuple[str, str, re.Pattern[str]], ...]:
    """Compile the reviewed alias dictionary once per process."""
    return tuple(
        (canonical, alias, _alias_pattern(alias))
        for canonical, alias in _known_aliases()
    )


def _known_aliases() -> Iterable[tuple[str, str]]:
    for canonical in CANONICAL_COMPLEXES:
        yield canonical, canonical
        for alias in COMPLEX_ALIASES.get(canonical, ()):
            yield canonical, alias


def _relation_after(title: str, alias: str) -> str:
    normalized_title = normalize_complex_name(title)
    normalized_alias = normalize_complex_name(alias)
    start = normalized_title.find(normalized_alias)
    if start < 0:
        return "unit"
    tail = normalized_title[start + len(normalized_alias):]
    return "landmark" if _LANDMARK_AFTER.match(tail) else "unit"


def extract_complex(title: str | None) -> ComplexMatch | None:
    """Extract a complex from a title, preferring reviewed aliases.

    A landmark reference is returned as such so callers can retain evidence,
    but must not assign listings.complex_id from it. Numbered neighbourhoods
    (e.g. "3,4-р хороолол") are locations and intentionally return None.
    """
    if not title:
        return None
    normalized_title = normalize_complex_name(title)
    candidates = [
        (canonical, alias, _relation_after(title, alias))
        for canonical, alias, pattern in _compiled_aliases()
        if pattern.search(normalized_title)
    ]
    if candidates:
        # A title may mention one complex as a landmark before naming the
        # actual unit's complex ("Хүннү 2222 хажууд Агниста хотхонд...").
        # Unit evidence therefore outranks alias length; length only resolves
        # overlapping unit aliases such as Академи vs Академи 2.
        canonical, alias, relation = max(
            candidates,
            key=lambda item: (item[2] == "unit", len(_compact(item[1]))),
        )
        return ComplexMatch(
            canonical_name=canonical,
            raw_name=alias,
            matched_alias=alias,
            trigger=None,
            relation=relation,
            confidence=0.99 if relation == "unit" else 0.55,
        )

    normalized = normalize_complex_name(title)
    if _NUMBERED_NEIGHBOURHOOD.search(normalized):
        return None
    match = _TRIGGER.search(normalized)
    if not match:
        return None
    raw_name = match.group("name").strip()
    while True:
        cleaned = _PREFIX_NOISE.sub("", raw_name)
        if cleaned == raw_name:
            break
        raw_name = cleaned
    if not raw_name or raw_name.isdigit():
        return None
    trigger = match.group("trigger")
    relation = "landmark" if _LANDMARK_AFTER.match(normalized[match.end("name"):]) else "unit"
    return ComplexMatch(
        canonical_name=raw_name.title(),
        raw_name=raw_name,
        matched_alias=None,
        trigger=trigger,
        relation=relation,
        confidence=0.75 if relation == "unit" else 0.45,
    )
