# orch-eval-matrix

**Enterprise Orchestration & Routing Evaluation Framework**

![Scenarios](https://img.shields.io/badge/scenarios-75-blue)
![Score Scale](https://img.shields.io/badge/score%20scale-1000%20pts-green)
![Production Threshold](https://img.shields.io/badge/production%20ready-%E2%89%A5850-brightgreen)
![Framework Agnostic](https://img.shields.io/badge/framework-agnostic-lightgrey)
![License](https://img.shields.io/badge/license-MIT-blue)

75 production-grade scenarios to validate:

- Multi-intent decomposition & parallel routing
- Missing context clarification flows
- Multi-turn state preservation
- Conditional routing logic
- Conflict detection & escalation
- Tool → tool coordination chains

**Developer:** [Eduardo Arana](https://github.com/arananet)

---

## What This Is

`orch-eval-matrix` is a **framework-agnostic evaluation corpus** for benchmarking AI orchestration and routing systems. It does **not** implement an orchestrator — it provides the scenarios, scoring rubric, and tooling to evaluate yours.

Whether you're building on LangGraph, AutoGen/Magentic-One, CrewAI, Semantic Kernel, DSPy, Haystack, Agno, or a fully custom orchestration layer, this matrix gives you a consistent, reproducible score across 6 critical enterprise capability dimensions.

**Who it's for:**
- Platform teams building shared orchestration infrastructure
- AI engineers evaluating orchestration frameworks before adoption
- QA teams setting production readiness gates for agent systems
- Teams integrating LLM routing into enterprise ERP/ITSM/HR workflows

---

## Quick Start

```bash
git clone https://github.com/arananet/orch-eval-matrix
cd orch-eval-matrix

# Validate scenario files (requires Python + jsonschema)
python3 -c "
import json, glob
for f in glob.glob('scenarios/*/scenarios.json'):
    data = json.load(open(f))
    print(f'{f}: {len(data[\"scenarios\"])} scenarios')
"

# Run evaluation interactively using the Claude Code skill
# (inside Claude Code CLI)
/orch-eval
```

Or use the reference config for your harness:
```bash
cp examples/sample_run_config.yaml my-eval-config.yaml
# edit target_system section, then run with your eval harness
```

---

## Repository Structure

```
orch-eval-matrix/
├── README.md
├── .claude/
│   └── skills/
│       └── orch-eval.md            # Claude Code /orch-eval skill
├── scenarios/
│   ├── schema.json                 # JSON Schema for all scenario files
│   ├── 01_intent_detection/
│   │   └── scenarios.json          # 10 scenarios — INT-001..010
│   ├── 02_clarification_required/
│   │   └── scenarios.json          # 25 scenarios — CLR-001..025
│   ├── 03_multi_turn_context/
│   │   └── scenarios.json          # 15 scenarios — MTX-001..015
│   ├── 04_conditional_routing/
│   │   └── scenarios.json          # 10 scenarios — CND-001..010
│   ├── 05_conflict_resolution/
│   │   └── scenarios.json          # 10 scenarios — CNF-001..010
│   └── 06_tool_chaining/
│       └── scenarios.json          # 5 scenarios  — TLC-001..005
├── scoring/
│   ├── rubric.json                 # Per-dimension scoring rules & weights
│   └── thresholds.json             # Production/needs-work/fail bands
├── observability/
│   └── integration_guide.md        # Langfuse, Phoenix/Arize, OpenTelemetry
└── examples/
    └── sample_run_config.yaml      # Reference config for evaluation harnesses
```

---

## Scenario Categories

| # | Category | IDs | Scenarios | Points | Pass Threshold | Enterprise Focus |
|---|---|---|---|---|---|---|
| 1 | Intent Detection | INT-001..010 | 10 | 200 | ≥90% | Parallel/sequential/conditional routing from natural language |
| 2 | Clarification Required | CLR-001..025 | 25 | 250 | ≥95% | HR · Procurement · IT · Finance · Manufacturing |
| 3 | Multi-Turn Context | MTX-001..015 | 15 | 150 | ≥90% | State carryover, context updates, policy evolution |
| 4 | Conditional Routing | CND-001..010 | 10 | 150 | ≥85% | Boolean gates, threshold checks, policy branching |
| 5 | Conflict Resolution | CNF-001..010 | 10 | 150 | ≥80% | Priority conflicts, policy vs. urgency, escalation chains |
| 6 | Tool Chaining | TLC-001..005 | 5 | 100 | ≥90% | Multi-tool dependency chains, context passing |
| | **Total** | | **75** | **1,000** | | |

### Domain Coverage

| Domain | Scenarios |
|---|---|
| HR & Workforce | 12 |
| Procurement & Supply Chain | 14 |
| IT & Incident Management | 12 |
| Finance & Accounting | 10 |
| Manufacturing & Operations | 8 |
| Customer Service | 8 |
| Travel & Facilities | 6 |
| General / Cross-Domain | 5 |

---

## Scoring System

### Total: 1,000 Points

```
Total Score = Σ (category_score × category_weight)
```

Each scenario awards points across multiple dimensions:
- **Routing accuracy** — correct agent(s) selected, correct pattern (parallel/sequential/conditional)
- **Clarification quality** — all missing context asked for, no premature action taken
- **Context retention** — prior turn state correctly applied (multi-turn scenarios)
- **Condition evaluation** — all gate conditions checked before branching
- **Conflict detection** — conflict identified and escalated to the right stakeholder
- **Tool chain integrity** — output from tool N correctly passed to tool N+1

### Pass Tiers

| Score | Tier | Recommendation |
|---|---|---|
| ≥ 850 | **Production Ready** | Deploy. Set up automated regression testing. |
| 700–849 | **Needs Work** | Fix lowest-scoring category before deploying. |
| < 700 | **Fail** | Do not deploy. Remediate core routing and clarification logic. |

### Critical Failure Overrides

Certain failures cap or override the tier regardless of total score:

| Override | Effect |
|---|---|
| Any `critical` severity failure mode triggered | Tier capped at "Needs Work" |
| PII logged in observability traces | Automatic Fail |
| Security approval gate bypassed | Automatic Fail |
| Zero score in any category | Automatic Fail |

See `scoring/thresholds.json` for full override definitions.

---

## Supported Orchestration Frameworks (2025–2026)

This matrix is framework-agnostic. It has been designed with the following patterns and platforms in mind, covering the orchestration landscape as of late 2025 and early 2026:

### Graph-Based Orchestrators

| Framework | Pattern | Key Eval Scenarios |
|---|---|---|
| **LangGraph 0.3+** | Stateful DAG with persistent checkpointing. Nodes are agents; edges encode routing logic. Supports supervisor, hierarchical, and swarm topologies. | MTX-* (checkpointed state), CND-* (edge conditions), TLC-* (node chains) |
| **LangGraph Multi-Agent** | Supervisor agent delegates to specialized sub-agents. Sub-agents report back; supervisor decides next step. | INT-* (supervisor decomposition), CNF-* (supervisor conflict arbitration) |

### Role-Based / Collaborative Orchestrators

| Framework | Pattern | Key Eval Scenarios |
|---|---|---|
| **AutoGen 0.4+ / Magentic-One** | Orchestrator + Ledger pattern. Orchestrator maintains a task ledger; agents report progress. Supports parallel agent execution with dynamic re-planning. | INT-* (parallel dispatch), MTX-* (ledger-based context), CNF-* (orchestrator arbitration) |
| **CrewAI** | Crew of role-defined agents with sequential or hierarchical process. Manager LLM routes tasks based on agent roles. | CLR-* (manager role requests clarification), INT-* (crew task decomposition) |

### Declarative / DSL Orchestrators

| Framework | Pattern | Key Eval Scenarios |
|---|---|---|
| **Semantic Kernel (Planner)** | Handlebars or Stepwise Planner generates a plan from intent. Sequential plan execution with step-level tool calls. | INT-* (planner intent decomposition), TLC-* (stepwise tool chains) |
| **DSPy** | Declarative signatures + compiled optimization. Routing logic is a learned module. | CND-* (compiled conditional routing), INT-* (signature-based intent classification) |
| **Haystack Pipelines** | DAG of components (nodes). Routers branch flow based on output scores or metadata. | CND-* (branch nodes), TLC-* (pipeline chains) |

### Emerging 2025–2026 Patterns

| Pattern | Description | Key Eval Scenarios |
|---|---|---|
| **Agno / Agent-as-Function** | Lightweight agents represented as typed Python functions. Orchestrator calls agents like function calls with structured I/O. Zero framework overhead. | TLC-* (function chain context), INT-* (function dispatch) |
| **Model Context Protocol (MCP)** | Standardized protocol (Anthropic, 2024–2025) for tool and resource exposure. Orchestrators call MCP servers to invoke tools; context passed as structured resources. Becoming the de-facto enterprise tool integration standard. | TLC-* (MCP tool chains), CLR-* (resource context requests) |
| **A2A (Agent-to-Agent) Protocol** | Google-proposed (2025) open standard for agent interoperability. Agents expose capabilities as "Agent Cards"; orchestrators discover and delegate via standardized HTTP. Enables cross-vendor agent composition. | TLC-* (A2A delegation chains), CNF-* (A2A conflict when agents disagree) |
| **Supervisor + Swarm Hybrid** | Top-level supervisor decomposes intent and delegates to a swarm of specialized agents. Swarm agents collaborate peer-to-peer for sub-tasks; results aggregated by supervisor. Dominant pattern in enterprise deployments as of 2026. | INT-* (supervisor decomposition), MTX-* (swarm state sharing), CNF-* (swarm conflict resolution) |
| **Orchestrator Principal Pattern** | Central Orquestador Principal (main orchestrator) connected bidirectionally to domain agents (Agente1, Agente2, Agente3) and backend services (Servicio A, Servicio B, Base de Datos). Orchestrator is the sole integration point; agents and services never call each other directly. | All categories — this is the primary architecture pattern this matrix tests. |
| **Agentic RAG Orchestration** | Retrieval is an agent, not a static pipeline step. Orchestrator routes queries to a Retrieval Agent which selects the right knowledge source; results fed to generation agents with source attribution. | CLR-* (retrieval before action), TLC-* (retrieval → reasoning → generation chain) |
| **LLM-as-Router** | A dedicated LLM call classifies intent and emits a structured routing decision (agent name + parameters). Replaces rule-based routers. Used in production by enterprise platforms as of 2025. | INT-* (LLM router accuracy), CND-* (LLM conditional gate accuracy) |
| **Persistent Agent Memory** | Agents maintain long-term memory across sessions (MemGPT-style, Zep, Mem0). Orchestrator injects relevant memories into agent context. Critical for enterprise workflows spanning days or weeks. | MTX-* (cross-session context), MTX-006 specifically (prior session recall) |
| **Tool-Use via Structured Outputs** | Orchestrator uses constrained decoding (JSON schema-enforced outputs) to guarantee tool calls are well-formed. Eliminates hallucinated tool names. Standard pattern in OpenAI, Anthropic, and Gemini function-calling as of 2025. | TLC-* (structured tool call chains), CLR-* (structured clarification requests) |
| **Human-in-the-Loop (HITL) Gating** | Orchestrator pauses execution at defined checkpoints for human approval before proceeding. Standard for finance approvals, compliance actions, and legal reviews. Enforced via interrupt nodes (LangGraph) or approval workflows. | CNF-* (HITL escalation), CND-008 (policy gate), TLC-003 (HITL in chain) |
| **Multi-Tenant Orchestration** | Single orchestrator serves multiple business units with isolated context, routing rules, and tool access. Policy engine ensures BU-level data isolation. | CLR-008 (BU-scoped escalation), CNF-005 (regional vs. global), CND-006 (regulatory routing) |

---

## Evaluation via Claude Code Skill

The `/orch-eval` skill turns Claude Code into an interactive evaluation runner:

```
# Inside Claude Code
/orch-eval
```

The skill will:
1. Discover your orchestration system (framework, submission method, observability)
2. Walk through each selected scenario, submitting prompts and capturing responses
3. Score each response against the rubric
4. Generate the full scoring report with recommendations
5. Optionally export results as JSON for CI/CD pipelines

See `.claude/skills/orch-eval.md` for the full skill workflow.

---

## Observability Integration

Every scenario includes `observability_hints` with recommended OpenTelemetry span attributes. Supported platforms:

| Platform | Use Case |
|---|---|
| **Langfuse** | Trace-level scoring, multi-turn session grouping, regression dataset |
| **Phoenix / Arize** | Span-level evaluation, routing accuracy heatmaps, latency analysis |
| **OpenTelemetry** | Generic OTLP export to any collector (Jaeger, Tempo, Honeycomb, Grafana) |
| **CI/CD** | GitHub Actions workflow to gate deployments on eval score |

See `observability/integration_guide.md` for complete setup instructions.

---

## Adding Custom Scenarios

1. Pick the appropriate category folder under `scenarios/`
2. Add your scenario object to the `scenarios` array in the category's `scenarios.json`
3. Ensure the object conforms to `scenarios/schema.json` (validate with `jsonschema`)
4. Assign a unique ID using the category prefix (e.g., `CLR-026` for a new clarification scenario)
5. Scoring weights in your scenario's `scoring` object must sum to 100

Scenario schema fields:
```json
{
  "id": "CLR-026",
  "category": "clarification_required",
  "subcategory": "missing_entity",
  "domain": "hr",
  "title": "My new scenario",
  "prompt": "...",
  "turns": null,
  "expected_routing": { "agents": [...], "pattern": "sequential" },
  "expected_clarification": ["field1", "field2"],
  "failure_modes": ["failure description"],
  "enterprise_impact": "Business consequence if this fails",
  "scoring": { "clarification_completeness": 70, "no_premature_action": 30 },
  "tags": ["clarification", "hr"]
}
```

---

## Design Principles

**Framework-agnostic by design.** Scenarios are pure JSON. Any evaluation harness in any language can consume them. The scoring rubric is explicit enough to minimize inter-rater variance.

**Enterprise-first scenarios.** Every scenario reflects a real business domain (HR, Procurement, IT, Finance, Manufacturing) with documented business consequences if the orchestrator fails. Not toy examples.

**Observability-native.** Scenarios ship with `observability_hints` so evaluation runs are first-class traces in your monitoring stack, not black-box pass/fail checks.

**Safety-sensitive scoring.** Critical failure overrides exist for scenarios where a wrong routing decision has legal, financial, or physical safety implications. A high aggregate score cannot mask a catastrophic single failure.

**2025–2026 pattern coverage.** The matrix is designed to exercise Orchestrator Principal, MCP tool chains, A2A delegation, Supervisor+Swarm hybrids, HITL gating, and persistent memory — the dominant enterprise orchestration patterns emerging from 2025 into 2026.

---

## License

MIT License. See LICENSE for details.

---

*orch-eval-matrix — Built for engineers who need to know their orchestrator works before it touches production.*
