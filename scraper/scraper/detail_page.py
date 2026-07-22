"""Fetch and parse Unegui.mn ad detail pages (/adv/{id}_{slug}/).

Parsing is done on the raw HTML string (BeautifulSoup) rather than the live
Playwright page, so it can be unit-tested offline against saved fixtures.
"""

import re
import time
from datetime import datetime, timedelta
from typing import Any

from bs4 import BeautifulSoup
from playwright.sync_api import Browser

from scraper.browser import new_context, wait_past_challenge

AD_ID_URL_RE = re.compile(r"/adv/(\d+)_")
# Map image URL embeds coordinates as .../geo/static/streets/{lng}/{lat}/...
GEO_COORDS_RE = re.compile(r"/geo/static/streets/(-?\d{1,3}\.\d+)/(-?\d{1,3}\.\d+)")
POSTED_PREFIX = "Нийтэлсэн:"
TODAY_WORD = "өнөөдөр"
YESTERDAY_WORD = "өчигдөр"
TIME_RE = re.compile(r"(\d{1,2}):(\d{2})")
ABS_DATE_RE = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")


def fetch_detail_html(browser: Browser, url: str, *, retries: int = 2) -> str | None:
    """Load one ad detail page in a fresh browser context and return its HTML.

    Returns None if the bot-check interstitial never clears after retrying.
    """
    for attempt in range(retries + 1):
        context = new_context(browser)
        try:
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded")
            if wait_past_challenge(page):
                return page.content()
        finally:
            context.close()
        if attempt < retries:
            time.sleep(2)
    return None


def parse_posted_at(raw: str, *, now: datetime | None = None) -> str | None:
    """Normalize a posted-date string to ISO 'YYYY-MM-DDTHH:MM'.

    Handles 'Өнөөдөр HH:MM', 'Өчигдөр HH:MM' and absolute 'YYYY-M-D' forms;
    returns None for anything unrecognized (caller keeps the raw string too).
    """
    now = now or datetime.now()
    text = raw.lower()
    time_m = TIME_RE.search(text)
    hour, minute = (int(time_m.group(1)), int(time_m.group(2))) if time_m else (0, 0)

    if TODAY_WORD in text:
        day = now
    elif YESTERDAY_WORD in text:
        day = now - timedelta(days=1)
    else:
        abs_m = ABS_DATE_RE.search(text)
        if not abs_m:
            return None
        day = datetime(int(abs_m.group(1)), int(abs_m.group(2)), int(abs_m.group(3)))
    return day.replace(hour=hour, minute=minute).strftime("%Y-%m-%dT%H:%M")


def _slug_from_href(href: str) -> str | None:
    """Return the last path segment of a category href, e.g. '/l-hdlh/.../oron-suuts/' -> 'oron-suuts'."""
    segment = href.rstrip("/").rsplit("/", 1)[-1]
    return segment or None


def _parse_breadcrumbs(soup: BeautifulSoup) -> dict[int, tuple[str, str]]:
    """Return breadcrumb items as {position: (name, href)}.

    The ad breadcrumb is a schema.org BreadcrumbList: position 3 is the
    transaction type (зарна/түрээслүүлнэ), position 4 the property category,
    position 5 an optional subcategory.
    """
    crumbs: dict[int, tuple[str, str]] = {}
    for li in soup.select("ul.breadcrumbs li"):
        position_el = li.select_one("meta[itemprop=position]")
        name_el = li.select_one("span[itemprop=name]")
        link_el = li.select_one("a[href]")
        if not (position_el and name_el):
            continue
        try:
            position = int(position_el.get("content", ""))
        except ValueError:
            continue
        href = link_el.get("href", "") if link_el else ""
        crumbs[position] = (name_el.get_text(strip=True), href)
    return crumbs


def _parse_phones(soup: BeautifulSoup) -> list[str]:
    """Owner phone numbers from the hidden contacts dialog's tel: anchors.

    The dialog ships pre-rendered in the raw HTML (display:none), so no
    'Дугаар харах' click is needed. Site-support numbers live outside the
    dialog as unrendered {{...}} templates; the guard drops any that leak.
    """
    phones: list[str] = []
    for anchor in soup.select("div.contacts-dialog a[href^='tel:']"):
        number = anchor.get("href", "").removeprefix("tel:").strip()
        if number and "{{" not in number and number not in phones:
            phones.append(number)
    return phones


def _parse_photo_urls(soup: BeautifulSoup) -> list[str]:
    """Full-size gallery image URLs, scoped to the ad's own gallery container.

    The page also carries ~50 thumbnails for the similar-ads grid, so only
    div.announcement__images images count. data-full is the full-size
    variant; src is the already-loaded fallback.
    """
    urls: list[str] = []
    for img in soup.select("div.announcement__images img[itemprop=image]"):
        url = img.get("data-full") or img.get("src")
        if url and url not in urls:
            urls.append(url)
    return urls


def _split_location(raw: str) -> tuple[str | None, str | None]:
    """Split 'Дүүрэг, Дэд байршил, ...' into (district, sub_district)."""
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    district = parts[0] if parts else None
    sub_district = ", ".join(parts[1:]) if len(parts) > 1 else None
    return district, sub_district


def parse_detail_page(html: str, url: str) -> dict[str, Any]:
    """Parse one ad detail page's HTML into a flat dict.

    The spec list (Шал, Тагт, Талбай, ...) is returned as a generic 'specs'
    dict because the key set varies by listing type.
    """
    soup = BeautifulSoup(html, "html.parser")

    title_el = soup.select_one("h1#ad-title")
    description_el = soup.select_one("div.announcement-description[itemprop=description]")
    price_meta = soup.select_one("meta[itemprop=price]")
    currency_meta = soup.select_one("meta[itemprop=priceCurrency]")
    price_cost_el = soup.select_one(".announcement-price__cost")
    address_el = soup.select_one("span[itemprop=address]")
    sku_el = soup.select_one("span[itemprop=sku]")
    date_el = soup.select_one("span.date-meta")

    ad_id: int | None = None
    if sku_el and sku_el.get_text(strip=True).isdigit():
        ad_id = int(sku_el.get_text(strip=True))
    else:
        url_m = AD_ID_URL_RE.search(url)
        if url_m:
            ad_id = int(url_m.group(1))

    price: float | None = None
    if price_meta and price_meta.get("content"):
        try:
            price = float(price_meta["content"])
        except ValueError:
            price = None

    location_raw = address_el.get_text(strip=True) if address_el else None
    district, sub_district = _split_location(location_raw) if location_raw else (None, None)

    posted_raw: str | None = None
    if date_el:
        posted_raw = date_el.get_text(strip=True).removeprefix(POSTED_PREFIX).strip()

    specs: dict[str, str] = {}
    for li in soup.select("ul.chars-column li"):
        key_el = li.select_one(".key-chars")
        value_el = li.select_one(".value-chars")
        if key_el and value_el:
            key = key_el.get_text(strip=True).rstrip(":")
            specs[key] = value_el.get_text(strip=True)

    latitude = longitude = None
    coords_m = GEO_COORDS_RE.search(html)
    if coords_m:
        longitude, latitude = float(coords_m.group(1)), float(coords_m.group(2))

    crumbs = _parse_breadcrumbs(soup)
    listing_type: str | None = None
    if 3 in crumbs:
        transaction_href = crumbs[3][1]
        if "zarna" in transaction_href:
            listing_type = "sale"
        elif "treesllne" in transaction_href:
            listing_type = "rent"
    category_name, category_href = crumbs.get(4, (None, ""))
    subcategory_name, subcategory_href = crumbs.get(5, (None, ""))

    return {
        "url": url,
        "ad_id": ad_id,
        "title": title_el.get_text(strip=True) if title_el else None,
        "description": description_el.get_text("\n", strip=True) if description_el else None,
        "price": price,
        "price_raw": re.sub(r"\s+", " ", price_cost_el.get_text(" ", strip=True)) if price_cost_el else None,
        "currency": currency_meta.get("content") if currency_meta else None,
        "location_raw": location_raw,
        "district": district,
        "sub_district": sub_district,
        "listing_type": listing_type,
        "property_category": category_name,
        "property_category_slug": _slug_from_href(category_href),
        "property_subcategory": subcategory_name,
        "property_subcategory_slug": _slug_from_href(subcategory_href),
        "posted_raw": posted_raw,
        "posted_at": parse_posted_at(posted_raw) if posted_raw else None,
        "latitude": latitude,
        "longitude": longitude,
        "phones": _parse_phones(soup),
        "photo_urls": _parse_photo_urls(soup),
        "specs": specs,
    }
