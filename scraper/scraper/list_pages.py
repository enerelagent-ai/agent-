import random
import re
import time
from urllib.parse import urljoin

from playwright.sync_api import Browser
from playwright.sync_api import Error as PlaywrightError

from scraper.browser import new_context, wait_past_challenge

AD_HREF_RE = re.compile(r"^/adv/\d+_[\w-]+/?$")


def build_page_url(category_url: str, page_num: int) -> str:
    """Return the list-page URL for a given page number of a category (page 1 has no query param)."""
    if page_num <= 1:
        return category_url
    return f"{category_url}?page={page_num}"


def fetch_ad_urls_from_page(browser: Browser, url: str, *, retries: int = 2) -> list[str]:
    """Load one list page in a fresh browser context and return the unique,
    absolute detail-page URLs found on it.

    Returns an empty list if the bot-check interstitial never clears after
    retrying, or if every attempt fails on a transient error (network change,
    timeout) — long unattended runs must survive those, not crash.
    """
    for attempt in range(retries + 1):
        context = new_context(browser)
        try:
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded")
            if wait_past_challenge(page):
                hrefs = page.eval_on_selector_all(
                    "a[href*='/adv/']", "els => els.map(e => e.getAttribute('href'))"
                )
                matched = {h for h in hrefs if h and AD_HREF_RE.match(h)}
                return sorted(urljoin(url, h) for h in matched)
        except PlaywrightError as exc:
            reason = str(exc).splitlines()[0][:120]
            print(f"    fetch error (attempt {attempt + 1}): {reason}", flush=True)
        finally:
            context.close()
        if attempt < retries:
            time.sleep(2 * (attempt + 1))
    return []


def collect_ad_urls(
    browser: Browser,
    category_url: str,
    max_pages: int,
    *,
    delay_range: tuple[float, float] = (2.0, 3.0),
    stop_after_stale: int = 3,
) -> list[str]:
    """Walk pages 1..max_pages of a category listing and collect unique ad detail URLs.

    Sleeps a random delay within delay_range after every page request to respect
    the site's load. Stops early once stop_after_stale consecutive pages yield
    no new URLs — past the category's real last page the site can only return
    empty or repeated content, and categories differ in page count so a shared
    max_pages overshoots the smaller one. The threshold (not a single empty
    page) keeps one transient bot-challenge failure from truncating the walk.
    """
    seen: dict[str, None] = {}
    stale_pages = 0
    for page_num in range(1, max_pages + 1):
        page_url = build_page_url(category_url, page_num)
        ad_urls = fetch_ad_urls_from_page(browser, page_url)
        new_urls = sum(1 for ad_url in ad_urls if ad_url not in seen)
        print(f"    page {page_num}: {len(ad_urls)} ads, {new_urls} new ({page_url})", flush=True)
        for ad_url in ad_urls:
            seen.setdefault(ad_url, None)
        stale_pages = 0 if new_urls else stale_pages + 1
        if stale_pages >= stop_after_stale:
            print(f"    stopping: {stop_after_stale} consecutive pages with no new ads")
            break
        time.sleep(random.uniform(*delay_range))
    return list(seen)
