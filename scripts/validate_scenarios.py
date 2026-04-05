#!/usr/bin/env python3
"""
Validate all scenario JSON files against scenarios/schema.json.
Checks schema conformance, scoring weight sums, and ID uniqueness.

Usage:
    python3 scripts/validate_scenarios.py
    python3 scripts/validate_scenarios.py --strict   # fail on warnings too
"""
import argparse
import glob
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema")
    sys.exit(1)

ROOT = Path(__file__).parent.parent
SCHEMA_PATH = ROOT / "scenarios" / "schema.json"
SCENARIO_GLOB = str(ROOT / "scenarios" / "*" / "scenarios.json")

EXPECTED_COUNTS = {
    "01_intent_detection": 10,
    "02_clarification_required": 25,
    "03_multi_turn_context": 15,
    "04_conditional_routing": 10,
    "05_conflict_resolution": 10,
    "06_tool_chaining": 5,
    "07_adversarial": 5,
}


def load_schema() -> dict:
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def validate_file(path: str, schema: dict, all_ids: set) -> tuple[int, list[str], list[str]]:
    """Returns (scenario_count, errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    with open(path) as f:
        data = json.load(f)

    scenarios = data.get("scenarios", [])
    category_dir = Path(path).parent.name

    # Category count check
    expected = EXPECTED_COUNTS.get(category_dir)
    if expected is not None and len(scenarios) != expected:
        errors.append(
            f"Expected {expected} scenarios in {category_dir}, found {len(scenarios)}"
        )

    for scenario in scenarios:
        sid = scenario.get("id", "<no id>")

        # Schema validation
        try:
            jsonschema.validate(scenario, schema)
        except jsonschema.ValidationError as e:
            errors.append(f"{sid}: schema error — {e.message}")

        # ID uniqueness
        if sid in all_ids:
            errors.append(f"{sid}: duplicate ID")
        all_ids.add(sid)

        # Scoring weights sum to 100
        scoring = scenario.get("scoring", {})
        total = sum(scoring.values())
        if total != 100:
            errors.append(f"{sid}: scoring weights sum to {total}, expected 100")

        # Warn on missing observability_hints (non-blocking)
        if "observability_hints" not in scenario:
            warnings.append(f"{sid}: missing optional observability_hints")

    return len(scenarios), errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate orch-eval-matrix scenario files")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args()

    schema = load_schema()
    files = sorted(glob.glob(SCENARIO_GLOB))

    if not files:
        print("ERROR: No scenario files found. Run from repo root.")
        sys.exit(1)

    all_ids: set[str] = set()
    total_scenarios = 0
    all_errors: list[str] = []
    all_warnings: list[str] = []

    for path in files:
        count, errors, warnings = validate_file(path, schema, all_ids)
        rel = Path(path).relative_to(ROOT)
        status = "OK" if not errors else "FAIL"
        print(f"{rel}: {count} scenarios [{status}]")
        for e in errors:
            print(f"  ERROR: {e}")
        for w in warnings:
            print(f"  WARN:  {w}")
        total_scenarios += count
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    print(f"\nTotal scenarios: {total_scenarios}/80")
    print(f"Total IDs: {len(all_ids)} unique")

    if all_errors:
        print(f"\n{len(all_errors)} error(s) found. Validation FAILED.")
        sys.exit(1)

    if args.strict and all_warnings:
        print(f"\n{len(all_warnings)} warning(s) in strict mode. Validation FAILED.")
        sys.exit(1)

    print("\nAll scenarios valid. Validation PASSED.")


if __name__ == "__main__":
    main()
