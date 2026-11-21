#!/usr/bin/env python3
"""Rank hackathon ideas with adjustable weighted criteria."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, NoReturn


DEFAULT_WEIGHTS = {
    "rubric_fit": 2.0,
    "demo_impact": 2.0,
    "feasibility": 1.5,
    "originality": 1.0,
    "visual_potential": 1.0,
    "story_strength": 1.0,
    "technical_depth": 1.0,
    "sponsor_fit": 1.0,
    "usefulness": 1.0,
    "time_to_mvp": 1.0,
    "differentiation": 1.0,
    "failure_risk": -1.0,
    "complexity_cost": -1.0,
    "dependency_risk": -1.0,
}


def fail(message: str) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def load_structured(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        fail(f"cannot read {path}: {exc}")
    try:
        return json.loads(text)
    except json.JSONDecodeError as json_exc:
        try:
            import yaml  # type: ignore
        except ImportError:
            fail(
                f"{path} is not valid JSON ({json_exc.msg}); install PyYAML to read YAML"
            )
        try:
            return yaml.safe_load(text)
        except Exception as yaml_exc:  # PyYAML exposes several parser errors
            fail(f"cannot parse {path} as JSON or YAML: {yaml_exc}")


def normalize_key(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def parse_weights(data: Any) -> dict[str, float]:
    if not isinstance(data, dict):
        fail("weights must be an object mapping criterion names to numbers")
    result: dict[str, float] = {}
    for key, value in data.items():
        if isinstance(value, bool):
            fail(f"weight for {key!r} must be a finite number, not boolean")
        try:
            number = float(value)
        except (TypeError, ValueError):
            fail(f"weight for {key!r} is not numeric")
        if not math.isfinite(number):
            fail(f"weight for {key!r} must be finite")
        normalized = normalize_key(str(key))
        if normalized in result:
            fail(f"duplicate normalized weight {normalized!r}")
        result[normalized] = number
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rank hackathon ideas using a transparent weighted score.",
        epilog=(
            "Input may be JSON, or YAML when PyYAML is installed. Use either a list of "
            "ideas or {'ideas': [...], 'weights': {...}}. Each idea needs 'name' and a "
            "'scores' mapping with values from 0-10. A high time_to_mvp score means fast. "
            "Set fatal_pass=false to mark an idea disqualified without hiding its score."
        ),
    )
    parser.add_argument("input", type=Path, help="JSON/YAML idea file")
    parser.add_argument("--weights", type=Path, help="optional JSON/YAML weight overrides")
    parser.add_argument("--top", type=int, help="show only the top N eligible ideas")
    missing = parser.add_mutually_exclusive_group()
    missing.add_argument("--strict", action="store_true", help="require all active scores (default)")
    missing.add_argument("--allow-missing", action="store_true", help="provisional: missing benefits=0, missing costs/risks=10")
    parser.add_argument("--replace-weights", action="store_true", help="start with no default weights; useful for exact event rubrics")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.top is not None and args.top <= 0:
        fail("--top must be positive")
    data = load_structured(args.input)
    if isinstance(data, dict):
        ideas = data.get("ideas")
        embedded_weights = data.get("weights", {})
    else:
        ideas = data
        embedded_weights = {}
    if not isinstance(ideas, list) or not ideas:
        fail("input must contain a non-empty list of ideas")

    weights = {} if args.replace_weights else dict(DEFAULT_WEIGHTS)
    weights.update(parse_weights(embedded_weights))
    if args.weights:
        weights.update(parse_weights(load_structured(args.weights)))
    if not any(value != 0 for value in weights.values()):
        fail("at least one weight must be non-zero")

    results = []
    warnings = []
    names = set()
    for index, item in enumerate(ideas, start=1):
        if not isinstance(item, dict):
            fail(f"idea {index} is not an object")
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            fail(f"idea {index} has no non-empty name")
        name = name.strip()
        if name in names:
            fail(f"duplicate idea name {name!r}")
        names.add(name)
        for gate in ("fatal_pass", "eligible"):
            if gate in item and not isinstance(item[gate], bool):
                fail(f"{name}: {gate} must be JSON true or false")
        if "fatal_pass" in item and "eligible" in item and item["fatal_pass"] != item["eligible"]:
            fail(f"{name}: conflicting eligibility flags")
        raw_scores = item.get("scores", item)
        if not isinstance(raw_scores, dict):
            fail(f"scores for {name!r} must be an object")
        scores = {normalize_key(str(k)): v for k, v in raw_scores.items()}
        contributions: dict[str, float] = {}
        for criterion, weight in weights.items():
            if criterion not in scores:
                if weight == 0:
                    contributions[criterion] = 0.0
                    continue
                score = 10.0 if weight < 0 else 0.0
                message = f"{name}: missing {criterion}; conservative provisional value {score:g}"
                if not args.allow_missing:
                    fail(f"{name}: missing {criterion}; supply it or use --allow-missing")
                warnings.append(message)
            else:
                if isinstance(scores[criterion], bool):
                    fail(f"{name}: {criterion} must be numeric, not boolean")
                try:
                    score = float(scores[criterion])
                except (TypeError, ValueError):
                    fail(f"{name}: {criterion} is not numeric")
                if not math.isfinite(score) or not 0 <= score <= 10:
                    fail(f"{name}: {criterion}={score} is outside 0-10")
            contributions[criterion] = score * weight
        total = sum(contributions.values())
        positive_weight = sum(value for value in weights.values() if value > 0)
        if not math.isfinite(total) or not math.isfinite(positive_weight):
            fail("score arithmetic overflow; rescale the weights")
        normalized = total / positive_weight if positive_weight else total
        fatal_pass = item.get("fatal_pass", item.get("eligible", True))
        if "fatal_pass" not in item and "eligible" not in item:
            warnings.append(f"{name}: eligibility assumed; verify fatal gates before selecting")
        results.append(
            {
                "name": name,
                "fatal_pass": fatal_pass,
                "score": round(total, 3),
                "normalized": round(normalized, 3),
                "contributions": {k: round(v, 3) for k, v in contributions.items()},
            }
        )

    results.sort(key=lambda row: (row["fatal_pass"], row["score"]), reverse=True)
    eligible = [row for row in results if row["fatal_pass"]]
    shown = eligible[: args.top] if args.top else results

    if args.json:
        print(json.dumps({"weights": weights, "ranking": shown, "warnings": warnings,
                          "provisional": bool(warnings), "eligible_count": len(eligible)}, indent=2, allow_nan=False))
    else:
        width = max(len(row["name"]) for row in shown) if shown else 4
        print(f"{'Rank':>4}  {'Idea':<{width}}  {'Score':>8}  {'Norm':>7}  Status")
        rank = 0
        for row in shown:
            if row["fatal_pass"]:
                rank += 1
                rank_text = str(rank)
                status = "eligible"
            else:
                rank_text = "-"
                status = "fatal gate failed"
            print(
                f"{rank_text:>4}  {row['name']:<{width}}  {row['score']:>8.2f}  "
                f"{row['normalized']:>7.2f}  {status}"
            )
        for warning in warnings:
            print(f"warning: {warning}", file=sys.stderr)
    return 0 if eligible else 1


if __name__ == "__main__":
    raise SystemExit(main())
