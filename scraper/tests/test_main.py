"""Import smoke test for the pipeline entry point.

No test previously imported scraper.main, so a broken import (e.g. matches.py
moving to the analytics package without scraper's venv gaining that
dependency) went uncaught by the test suite. This test exists to make that
class of regression fail loudly again.
"""

import scraper.main as main_module


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
