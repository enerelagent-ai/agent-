"""Regression coverage for scripts invoked from the repository root in CI."""

import subprocess
import sys
from pathlib import Path


def test_verified_complex_workflow_scripts_import_from_repo_root() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    scripts = (
        "apply_verified_complex_match_backfill.py",
        "apply_pending_complex_match_backfill.py",
    )

    for script in scripts:
        result = subprocess.run(
            [sys.executable, str(repo_root / "analytics" / "scripts" / script), "--help"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
