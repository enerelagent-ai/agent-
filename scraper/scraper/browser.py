from playwright.sync_api import Browser, BrowserContext, Page, Playwright

CHALLENGE_TITLE_MARKER = "just a moment"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# unegui.mn shows a bot-check interstitial to default Playwright fingerprints
# (navigator.webdriver + automation flag); this is enough to avoid it in practice.
_HIDE_WEBDRIVER_SCRIPT = (
    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
)


def launch_browser(playwright: Playwright) -> Browser:
    """Launch headless Chromium with args tuned to avoid the site's bot-detection challenge."""
    return playwright.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"],
    )


def new_context(browser: Browser) -> BrowserContext:
    """Create a fresh, isolated context.

    A new context is needed per request: reusing one context across several
    navigations was observed to get stuck behind the bot-check interstitial
    indefinitely, while a fresh context reliably passes.
    """
    context = browser.new_context(
        viewport={"width": 1366, "height": 900},
        locale="mn-MN",
        user_agent=USER_AGENT,
    )
    context.add_init_script(_HIDE_WEBDRIVER_SCRIPT)
    return context


def wait_past_challenge(page: Page, timeout_s: float = 12.0, poll_s: float = 1.0) -> bool:
    """Poll the page title until the bot-check interstitial clears, or timeout_s elapses."""
    elapsed = 0.0
    while elapsed < timeout_s:
        if CHALLENGE_TITLE_MARKER not in (page.title() or "").lower():
            return True
        page.wait_for_timeout(int(poll_s * 1000))
        elapsed += poll_s
    return CHALLENGE_TITLE_MARKER not in (page.title() or "").lower()
