"""Validation tests for the explicit complex-correction action contract."""

import json

import pytest

from scripts.apply_complex_corrections import load_actions


def _action(listing_id: int = 1) -> dict:
    return {
        "listing_id": listing_id,
        "action": "unlink",
        "old_complex_name": "Home Plaza",
        "new_complex_name": None,
        "reason": "confirmed_landmark",
        "evidence_text": "Home Plaza-ийн хажууд байр",
        "district": "Баянзүрх",
    }


def _write(tmp_path, actions: list[dict]):
    path = tmp_path / "actions.json"
    path.write_text(json.dumps({"actions": actions}), encoding="utf-8")
    return str(path)


def test_load_actions_accepts_unique_complete_actions(tmp_path) -> None:
    assert load_actions(_write(tmp_path, [_action()])) == [_action()]


def test_load_actions_rejects_duplicate_listing_ids(tmp_path) -> None:
    with pytest.raises(ValueError, match="duplicate action"):
        load_actions(_write(tmp_path, [_action(), _action()]))


def test_load_actions_rejects_unlink_with_reassignment_target(tmp_path) -> None:
    action = _action()
    action["new_complex_name"] = "Нархан"
    with pytest.raises(ValueError, match="must have null"):
        load_actions(_write(tmp_path, [action]))


def test_load_actions_rejects_missing_evidence(tmp_path) -> None:
    action = _action()
    action["evidence_text"] = ""
    with pytest.raises(ValueError, match="evidence_text"):
        load_actions(_write(tmp_path, [action]))
