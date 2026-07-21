from playwright.sync_api import sync_playwright

from scraper.browser import launch_browser
from scraper.list_pages import collect_ad_urls

# Scope is intentionally limited to these two categories — see CLAUDE.md.
# /new-buildings/ and any other category must NOT be scraped.
CATEGORIES = {
    "for_sale": "https://www.unegui.mn/l-hdlh/l-hdlh-zarna/",
    "for_rent": "https://www.unegui.mn/l-hdlh/l-hdlh-treesllne/",
}


def main() -> None:
    """Collect ad detail URLs from pages 1-3 of each category and print the counts."""
    with sync_playwright() as p:
        browser = launch_browser(p)
        total = 0
        for name, url in CATEGORIES.items():
            print(f"{name}:")
            ad_urls = collect_ad_urls(browser, url, max_pages=3)
            print(f"{name}: {len(ad_urls)} unique ad urls\n")
            total += len(ad_urls)
        browser.close()
        print(f"total: {total} unique ad urls")


if __name__ == "__main__":
    main()
