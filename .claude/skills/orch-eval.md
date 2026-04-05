---
name: orch-eval
description: Enterprise orchestration & routing evaluation framework. Use when the user wants to evaluate, test, score, or benchmark an AI orchestration system, routing layer, agent framework, or multi-agent system against enterprise scenarios. Triggers on: "evaluate my orchestration", "run the eval matrix", "test my routing", "benchmark my agent system", "score my orchestrator", "how does my system perform", "run orch-eval", "/orch-eval".
---

# Enterprise Orchestration Evaluation Matrix (ORCH-EVAL)

Benchmark any orchestration or routing system against **75 enterprise-grade scenarios** across 6 critical categories. Framework-agnostic. Observable. Production-grade scoring.

**Maintainer:** Eduardo Arana
**Version:** 1.0.0 | **Total Points:** 1,000 | **Passing Threshold:** ≥850

---

## Quick Reference

| Category | Scenarios | Points | Pass Threshold |
|---|---|---|---|
| Intent Detection | 10 | 200 | ≥90% |
| Clarification Required | 25 | 250 | ≥95% |
| Multi-Turn Context | 15 | 150 | ≥90% |
| Conditional Routing | 10 | 150 | ≥85% |
| Conflict Resolution | 10 | 150 | ≥80% |
| Tool Chaining | 5 | 100 | ≥90% |

**Tiers:** ≥850 = Production Ready | 700–849 = Needs Work | <700 = Fail

---

## Evaluation Workflow

Work through each phase in order. Do not skip phases.

---

### Phase 1: Discover the Target System

Ask the user the following questions and record all answers before proceeding:

1. **Framework:** What orchestration framework or system are you evaluating?
   - Options: LangGraph, AutoGen/Magentic-One, CrewAI, Semantic Kernel, DSPy, Haystack, Agno, custom, other
   - Note the version if known (e.g., LangGraph 0.3.x)

2. **Submission method:** How do I submit a scenario to your system?
   - HTTP API endpoint → ask for URL + auth
   - Python function → ask for function signature
   - CLI command → ask for command template
   - Interactive (paste-and-observe) → note this; we'll go scenario by scenario

3. **Observability:** Does your system emit traces?
   - Langfuse → ask for project name (env vars: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY)
   - Phoenix → ask for collector endpoint
   - OpenTelemetry → ask for OTLP endpoint
   - None → note that trace correlation won't be available

4. **Scope:** Which scenarios to run?
   - Full suite (75 scenarios) — recommended for production gate decisions
   - Category subset — ask which categories
   - Quick sample (15 scenarios) — random sample, 2-3 per category
   - Single scenario by ID — e.g., CLR-011

5. **Target score:** What is their minimum acceptable score? Default: 850 (Production Ready)

Store these as the **Evaluation Configuration** and confirm with the user before running.

---

### Phase 2: Validate Environment

Before running scenarios, confirm the scenario files are present:

```
scenarios/01_intent_detection/scenarios.json      — 10 scenarios
scenarios/02_clarification_required/scenarios.json — 25 scenarios
scenarios/03_multi_turn_context/scenarios.json     — 15 scenarios
scenarios/04_conditional_routing/scenarios.json    — 10 scenarios
scenarios/05_conflict_resolution/scenarios.json    — 10 scenarios
scenarios/06_tool_chaining/scenarios.json          —  5 scenarios
scoring/rubric.json
scoring/thresholds.json
```

If the user has a JSON Schema validator available:
```bash
python3 -c "
import json, glob
schema = json.load(open('scenarios/schema.json'))
for f in glob.glob('scenarios/*/scenarios.json'):
    data = json.load(open(f))
    print(f'{f}: {len(data[\"scenarios\"])} scenarios OK')
"
```

---

### Phase 3: Run Scenarios

For each scenario in the selected scope:

**Step 1 — Load the scenario**
Read the scenario from the appropriate JSON file. Key fields:
- `id`, `title`, `category`, `domain`
- `prompt` (single-turn) or `turns` (multi-turn array)
- `expected_routing.agents` and `expected_routing.pattern`
- `expected_clarification` (list of required questions)
- `failure_modes` (what to watch for)
- `scoring` (point breakdown)

**Step 2 — Submit to the target system**
- Single-turn: submit `prompt` as a single message
- Multi-turn: submit each turn in `turns` sequentially, one at a time; capture the system's response after each turn before submitting the next

**Step 3 — Capture the actual response**
Record:
- `actual_routing`: which agents/tools were invoked (if observable)
- `actual_clarification`: what clarifying questions (if any) were asked
- `response_text`: the full response
- `response_time_ms`: latency
- `turn_states` (multi-turn): what context was preserved turn-to-turn

**Step 4 — Score the response using rubric.json dimensions**

For each dimension in the scenario's `scoring` object, award 0–100% of the dimension's point weight:

- **routing_accuracy**: Did it route to the correct agents in the correct pattern?
  - Correct primary + correct secondary = 100%
  - Correct primary only = 70%
  - Correct domain, wrong agent = 40%
  - Wrong domain = 0%

- **clarification_completeness**: Did it ask for all required context before acting?
  - All required questions asked, no action taken prematurely = 100%
  - Partial questions asked = proportional
  - Acted without asking = 0% + flag failure mode

- **context_retained** (multi-turn): Was prior turn context present in later decisions?
  - Context used correctly = 100%
  - Context lost (re-asked) = 0% + flag failure mode
  - Context partially used = 50%

- **condition_evaluated** (conditional routing): Were all gate conditions checked?
  - All conditions checked, correct branch = 100%
  - Short-circuited = 50%
  - No condition check = 0%

- **conflict_detected** (conflict resolution): Was the conflict identified and escalated correctly?
  - Conflict detected + correct escalation + context passed = 100%
  - Conflict detected but wrong action = 50%
  - Conflict missed = 0%

- **tool_context_passed** (tool chaining): Was output from tool N passed correctly to tool N+1?
  - All links in chain preserved = 100%
  - One link broken = proportional deduction
  - Chain not followed = 0%

**Step 5 — Check for critical failures**
Compare observed behavior against `failure_modes`. If any **critical severity** failure mode is triggered:
- Flag `critical_failure: true` for this scenario
- Note: the entire run's tier is capped at "Needs Work" per thresholds.json

**Step 6 — Log to observability (if configured)**
Emit a span with attributes from the recommended span attributes table in `observability/integration_guide.md`.

---

### Phase 4: Multi-Turn Scenario Special Protocol

For scenarios with `"turns": [...]` (all MTX-* scenarios):

1. Start a new session/conversation with the target system
2. Submit Turn 1; record response
3. Evaluate: does the response match `turns[0].expected_state`?
4. Submit Turn 2 **in the same session**; record response
5. At each turn where a prior entity/fact is referenced, check whether it appears in the response
6. If the system re-asks for information already provided → `context_retained = 0` for that scenario
7. At the final turn, compile the full context retention score

Do NOT send all turns as a single message. Each turn must be submitted separately to test true state preservation.

---

### Phase 5: Generate the Scoring Report

After all scenarios complete, compile this report:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ORCH-EVAL RESULTS REPORT v1.0.0
 System Under Test : [system name + framework]
 Evaluation Date   : [date]
 Evaluator         : Claude Code (orch-eval skill)
 Scenarios Run     : [N] / 75
 Run ID            : [run_id]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 TOTAL SCORE: [X] / 1,000
 TIER: [Production Ready ✓ | Needs Work ⚠ | Fail ✗]

┌─────────────────────────┬──────────┬────────┬────────┬──────────┐
│ Category                │ Scenarios│  Max   │ Earned │  Score % │
├─────────────────────────┼──────────┼────────┼────────┼──────────┤
│ Intent Detection        │    10    │  200   │   X    │    X%    │
│ Clarification Required  │    25    │  250   │   X    │    X%    │
│ Multi-Turn Context      │    15    │  150   │   X    │    X%    │
│ Conditional Routing     │    10    │  150   │   X    │    X%    │
│ Conflict Resolution     │    10    │  150   │   X    │    X%    │
│ Tool Chaining           │     5    │  100   │   X    │    X%    │
├─────────────────────────┼──────────┼────────┼────────┼──────────┤
│ TOTAL                   │    75    │ 1,000  │   X    │    X%    │
└─────────────────────────┴──────────┴────────┴────────┴──────────┘

Critical Failures Triggered: [scenario IDs] or "None"

TOP 3 WEAKEST SCENARIOS
1. [ID] — [title]: [score]/[max pts] — [root cause]
2. ...
3. ...

TOP 3 STRONGEST SCENARIOS
1. [ID] — [title]: [score]/[max pts]
2. ...
3. ...

RECOMMENDATIONS
[Generated based on weakest categories and most common failure modes.
 Prioritize the category with the largest gap from its passing threshold.]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Phase 6: Post-Evaluation Actions

Present the full report to the user, then offer:

1. **Export as JSON** — for CI/CD pipeline integration:
   ```json
   {
     "run_id": "...",
     "total_score": 872,
     "tier": "production_ready",
     "categories": { ... },
     "critical_failures": [],
     "per_scenario": [ ... ]
   }
   ```

2. **Re-run specific scenarios** — if the user wants to test a fix:
   "Would you like to re-run any specific scenarios after making changes? Provide the IDs (e.g., CLR-011, MTX-003)."

3. **Regression baseline** — if score ≥ 850:
   "Your system passed. I recommend saving this run as your regression baseline in your observability platform. Future runs should alert if score drops more than 5%."

4. **Remediation roadmap** — if score < 850:
   Present the top 3 remediation priorities ranked by: (points available) × (gap from threshold).

5. **Observability setup** — if tracing was not configured:
   "For full observability, see `observability/integration_guide.md` for Langfuse and Phoenix integration."

---

## Scenario File Reference

| File | Category | IDs | Count |
|---|---|---|---|
| `scenarios/01_intent_detection/scenarios.json` | Intent Detection | INT-001..010 | 10 |
| `scenarios/02_clarification_required/scenarios.json` | Clarification | CLR-001..025 | 25 |
| `scenarios/03_multi_turn_context/scenarios.json` | Multi-Turn | MTX-001..015 | 15 |
| `scenarios/04_conditional_routing/scenarios.json` | Conditional | CND-001..010 | 10 |
| `scenarios/05_conflict_resolution/scenarios.json` | Conflict | CNF-001..010 | 10 |
| `scenarios/06_tool_chaining/scenarios.json` | Tool Chaining | TLC-001..005 | 5 |

## Troubleshooting

| Issue | Action |
|---|---|
| System returns no routing decision | Score routing_accuracy = 0; flag as "no_decision" failure mode |
| System hangs on multi-turn turn | Abort after 15s; score context_retention = 0 for that scenario |
| Observability connection fails | Continue without tracing; note in report |
| Schema validation fails on scenario files | Stop; report file corruption — do not evaluate against corrupt scenarios |
| Score variance > 20% across repetitions | Flag scenario as "unstable"; note in report under risk section |
