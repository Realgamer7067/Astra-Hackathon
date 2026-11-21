import json
from copy import deepcopy
from pathlib import Path

import pytest
from app.models.wire import DemoBundle, ScenarioRequest
from pydantic import ValidationError

FIXTURE = Path(__file__).resolve().parents[3] / "data/fixtures/demo.json"


def test_duplicate_participants_are_rejected() -> None:
    scenario = json.loads(FIXTURE.read_text(encoding="utf-8"))["scenario"]
    scenario["participants"][1] = deepcopy(scenario["participants"][0])
    with pytest.raises(ValidationError, match="distinct"):
        ScenarioRequest.model_validate(scenario)


def test_wrong_render_units_and_naive_epochs_are_rejected() -> None:
    demo = json.loads(FIXTURE.read_text(encoding="utf-8"))
    demo["states"]["position_unit"] = "km"
    demo["states"]["at_utc"] = "2026-11-21T12:00:00"
    with pytest.raises(ValidationError) as error:
        DemoBundle.model_validate(demo)
    assert {e["loc"] for e in error.value.errors()} >= {
        ("states", "position_unit"),
        ("states", "at_utc"),
    }
