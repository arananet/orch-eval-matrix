# Contributing to orch-eval-matrix

Thank you for contributing. This framework grows in value with every new scenario that reflects a real enterprise orchestration failure mode.

---

## What Belongs Here

**In scope:** Scenarios that test orchestration and routing decisions — intent decomposition, context management, clarification handling, conditional branching, conflict resolution, tool chaining.

**Out of scope:** Protocol compliance testing (MCP, A2A, REST), agent response quality, model benchmarking, framework-specific feature testing.

If you're unsure whether a scenario fits, open an issue first.

---

## Adding a New Scenario

### 1. Choose the right category

| Prefix | Category | Add here when... |
|---|---|---|
| `INT` | Intent Detection | The prompt contains multiple intents or requires routing pattern selection |
| `CLR` | Clarification Required | The prompt is missing context the orchestrator must ask for before acting |
| `MTX` | Multi-Turn Context | The scenario spans multiple turns and tests state preservation |
| `CND` | Conditional Routing | The routing decision depends on evaluating a condition or policy gate |
| `CNF` | Conflict Resolution | Competing constraints require conflict detection and correct escalation |
| `TLC` | Tool Chaining | Multiple tools must be called in sequence with context passed between them |

### 2. Assign the next sequential ID

Check the highest existing ID in the category file and increment by 1.

```bash
# Example: find the next CLR ID
python3 -c "
import json
data = json.load(open('scenarios/02_clarification_required/scenarios.json'))
ids = [s['id'] for s in data['scenarios']]
print(sorted(ids)[-1])
"
```

### 3. Write the scenario object

All scenarios must conform to `scenarios/schema.json`. Required fields:

```json
{
  "id": "CLR-026",
  "category": "clarification_required",
  "subcategory": "missing_entity",
  "domain": "hr",
  "title": "Short descriptive title",
  "prompt": "The user's ambiguous or incomplete request.",
  "turns": null,
  "expected_routing": {
    "agents": ["ClarificationAgent", "HRLeaveAgent"],
    "pattern": "sequential",
    "notes": "Why this routing pattern is correct."
  },
  "expected_clarification": ["Missing field 1", "Missing field 2"],
  "failure_modes": [
    "Concrete description of what the orchestrator does wrong"
  ],
  "enterprise_impact": "Business consequence if this scenario fails in production.",
  "scoring": {
    "clarification_completeness": 70,
    "no_premature_action": 30
  },
  "tags": ["clarification", "hr", "leave"]
}
```

**Scoring weights must sum to exactly 100.**

For multi-turn scenarios, use `"prompt": null` and provide a `"turns"` array:

```json
{
  "turns": [
    {
      "turn": 1,
      "user": "First user message.",
      "expected_state": { "key": "value" }
    },
    {
      "turn": 2,
      "user": "Follow-up referencing turn 1 context.",
      "expected_state": { "key": "value", "new_key": "new_value" }
    }
  ]
}
```

### 4. Validate before submitting

```bash
pip install jsonschema
python3 scripts/validate_scenarios.py
```

All scenario files must pass validation. A PR with failing validation will not be merged.

### 5. Open a pull request

- Branch name: `scenario/CLR-026-short-description`
- PR title: `feat(scenarios): add CLR-026 — [title]`
- PR description: explain the enterprise context and why this failure mode matters

---

## Improving Existing Scenarios

To improve a scenario (clearer prompt, better failure modes, additional tags):

1. Edit the scenario in the appropriate `scenarios/XX_category/scenarios.json` file
2. Do not change the `id` — IDs are permanent references
3. If the change is significant (new subcategory, different routing expectation), note in the PR why the original was incorrect
4. Run validation before submitting

---

## Improving the Scoring Rubric

Changes to `scoring/rubric.json` or `scoring/thresholds.json` affect all 75 scenarios. These require a stronger justification:

- Explain the real-world calibration basis for the proposed threshold
- Show how it would change scores for existing scenarios (run a before/after)
- Rubric changes require approval from the maintainer before merge

---

## Style Guidelines

- **Prompts** should read like real enterprise user requests — informal, enterprise domain vocabulary, realistic ambiguity
- **Enterprise impact** must be concrete: "wrong vendor notified" not "bad outcome"
- **Failure modes** must describe what the orchestrator *does* wrong, not what the agent does wrong — this matrix evaluates routing decisions only
- **Tags** use kebab-case, lowercase: `multi-intent`, `missing-entity`, `hr`, `P1`

---

## Running the Validation Script

```bash
python3 scripts/validate_scenarios.py

# Output:
# scenarios/01_intent_detection/scenarios.json: 10 scenarios OK
# scenarios/02_clarification_required/scenarios.json: 25 scenarios OK
# ...
# All 75 scenarios valid. Total scoring weight check: PASS
```

---

## Maintainer

**Eduardo Arana** — [github.com/arananet](https://github.com/arananet)

For questions about scope or design decisions, open an issue rather than a PR.
