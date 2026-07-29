"""Import smoke test for the pipeline entry point.

No test previously imported scraper.main, so a broken import (e.g. matches.py
moving to the analytics package without scraper's venv gaining that
dependency) went uncaught by the test suite. This test exists to make that
class of regression fail loudly again.
"""

import scraper.main as main_module


def test_main_module_imports_cleanly() -> None:
    assert callable(main_module.run_pipeline)
