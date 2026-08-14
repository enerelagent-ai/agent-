"""Full Unegui.mn scraping pipeline: list pages -> detail pages -> Postgres.

Run small first (see --ads-per-category) and only scale up after the whole
chain is verified end-to-end, per the project workflow.
"""

import argparse
import os
import random
import sys
import time

from playwright.sync_api import Browser, sync_playwright

from analytics.calculations import snapshot_market_prices_conn
from analytics.matches import match_new_listings

from scraper.browser import launch_browser
from scraper.detail_page import fetch_detail_html, parse_detail_page
from scraper.list_pages import collect_ad_urls
from scraper.save import (
    known_urls_conn,
    listing_row_from_parsed,
    recently_scraped_urls,
    upsert_listings,
)

# Scope is intentionally limited to these two categories — see CLAUDE.md.
# /new-buildings/ and any other category must NOT be scraped.
CATEGORIES = {
    "for_sale": "https://www.unegui.mn/l-hdlh/l-hdlh-zarna/",
    "for_rent": "https://www.unegui.mn/l-hdlh/l-hdlh-treesllne/",
}
DELAY_RANGE = (2.0, 3.0)


def scrape_and_save(
    browser: Browser,
    ad_urls: list[str],
    dsn: str,
    *,
    batch_size: int = 50,
) -> tuple[int, list[tuple[int, int, float]], list[str]]:
    """Fetch, parse and persist ads in batches of batch_size.

    Incremental saving matters on long runs: a crash loses at most one
    batch of work, and --skip-recent-days can then resume past everything
    already saved. Returns (rows saved, duplicate matches, errors).
    """
    saved = 0
    matches: list[tuple[int, int, float]] = []
    errors: list[str] = []
    batch: list[dict] = []

    def flush() -> None:
        nonlocal saved
        if not batch:
            return
        saved += upsert_listings(dsn, batch)
        matches.extend(match_new_listings(dsn, [row["source_url"] for row in batch]))
        batch.clear()

    for n, url in enumerate(ad_urls, 1):
        html = fetch_detail_html(browser, url)
        if html is None:
            errors.append(f"bot challenge never cleared: {url}")
        else:
            row = listing_row_from_parsed(parse_detail_page(html, url))
            if row is None:
                errors.append(f"unusable page (no title): {url}")
            else:
                batch.append(row)
        if len(batch) >= batch_size:
            flush()
        print(f"    detail {n}/{len(ad_urls)} saved={saved} pending={len(batch)} err={len(errors)}", flush=True)
        time.sleep(random.uniform(*DELAY_RANGE))
    flush()
    return saved, matches, errors


def run_pipeline(
    dsn: str,
    max_pages: int,
    ads_per_category: int | None,
    skip_recent_days: float = 0.0,
    stop_after_known_pages: int = 0,
) -> int:
    """Collect ad URLs from both categories, scrape details, upsert into Postgres.

    skip_recent_days > 0 skips ads already scraped within that window, so an
    interrupted long run can resume without re-fetching finished pages.
    stop_after_known_pages > 0 additionally cuts the list-page walk itself
    short once that many consecutive pages are entirely already-known ads —
    see list_pages.collect_ad_urls for why this is a separate mechanism from
    skip_recent_days (that one skips detail-page fetches; this one skips
    list-page requests, which matters for a daily incremental run where most
    of a generous --pages ceiling would otherwise be re-walking old pages).
    Returns the number of error entries encountered (0 means a clean run).
    """
    all_errors: list[str] = []
    with sync_playwright() as p:
        browser = launch_browser(p)
        for name, category_url in CATEGORIES.items():
            print(f"{name}: collecting ad urls (pages 1-{max_pages})")
            known_checker = (
                (lambda urls: known_urls_conn(dsn, urls))
                if stop_after_known_pages > 0
                else None
            )
            ad_urls = collect_ad_urls(
                browser,
                category_url,
                max_pages=max_pages,
                known_urls_checker=known_checker,
                stop_after_known=stop_after_known_pages or 3,
            )
            if skip_recent_days > 0:
                skip = recently_scraped_urls(dsn, ad_urls, skip_recent_days)
                ad_urls = [u for u in ad_urls if u not in skip]
                print(f"{name}: skipping {len(skip)} ads scraped within {skip_recent_days} day(s)")
            if ads_per_category is not None:
                ad_urls = ad_urls[:ads_per_category]
            print(f"{name}: scraping {len(ad_urls)} detail pages", flush=True)
            saved, matches, errors = scrape_and_save(browser, ad_urls, dsn)
            all_errors.extend(errors)
            print(f"{name}: saved {saved} rows, {len(matches)} duplicate matches, {len(errors)} errors")
            for id_a, id_b, score in matches:
                print(f"    duplicate match: listings {id_a} <-> {id_b} (score {score:.2f})")
            print(flush=True)
        browser.close()

    snapshot_count = snapshot_market_prices_conn(dsn)
    print(f"market snapshot: {snapshot_count} price groups recorded", flush=True)

    if all_errors:
        print("errors:")
        for error in all_errors:
            print(f"  - {error}")
    return len(all_errors)


def main() -> None:
    """CLI entry point; reads the Postgres URL from the DATABASE_URL env var."""
    parser = argparse.ArgumentParser(description="Unegui.mn -> Postgres scraping pipeline")
    parser.add_argument("--pages", type=int, default=1, help="list pages per category (default 1)")
    parser.add_argument(
        "--ads-per-category",
        type=int,
        default=None,
        help="cap detail pages per category; omit to scrape every collected URL",
    )
    parser.add_argument(
        "--skip-recent-days",
        type=float,
        default=0.0,
        help="skip ads already scraped within this many days (resume support); 0 disables",
    )
    parser.add_argument(
        "--stop-after-known-pages",
        type=int,
        default=0,
        help=(
            "stop a category's list-page walk after this many consecutive pages are "
            "entirely already-known ads (for daily incremental runs); 0 disables"
        ),
    )
    args = parser.parse_args()

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        sys.exit("DATABASE_URL environment variable is required (see backend/.env)")
    error_count = run_pipeline(
        dsn,
        max_pages=args.pages,
        ads_per_category=args.ads_per_category,
        skip_recent_days=args.skip_recent_days,
        stop_after_known_pages=args.stop_after_known_pages,
    )
    sys.exit(1 if error_count else 0)


if __name__ == "__main__":
    main()
