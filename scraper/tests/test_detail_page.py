from scraper.detail_page import parse_detail_page


def test_parse_detail_page_extracts_source_view_count() -> None:
    parsed = parse_detail_page(
        """
        <html><body>
          <h1 id="ad-title">Тест зар</h1>
          <span class="counter-views">Үзсэн : 1,234</span>
        </body></html>
        """,
        "https://www.unegui.mn/adv/123_test/",
    )

    assert parsed["view_count"] == 1234


def test_parse_detail_page_leaves_missing_view_count_unknown() -> None:
    parsed = parse_detail_page(
        '<h1 id="ad-title">Тест зар</h1>',
        "https://www.unegui.mn/adv/123_test/",
    )

    assert parsed["view_count"] is None
