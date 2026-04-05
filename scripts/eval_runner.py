#!/usr/bin/env python3
"""
orch-eval-matrix — Reference Evaluation Harness

Submits each scenario to a target orchestration system via HTTP and scores
the response against the rubric. Outputs a structured JSON report.

Usage:
    python3 scripts/eval_runner.py --config examples/sample_run_config.yaml
    python3 scripts/eval_runner.py --config my-config.yaml --categories intent_detection clarification_required
    python3 scripts/eval_runner.py --config my-config.yaml --scenario-ids CLR-011 MTX-003

Requirements:
    pip install orch-eval-matrix         # base
    pip install orch-eval-matrix[langfuse]  # with Langfuse observability
    pip install orch-eval-matrix[phoenix]   # with Phoenix/Arize observability
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import yaml

ROOT = Path(__file__).parent.parent

# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass
class ScenarioResult:
    scenario_id: str
    category: str
    domain: str
    title: str
    score: float
    max_score: int
    score_pct: float
    routing_expected: list[str]
    routing_actual: list[str]
    clarification_expected: list[str]
    clarification_actual: list[str]
    critical_failure: bool
    failure_modes_triggered: list[str]
    response_time_ms: float
    turn_scores: list[dict] = field(default_factory=list)  # multi-turn only
    notes: str = ""


@dataclass
class EvalReport:
    run_id: str
    system_name: str
    framework: str
    eval_date: str
    scenarios_run: int
    total_score: float
    max_score: int
    score_pct: float
    tier: str
    critical_failures: list[str]
    category_scores: dict[str, dict]
    per_scenario: list[dict]
    recommendations: list[str]


# ── Config loading ────────────────────────────────────────────────────────────


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)["orch_eval"]


# ── Scenario loading ──────────────────────────────────────────────────────────


def load_scenarios(config: dict) -> list[dict]:
    scope = config.get("scope", {})
    all_scenarios: list[dict] = []

    category_map = {
        "intent_detection": "01_intent_detection",
        "clarification_required": "02_clarification_required",
        "multi_turn_context": "03_multi_turn_context",
        "conditional_routing": "04_conditional_routing",
        "conflict_resolution": "05_conflict_resolution",
        "tool_chaining": "06_tool_chaining",
    }

    target_categories = (
        list(category_map.keys())
        if scope.get("run_all", False)
        else scope.get("categories", list(category_map.keys()))
    )

    for cat in target_categories:
        dir_name = category_map.get(cat)
        if not dir_name:
            continue
        path = ROOT / "scenarios" / dir_name / "scenarios.json"
        if not path.exists():
            print(f"WARNING: {path} not found, skipping")
            continue
        with open(path) as f:
            data = json.load(f)
        all_scenarios.extend(data["scenarios"])

    # Filter by specific IDs if provided
    scenario_ids = scope.get("scenario_ids")
    if scenario_ids:
        all_scenarios = [s for s in all_scenarios if s["id"] in scenario_ids]

    # Filter by difficulty
    difficulty_filter = scope.get("difficulty_filter")
    if difficulty_filter:
        all_scenarios = [
            s for s in all_scenarios
            if s.get("difficulty", "intermediate") in difficulty_filter
        ]

    # Sample
    sample_size = scope.get("sample_size")
    if sample_size and sample_size < len(all_scenarios):
        import random
        all_scenarios = random.sample(all_scenarios, sample_size)

    return all_scenarios


# ── Submission ────────────────────────────────────────────────────────────────


def submit_single_turn(scenario: dict, config: dict) -> tuple[dict, float]:
    """Submit a single-turn scenario. Returns (response_dict, latency_ms)."""
    target = config["target_system"]
    endpoint = os.path.expandvars(target["endpoint"])
    auth = os.path.expandvars(target.get("auth_header", ""))
    timeout = target.get("timeout_ms", 15000) / 1000

    headers = {"Content-Type": "application/json"}
    if auth:
        headers["Authorization"] = f"Bearer {auth}"

    payload = {
        "message": scenario["prompt"],
        "session_id": f"orch-eval-{scenario['id']}",
    }

    start = time.monotonic()
    try:
        response = httpx.post(endpoint, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        elapsed_ms = (time.monotonic() - start) * 1000
        return response.json(), elapsed_ms
    except httpx.TimeoutException:
        elapsed_ms = (time.monotonic() - start) * 1000
        return {"error": "timeout", "agents_invoked": [], "text": ""}, elapsed_ms
    except Exception as e:
        elapsed_ms = (time.monotonic() - start) * 1000
        return {"error": str(e), "agents_invoked": [], "text": ""}, elapsed_ms


def submit_multi_turn(scenario: dict, config: dict) -> tuple[list[dict], float]:
    """Submit a multi-turn scenario turn by turn. Returns (turn_responses, total_ms)."""
    target = config["target_system"]
    session_endpoint = os.path.expandvars(
        target.get("session_endpoint", target["endpoint"])
    )
    auth = os.path.expandvars(target.get("auth_header", ""))
    timeout = target.get("timeout_ms", 15000) / 1000

    headers = {"Content-Type": "application/json"}
    if auth:
        headers["Authorization"] = f"Bearer {auth}"

    session_id = f"orch-eval-{scenario['id']}-{int(time.time())}"
    turn_responses = []
    total_ms = 0.0

    for turn in scenario["turns"]:
        payload = {"message": turn["user"], "session_id": session_id}
        start = time.monotonic()
        try:
            response = httpx.post(
                session_endpoint, json=payload, headers=headers, timeout=timeout
            )
            response.raise_for_status()
            elapsed_ms = (time.monotonic() - start) * 1000
            turn_responses.append({
                "turn": turn["turn"],
                "user": turn["user"],
                "response": response.json(),
                "latency_ms": elapsed_ms,
            })
        except Exception as e:
            elapsed_ms = (time.monotonic() - start) * 1000
            turn_responses.append({
                "turn": turn["turn"],
                "user": turn["user"],
                "response": {"error": str(e), "agents_invoked": [], "text": ""},
                "latency_ms": elapsed_ms,
            })
        total_ms += elapsed_ms

    return turn_responses, total_ms


# ── Scoring ───────────────────────────────────────────────────────────────────


def score_response(scenario: dict, response: dict) -> tuple[float, list[str]]:
    """
    Score a single-turn response against the scenario rubric.

    Returns (score_0_to_100, failure_modes_triggered).

    NOTE: This is a reference implementation. In practice, scoring requires
    either a human evaluator or a judge LLM to assess routing accuracy,
    clarification quality, and context retention. This implementation scores
    based on structured fields (agents_invoked, clarification_questions)
    that the target system must return in its response payload.

    Expected response payload shape:
    {
      "text": "...",
      "agents_invoked": ["AgentA", "AgentB"],
      "routing_pattern": "parallel",
      "clarification_questions": ["question 1", "question 2"],
      "context_state": {}
    }
    """
    scoring_weights = scenario["scoring"]
    max_points = sum(scoring_weights.values())  # always 100

    actual_agents = set(response.get("agents_invoked", []))
    expected_agents = set(scenario["expected_routing"]["agents"])
    actual_clarification = set(response.get("clarification_questions", []))
    expected_clarification = set(scenario["expected_clarification"])

    triggered_failures: list[str] = []
    dimension_scores: dict[str, float] = {}

    # ── Routing accuracy ──────────────────────────────────────────────────
    if "routing_accuracy" in scoring_weights or "intent_split" in scoring_weights:
        key = "routing_accuracy" if "routing_accuracy" in scoring_weights else "intent_split"
        if actual_agents == expected_agents:
            dimension_scores[key] = 1.0
        elif actual_agents & expected_agents:  # partial overlap
            dimension_scores[key] = len(actual_agents & expected_agents) / len(expected_agents)
        else:
            dimension_scores[key] = 0.0
            triggered_failures.append("wrong_domain_routing")

    # ── Clarification completeness ────────────────────────────────────────
    for key in ("clarification_completeness", "context_retained", "no_premature_action"):
        if key not in scoring_weights:
            continue
        if key == "clarification_completeness":
            if not expected_clarification:
                dimension_scores[key] = 1.0
            elif not actual_clarification and expected_clarification:
                dimension_scores[key] = 0.0
                triggered_failures.append("no_clarification_asked")
            else:
                asked_required = actual_clarification & expected_clarification
                dimension_scores[key] = len(asked_required) / len(expected_clarification)
        elif key == "no_premature_action":
            # Pass if clarification was asked before routing, or no clarification needed
            acted_without_asking = (
                bool(expected_clarification)
                and not actual_clarification
                and bool(actual_agents)
            )
            dimension_scores[key] = 0.0 if acted_without_asking else 1.0
            if acted_without_asking:
                triggered_failures.append("premature_action")

    # ── Routing pattern ───────────────────────────────────────────────────
    if "routing_pattern" in scoring_weights:
        expected_pattern = scenario["expected_routing"].get("pattern")
        actual_pattern = response.get("routing_pattern")
        dimension_scores["routing_pattern"] = 1.0 if actual_pattern == expected_pattern else 0.5

    # ── Conflict / escalation ─────────────────────────────────────────────
    for key in ("conflict_detected", "correct_escalation"):
        if key in scoring_weights:
            # Requires judge evaluation — default to requiring human review flag
            conflict_flagged = response.get("conflict_flagged", False)
            dimension_scores[key] = 1.0 if conflict_flagged else 0.0
            if not conflict_flagged and key == "conflict_detected":
                triggered_failures.append("conflict_not_detected")

    # ── Condition evaluated ───────────────────────────────────────────────
    if "condition_evaluated" in scoring_weights:
        conditions_checked = response.get("conditions_checked", [])
        dimension_scores["condition_evaluated"] = 1.0 if conditions_checked else 0.0

    # ── Tool chain context ────────────────────────────────────────────────
    for key in ("tool1_to_tool2_context", "tool2_to_tool3_context"):
        if key in scoring_weights:
            chain_intact = response.get("chain_context_intact", False)
            dimension_scores[key] = 1.0 if chain_intact else 0.0
            if not chain_intact:
                triggered_failures.append("tool_chain_context_lost")

    # ── Compute weighted score ────────────────────────────────────────────
    total = 0.0
    for dim, weight in scoring_weights.items():
        dim_score = dimension_scores.get(dim, 0.5)  # 0.5 = needs human review
        total += dim_score * weight

    return total, triggered_failures


def score_multi_turn(scenario: dict, turn_responses: list[dict]) -> tuple[float, list[str]]:
    """Score a multi-turn scenario by evaluating context preservation across turns."""
    turns = scenario["turns"]
    scoring_weights = scenario["scoring"]
    triggered_failures: list[str] = []

    context_scores = []
    for i, (turn_def, turn_resp) in enumerate(zip(turns, turn_responses)):
        response = turn_resp.get("response", {})
        expected_state = turn_def.get("expected_state", {})
        actual_state = response.get("context_state", {})

        # Check if expected state keys are present in actual state
        if expected_state:
            matched = sum(
                1 for k, v in expected_state.items()
                if actual_state.get(k) == v
            )
            context_scores.append(matched / len(expected_state))
            if matched < len(expected_state):
                triggered_failures.append(f"context_loss_turn_{i + 1}")
        else:
            context_scores.append(1.0)

    avg_context = sum(context_scores) / len(context_scores) if context_scores else 0.5

    total = 0.0
    for dim, weight in scoring_weights.items():
        if "context" in dim or "retained" in dim:
            total += avg_context * weight
        elif "no_re_ask" in dim:
            re_asked = any(
                t.get("response", {}).get("re_asked_prior_info", False)
                for t in turn_responses
            )
            total += (0.0 if re_asked else 1.0) * weight
            if re_asked:
                triggered_failures.append("re_asked_prior_info")
        else:
            total += 0.5 * weight  # neutral for unscored dimensions

    return total, triggered_failures


# ── Tier resolution ───────────────────────────────────────────────────────────


def resolve_tier(
    total_score: float,
    critical_failures: list[str],
    thresholds: dict,
) -> str:
    for override in thresholds.get("critical_failure_overrides", []):
        if override["action"] == "automatic_fail" and critical_failures:
            return "Fail"

    for tier in thresholds["tiers"]:
        if tier["min_score"] <= total_score <= tier["max_score"]:
            return tier["label"]
    return "Fail"


def generate_recommendations(category_scores: dict, thresholds: dict) -> list[str]:
    recs = []
    prod_mins = thresholds["tiers"][0].get("per_category_minimums") or {}
    gaps = []
    for cat, data in category_scores.items():
        earned = data["earned"]
        min_required = prod_mins.get(cat, 0)
        if earned < min_required:
            gaps.append((min_required - earned, cat, earned, data["max"]))

    gaps.sort(reverse=True)
    for gap, cat, earned, max_pts in gaps[:3]:
        recs.append(
            f"Prioritise '{cat}': scored {earned}/{max_pts} "
            f"({gap} pts below production-ready minimum)"
        )

    if not recs:
        recs.append(
            "All categories meet production-ready minimums. "
            "Set up automated regression testing to maintain this score."
        )
    return recs


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="orch-eval-matrix evaluation harness")
    parser.add_argument("--config", required=True, help="Path to run config YAML")
    parser.add_argument("--categories", nargs="*", help="Override categories to run")
    parser.add_argument("--scenario-ids", nargs="*", help="Run specific scenario IDs only")
    parser.add_argument("--output", help="Output JSON path (overrides config)")
    args = parser.parse_args()

    config = load_config(args.config)

    if args.categories:
        config["scope"]["categories"] = args.categories
        config["scope"]["run_all"] = False
    if args.scenario_ids:
        config["scope"]["scenario_ids"] = args.scenario_ids

    # Load scoring files
    with open(ROOT / "scoring" / "rubric.json") as f:
        rubric = json.load(f)
    with open(ROOT / "scoring" / "thresholds.json") as f:
        thresholds = json.load(f)

    scenarios = load_scenarios(config)
    if not scenarios:
        print("No scenarios matched the configured scope. Exiting.")
        return

    print(f"Running {len(scenarios)} scenarios against {config['target_system']['name']}...\n")

    results: list[ScenarioResult] = []
    repetitions = config.get("repetitions", {}).get("count", 3)

    for scenario in scenarios:
        is_multi_turn = bool(scenario.get("turns"))
        rep_scores = []

        for rep in range(repetitions):
            if is_multi_turn:
                turn_responses, total_ms = submit_multi_turn(scenario, config)
                score, failures = score_multi_turn(scenario, turn_responses)
            else:
                response, total_ms = submit_single_turn(scenario, config)
                score, failures = score_response(scenario, response)

            rep_scores.append(score)

        final_score = sum(rep_scores) / len(rep_scores)
        max_pts = sum(scenario["scoring"].values())

        result = ScenarioResult(
            scenario_id=scenario["id"],
            category=scenario["category"],
            domain=scenario["domain"],
            title=scenario.get("title", ""),
            score=round(final_score, 2),
            max_score=max_pts,
            score_pct=round(final_score / max_pts, 3),
            routing_expected=scenario["expected_routing"]["agents"],
            routing_actual=[],
            clarification_expected=scenario["expected_clarification"],
            clarification_actual=[],
            critical_failure=False,
            failure_modes_triggered=failures,
            response_time_ms=round(total_ms, 1),
        )
        results.append(result)

        status = "PASS" if not failures else "WARN"
        print(f"  [{status}] {scenario['id']:10s} {final_score:5.1f}/{max_pts}  {scenario.get('title','')[:50]}")

    # ── Aggregate scores ──────────────────────────────────────────────────
    category_scores: dict[str, dict] = {}
    for cat_key, cat_data in rubric["categories"].items():
        cat_results = [r for r in results if r.category == cat_key]
        earned = sum(r.score for r in cat_results)
        max_pts = cat_data["total_category_points"]
        category_scores[cat_key] = {
            "earned": round(earned, 1),
            "max": max_pts,
            "pct": round(earned / max_pts, 3) if max_pts else 0,
            "scenarios_run": len(cat_results),
        }

    total_score = sum(d["earned"] for d in category_scores.values())
    critical_failures = [r.scenario_id for r in results if r.critical_failure]
    tier = resolve_tier(total_score, critical_failures, thresholds)
    recommendations = generate_recommendations(category_scores, thresholds)

    report = EvalReport(
        run_id=config.get("run_id", f"eval-{int(time.time())}"),
        system_name=config["target_system"]["name"],
        framework=config["target_system"].get("framework", "unknown"),
        eval_date=datetime.now(timezone.utc).isoformat(),
        scenarios_run=len(results),
        total_score=round(total_score, 1),
        max_score=rubric["total_points"],
        score_pct=round(total_score / rubric["total_points"], 3),
        tier=tier,
        critical_failures=critical_failures,
        category_scores=category_scores,
        per_scenario=[asdict(r) for r in results],
        recommendations=recommendations,
    )

    # ── Print summary ─────────────────────────────────────────────────────
    print(f"\n{'━'*60}")
    print(f" ORCH-EVAL RESULTS")
    print(f" System : {report.system_name} ({report.framework})")
    print(f" Date   : {report.eval_date}")
    print(f"{'━'*60}")
    print(f" TOTAL  : {report.total_score:.0f} / {report.max_score}  ({report.score_pct:.0%})")
    print(f" TIER   : {report.tier}")
    print(f"{'━'*60}")
    for cat, data in report.category_scores.items():
        print(f"  {cat:30s} {data['earned']:6.1f} / {data['max']:4d}  {data['pct']:.0%}")
    if report.critical_failures:
        print(f"\nCritical failures: {', '.join(report.critical_failures)}")
    print(f"\nRecommendations:")
    for rec in report.recommendations:
        print(f"  • {rec}")

    # ── Write output ──────────────────────────────────────────────────────
    output_dir = Path(config.get("output", {}).get("output_dir", "results"))
    output_dir.mkdir(exist_ok=True)
    output_path = args.output or str(
        output_dir / f"{report.run_id}.json"
    )
    with open(output_path, "w") as f:
        json.dump(asdict(report), f, indent=2)
    print(f"\nFull results written to: {output_path}")

    # ── CI/CD exit code ───────────────────────────────────────────────────
    ci_config = config.get("ci_cd", {})
    fail_threshold = ci_config.get("fail_pipeline_on_score_below", 850)
    if report.total_score < fail_threshold:
        print(f"\nCI FAIL: score {report.total_score:.0f} < threshold {fail_threshold}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
