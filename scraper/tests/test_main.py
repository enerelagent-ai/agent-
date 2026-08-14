"""Import smoke test for the pipeline entry point.

No test previously imported scraper.main, so a broken import (e.g. matches.py
moving to the analytics package without scraper's venv gaining that
dependency) went uncaught by the test suite. This test exists to make that
class of regression fail loudly again.
"""

import scraper.main as main_module
from scraper.list_pages import InventoryResult


def test_main_module_imports_cleanly() -> None:
    assert callable(main_module.run_pipeline)


def test_cli_parses_expected_flags(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["scraper.main", "--pages", "5", "--skip-recent-days", "1", "--stop-after-known-pages", "3"],
    )
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost:5432/postgres")

    captured: dict = {}

    def fake_run_pipeline(dsn, max_pages, ads_per_category, skip_recent_days=0.0, stop_after_known_pages=0):
        captured.update(
            dsn=dsn,
            max_pages=max_pages,
            ads_per_category=ads_per_category,
            skip_recent_days=skip_recent_days,
            stop_after_known_pages=stop_after_known_pages,
        )
        return 0

    monkeypatch.setattr(main_module, "run_pipeline", fake_run_pipeline)

    try:
        main_module.main()
    except SystemExit as exc:
        assert exc.code in (0, None)

    assert captured == {
        "dsn": "postgresql://localhost:5432/postgres",
        "max_pages": 5,
        "ads_per_category": None,
        "skip_recent_days": 1.0,
        "stop_after_known_pages": 3,
    }


def test_pipeline_records_market_snapshot_after_scrape(monkeypatch) -> None:
    events: list[object] = []

    class FakePlaywrightContext:
        def __enter__(self):
            return object()

        def __exit__(self, exc_type, exc, traceback):
            return False

    class FakeBrowser:
        def close(self) -> None:
            events.append("browser_closed")

    monkeypatch.setattr(main_module, "CATEGORIES", {})
    monkeypatch.setattr(main_module, "sync_playwright", FakePlaywrightContext)
    monkeypatch.setattr(main_module, "launch_browser", lambda _playwright: FakeBrowser())
    monkeypatch.setattr(
        main_module,
        "snapshot_market_prices_conn",
        lambda dsn: events.append(("snapshot", dsn)) or 12,
    )

    errors = main_module.run_pipeline("postgresql://example/test", 1, None)

    assert errors == 0
    assert events == ["browser_closed", ("snapshot", "postgresql://example/test")]


def test_inventory_reconciliation_refuses_partial_crawl(monkeypatch) -> None:
    events: list[str] = []

    class FakePlaywrightContext:
        def __enter__(self):
            return object()

        def __exit__(self, exc_type, exc, traceback):
            return False

    class FakeBrowser:
        def close(self) -> None:
            events.append("browser_closed")

    monkeypatch.setattr(main_module, "CATEGORIES", {"for_sale": "https://x/sale"})
    monkeypatch.setattr(main_module, "sync_playwright", FakePlaywrightContext)
    monkeypatch.setattr(main_module, "launch_browser", lambda _playwright: FakeBrowser())
    monkeypatch.setattr(
        main_module,
        "collect_ad_inventory",
        lambda *_args, **_kwargs: InventoryResult(
            urls=["https://x/adv/1_a/"], complete=False, stop_reason="max_pages"
        ),
    )
    monkeypatch.setattr(
        main_module,
        "reconcile_category_inventory_conn",
        lambda *_args: events.append("reconciled"),
    )

    import pytest

    with pytest.raises(RuntimeError, match="incomplete"):
        main_module.run_inventory_reconciliation("postgresql://example/test", 10)

    assert events == ["browser_closed"]
