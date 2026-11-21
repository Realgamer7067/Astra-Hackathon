"""Export public API schemas without starting the service."""

from pathlib import Path
import json

from services.api.app.main import app

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    (ROOT / "packages/contracts/openapi.json").write_text(
        json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
