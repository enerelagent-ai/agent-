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

from scraper.browser import launch_browser
from scraper.detail_page import fetch_detail_html, parse_detail_page
from scraper.list_pages import collect_ad_urls
from scraper.matches import match_new_listings
from scraper.save import listing_row_from_parsed, upsert_listings

# Scope is intentionally limited to these two categories — see CLAUDE.md.
# /new-buildings/ and any other category must NOT be scraped.
CATEGORIES = {
    "for_sale": "https://www.unegui.mn/l-hdlh/l-hdlh-zarna/",
    "for_rent": "https://www.unegui.mn/l-hdlh/l-hdlh-treesllne/",
}
DELAY_RANGE = (2.0, 3.0)


def scrape_details(browser: Browser, ad_urls: list[str]) -> tuple[list[dict], list[str]]:
    """Fetch and parse each ad URL with a polite delay between requests.

    Returns (mapped rows ready for upsert, error descriptions for ads that
    could not be fetched or were unusable).
    """
    rows: list[dict] = []
    errors: list[str] = []
    for n, url in enumerate(ad_urls, 1):
        html = fetch_detail_html(browser, url)
        if html is None:
            errors.append(f"bot challenge never cleared: {url}")
        else:
            row = listing_row_from_parsed(parse_detail_page(html, url))
            if row is None:
                errors.append(f"unusable page (no title): {url}")
            else:
                rows.append(row)
        print(f"    detail {n}/{len(ad_urls)} ok={len(rows)} err={len(errors)}")
        time.sleep(random.uniform(*DELAY_RANGE))
    return rows, errors


def run_pipeline(dsn: str, max_pages: int, ads_per_category: int | None) -> int:
    """Collect ad URLs from both categories, scrape details, upsert into Postgres.

    Returns the number of error entries encountered (0 means a clean run).
    """
    all_errors: list[str] = []
    with sync_playwright() as p:
        browser = launch_browser(p)
        for name, category_url in CATEGORIES.items():
            print(f"{name}: collecting ad urls (pages 1-{max_pages})")
            ad_urls = collect_ad_urls(browser, category_url, max_pages=max_pages)
            if ads_per_category is not None:
                ad_urls = ad_urls[:ads_per_category]
            print(f"{name}: scraping {len(ad_urls)} detail pages")
            rows, errors = scrape_details(browser, ad_urls)
            saved = upsert_listings(dsn, rows)
            matches = match_new_listings(dsn, [row["source_url"] for row in rows])
            all_errors.extend(errors)
            print(f"{name}: saved {saved} rows, {len(matches)} duplicate matches, {len(errors)} errors")
            for id_a, id_b, score in matches:
                print(f"    duplicate match: listings {id_a} <-> {id_b} (score {score:.2f})")
            print()
        browser.close()

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
    args = parser.parse_args()

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        sys.exit("DATABASE_URL environment variable is required (see backend/.env)")
    error_count = run_pipeline(dsn, max_pages=args.pages, ads_per_category=args.ads_per_category)
    sys.exit(1 if error_count else 0)


if __name__ == "__main__":
    main()
