"""Unit tests for collect_ad_urls' early-stop logic, via a faked page fetch
(no live browser needed) — see scraper.list_pages.collect_ad_urls docstring
for why stop_after_known is a separate mechanism from stop_after_stale."""

import scraper.list_pages as list_pages_module
from scraper.list_pages import collect_ad_urls


def _fake_fetch(pages: dict[int, list[str]], fetched: list[int]):
    def fetch(browser, url, *, retries=2):
        page_num = int(url.rsplit("page=", 1)[-1]) if "page=" in url else 1
        fetched.append(page_num)
        return pages.get(page_num, [])

    return fetch


def test_collect_ad_urls_stops_after_known_pages(monkeypatch) -> None:
    pages = {n: [f"https://x/adv/{n}_a/"] for n in range(1, 7)}
    fetched: list[int] = []
    monkeypatch.setattr(list_pages_module, "fetch_ad_urls_from_page", _fake_fetch(pages, fetched))

    known = {pages[3][0], pages[4][0], pages[5][0]}

    result = collect_ad_urls(
        browser=None,
        category_url="https://x/",
        max_pages=10,
        delay_range=(0, 0),
        known_urls_checker=lambda urls: {u for u in urls if u in known},
        stop_after_known=3,
    )

    # pages 1,2 are new (not known); 3,4,5 are fully known -> streak hits 3, stop before page 6
    assert fetched == [1, 2, 3, 4, 5]
    assert result == [pages[n][0] for n in (1, 2, 3, 4, 5)]


def test_collect_ad_urls_resets_known_streak_on_partial_page(monkeypatch) -> None:
    pages = {
        1: ["https://x/adv/1_a/"],
        2: ["https://x/adv/2_a/"],
        # page 3 mixes an already-known url with a brand-new one -> not fully known
        3: ["https://x/adv/2_a/", "https://x/adv/3_a/"],
        4: ["https://x/adv/4_a/"],
        5: ["https://x/adv/5_a/"],
    }
    fetched: list[int] = []
    monkeypatch.setattr(list_pages_module, "fetch_ad_urls_from_page", _fake_fetch(pages, fetched))

    known = {"https://x/adv/1_a/", "https://x/adv/2_a/", "https://x/adv/4_a/"}

    result = collect_ad_urls(
        browser=None,
        category_url="https://x/",
        max_pages=5,
        delay_range=(0, 0),
        known_urls_checker=lambda urls: {u for u in urls if u in known},
        stop_after_known=3,
    )

    # streak of 2 (pages 1-2) is broken by page 3's partial match, and only one
    # more fully-known page (4) follows before max_pages -> never reaches 3,
    # so the walk runs all the way to page 5 instead of stopping early.
    assert fetched == [1, 2, 3, 4, 5]
    assert "https://x/adv/5_a/" in result


def test_collect_ad_urls_without_checker_is_unaffected(monkeypatch) -> None:
    """No known_urls_checker (the default) -> original stale-page-only behavior."""
    pages = {n: [] for n in range(1, 6)}  # every page empty -> stale immediately
    fetched: list[int] = []
    monkeypatch.setattr(list_pages_module, "fetch_ad_urls_from_page", _fake_fetch(pages, fetched))

    result = collect_ad_urls(
        browser=None,
        category_url="https://x/",
        max_pages=10,
        delay_range=(0, 0),
        stop_after_stale=3,
    )

    assert fetched == [1, 2, 3]  # stops after 3 consecutive empty (stale) pages
    assert result == []
