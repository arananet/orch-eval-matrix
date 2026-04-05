# orch-eval-matrix

**Enterprise Orchestration & Routing Evaluation Framework**

![Scenarios](https://img.shields.io/badge/scenarios-75-blue)
![Score Scale](https://img.shields.io/badge/score%20scale-1000%20pts-green)
![Production Threshold](https://img.shields.io/badge/production%20ready-%E2%89%A5850-brightgreen)
![Framework Agnostic](https://img.shields.io/badge/framework-agnostic-lightgrey)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## The Purpose of an Orchestrator

> **Divide the problem into smaller pieces → locate the right agent per domain → manage context precisely → reduce frontier model usage to only what demands it, delegating domain execution to purpose-built agents.**

An orchestrator's job is not to answer questions. It is to:

1. **Decompose** — break a complex user request into the smallest independently solvable sub-problems
2. **Route** — direct each sub-problem to the agent with the right domain expertise
3. **Manage context** — carry exactly the right information between steps, no more, no less
4. **Delegate** — the cost efficiency is a consequence of correct routing, not the goal; the goal is that the right agent handles each problem

**The complexity is in the orchestration and routing itself.** Deciding which agent owns which sub-problem, preserving the right context across steps, detecting when clarification is needed before acting, resolving conflicts between competing constraints, recovering from partial failures — this is where systems break in production. A system that routes everything to a single agent is not an orchestrator; it is a useless wrapper regardless of which model sits behind it.

This matrix does not measure whether an SLM performs better than a frontier model. It measures whether the **routing and orchestration decisions** are correct: did the right agent get called, with the right context, in the right order, with the right fallback when something went wrong.

### Human Oversight as a First-Class Concern

No orchestration system is complete without a clearly defined human oversight layer. This matrix evaluates two distinct patterns:

| Pattern | Definition | When Required |
|---|---|---|
| **Human-in-the-Loop (HITL)** | Orchestrator **pauses and waits** for explicit human approval before proceeding. The workflow cannot continue without it. | High-stakes irreversible actions: financial approvals, compliance sign-offs, legal reviews, safety-critical operations |
| **Human-on-the-Loop (HOTL)** | Orchestrator proceeds autonomously but **notifies a human** who can intervene within a defined window. Execution continues if no intervention occurs. | Routine but monitored actions: standard purchase orders, leave approvals within policy, automated incident responses |

The CNF-* and CND-* scenarios specifically test whether the orchestrator correctly identifies which actions require HITL (hard stop) vs HOTL (proceed with oversight) vs full autonomy. Misclassifying a HITL action as autonomous is a critical failure regardless of the routing decision's correctness.

---

75 production-grade scenarios to validate:

- Multi-intent decomposition & parallel routing
- Missing context clarification flows
- Multi-turn state preservation
- Conditional routing logic
- Conflict detection & escalation
- Tool → tool coordination chains

---

## Background & Lineage

This framework emerged from hands-on experience building enterprise orchestration systems from the ground up. Two prior projects shaped its design directly:

### [octo-agent](https://github.com/arananet/octo-agent)

A decentralized multi-agent orchestration framework inspired by cephalopod biology — the idea that intelligence distributed without losing coherence is more resilient than a single central brain. Octo-agent introduced the **Blackboard Architecture**: a shared, asynchronous state store that acts as the single source of truth across agents. A Strategic Core LLM handles high-level reasoning and conflict resolution; Specialized Arms (smaller, domain-specific models) execute logistics, finance, legal, and other tasks independently. Guardrails are enforced at the infrastructure layer, not the prompt layer.

Key lessons that shaped this evaluation matrix:
- "Central Brain Syndrome" is a real failure mode in enterprise AI — a single bottleneck LLM that owns all decisions doesn't scale and creates brittle systems
- Asynchronous blackboard collaboration exposes context-preservation gaps that synchronous chains hide — exactly what the MTX-* scenarios test
- Guardrail bypass at the prompt level is catastrophic — the critical failure override system in `scoring/thresholds.json` is a direct response to this

### [edgeneuro](https://github.com/arananet/edgeneuro)

An intelligent routing system combining LLMs with symbolic knowledge graphs to orchestrate distributed agent networks. EdgeNeuro introduced the **"Hot Potato" pattern**: the router classifies intent in <50ms at the edge and immediately hands off to a specialized agent, then exits — it never becomes a persistent proxy or bottleneck. A Neuro-Symbolic engine layers a Knowledge Graph (for fast symbolic matching and access control) with an LLM (invoked only when symbolic confidence < 0.5). Security follows **Default Deny**: if no explicit path exists in the knowledge graph, access is physically blocked.

Key lessons that shaped this evaluation matrix:
- Sub-50ms edge routing means intent detection accuracy is the critical variable — poor decomposition cannot be corrected later; the INT-* scenarios stress exactly this
- Hybrid symbolic + neural routing outperforms pure LLM routing for access control and policy gates — the CND-* scenarios are designed to expose systems that skip the symbolic/policy check layer
- Capability-based access control (e.g., `HAS_VALID_TICKET`, `MANAGER_APPROVED`) is more expressive than role-based — the CLR-* and CNF-* scenarios encode these capability-check requirements

---

## What This Is

`orch-eval-matrix` is a **framework-agnostic evaluation corpus** for benchmarking AI orchestration and routing systems. It does **not** implement an orchestrator — it provides the scenarios, scoring rubric, and tooling to evaluate yours.

### Scope

This framework evaluates **complex orchestration patterns**: how an orchestrator decomposes intent, preserves state, applies conditional logic, resolves conflicts, and chains tools correctly in enterprise workflows.

**Out of scope:** Protocol compliance testing (MCP, A2A, REST API, gRPC). Those are communication layer concerns. This matrix assumes your system can call tools and agents — it evaluates whether the *decisions* about what to call, when, and with what context are correct.

Whether you're building on LangGraph, CrewAI, Semantic Kernel, Microsoft Agent Framework, BeeAI, DSPy, Haystack, Agno, or a fully custom orchestration layer, this matrix gives you a consistent, reproducible score across 6 critical enterprise capability dimensions.

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

> These are **orchestration architecture patterns** — how decision-making, state, and routing are structured internally. Protocol compliance (MCP, A2A, REST) is out of scope; this matrix evaluates the orchestration logic above the transport layer.

| Pattern | Description | Key Eval Scenarios |
|---|---|---|
| **Orchestrator Principal** | Central orchestrator connected bidirectionally to domain agents and backend services. The orchestrator is the sole integration point — agents never call each other or services directly. Dominant enterprise topology as of 2025–2026. | All categories — primary architecture pattern this matrix is designed for. |
| **Blackboard Architecture** | Shared asynchronous state store (the "blackboard") as the single source of truth. Agents read and write to the blackboard independently; a Strategic Core LLM resolves conflicts. Pioneered in [octo-agent](https://github.com/arananet/octo-agent). | MTX-* (blackboard state preservation), CNF-* (strategic core conflict resolution) |
| **Neuro-Symbolic Routing** | Layered routing: symbolic knowledge graph handles fast intent matching and access control; LLM invoked only when symbolic confidence falls below threshold. "Default Deny" — no explicit graph path = no route. Pioneered in [edgeneuro](https://github.com/arananet/edgeneuro). | INT-* (hybrid intent classification), CND-* (symbolic policy gates), CLR-* (capability-based access checks) |
| **Hot Potato Pattern** | Edge router classifies intent in <50ms and immediately hands off to a specialized agent, then exits. Router is never a persistent proxy — eliminates the central bottleneck entirely. Pioneered in [edgeneuro](https://github.com/arananet/edgeneuro). | INT-* (fast dispatch accuracy), CLR-* (edge clarification before handoff) |
| **Supervisor + Swarm Hybrid** | Top-level supervisor decomposes intent and delegates to a swarm of specialized agents. Swarm agents collaborate peer-to-peer; results aggregated by supervisor. Dominant pattern in enterprise LangGraph deployments as of 2026. | INT-* (supervisor decomposition), MTX-* (swarm state sharing), CNF-* (supervisor arbitration) |
| **Agno / Agent-as-Function** | Lightweight agents as typed Python functions with structured I/O. Orchestrator calls agents like function calls. Zero framework overhead; maximum composability. | TLC-* (function chain context), INT-* (function dispatch) |
| **LLM-as-Router** | A dedicated LLM call classifies intent and emits a structured routing decision (agent name + parameters). Replaces hard-coded rule trees. Standard in enterprise platforms as of 2025. | INT-* (LLM router accuracy), CND-* (LLM conditional gate accuracy) |
| **Persistent Agent Memory** | Agents maintain long-term memory across sessions (MemGPT-style, Zep, Mem0). Orchestrator injects relevant memories into agent context at session start. Critical for enterprise workflows spanning multiple days. | MTX-013..015 (cross-session context, escalation chains, partial completion) |
| **Agentic RAG Orchestration** | Retrieval is an agent, not a static pipeline step. Orchestrator routes queries to a Retrieval Agent that selects the knowledge source dynamically; output feeds generation agents with source attribution. | CLR-* (retrieve before acting), TLC-* (retrieval → reasoning → generation chain) |
| **Human-in-the-Loop (HITL)** | Orchestrator pauses and waits for explicit human approval before proceeding. Hard stop — workflow cannot continue without it. Standard for high-stakes irreversible actions: financial approvals, compliance sign-offs, safety-critical operations. | CNF-001, CNF-002 (hard-stop escalation), CND-001 (approval gate), TLC-005 (budget approval before PO) |
| **Human-on-the-Loop (HOTL)** | Orchestrator proceeds autonomously but notifies a human who can intervene within a defined window. Execution continues if no intervention occurs. The orchestrator must correctly classify which actions qualify. | CNF-003, CNF-007 (proceed with oversight), CND-003 (auto-approve with notification) |
| **Multi-Tenant Orchestration** | Single orchestrator serves multiple business units with isolated context, routing rules, and tool access permissions. Policy engine enforces BU-level data isolation at the orchestration layer. | CLR-008 (BU-scoped escalation), CNF-005 (regional vs. global policy), CND-006 (regulatory routing) |
| **Strategic Core + Specialist Arms** | Central LLM reserved for strategic decisions and conflict resolution; domain-specific smaller models handle routine execution (logistics, finance, legal). Avoids "Central Brain Syndrome" where one model owns all decisions. Pioneered in [octo-agent](https://github.com/arananet/octo-agent). | CNF-* (strategic core arbitration), INT-* (delegation to specialist arms), TLC-* (arm coordination chains) |

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

## Observability & Feedback

Every scenario includes `observability_hints` with recommended OpenTelemetry span attributes. Supported platforms:

| Platform | Use Case |
|---|---|
| **Langfuse** | Trace-level scoring, multi-turn session grouping, regression dataset |
| **Phoenix / Arize** | Span-level evaluation, routing accuracy heatmaps, latency analysis |
| **OpenTelemetry** | Generic OTLP export to any collector (Jaeger, Tempo, Honeycomb, Grafana) |
| **CI/CD** | GitHub Actions workflow to gate deployments on eval score |

### The Two-Layer Feedback Problem

Observability in orchestration systems must answer two fundamentally different questions, and **conflating them is a common mistake**:

```
Layer 1 — Orchestrator evaluation
  "Did the orchestrator send the request to the right agent?"
  Measured by: routing decision accuracy, clarification trigger rate,
               context completeness passed to agent, HITL/HOTL classification

Layer 2 — Agent evaluation
  "Did the agent give the right response to the user's prompt?"
  Measured by: response correctness, hallucination rate, tool call accuracy,
               answer quality relative to the domain task
```

**This matrix evaluates Layer 1 exclusively.** It tests the orchestration and routing decisions — not the quality of what the downstream agent produces. A correct routing decision to an agent that gives a wrong answer is a passing orchestrator score and a failing agent score. These are different problems that require separate evaluation pipelines.

When setting up observability, structure your traces to separate these layers:
- Orchestrator spans: `orch.intent_count`, `orch.routing_decision`, `orch.clarification_required`, `orch.hitl_triggered`, `orch.context_passed`
- Agent spans: `agent.response_quality`, `agent.tool_calls`, `agent.latency`, `agent.domain`

Feedback loops should feed back to the correct layer: agent response quality feedback improves the agent; routing decision feedback improves the orchestrator. Mixing them corrupts both improvement signals.

See `observability/integration_guide.md` for complete platform setup.

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

**Decomposition-first evaluation.** Every INT-* scenario tests whether the orchestrator breaks a complex prompt into the right sub-problems before routing. A system that sends the full prompt to one agent fails these scenarios — even if it gets the right answer.

**Domain routing accuracy.** Each scenario has an expected domain agent. Routing a finance problem to a general-purpose agent when a Finance Agent exists is a failure, not a partial credit. The complexity being evaluated is the routing decision — not the quality of the agent's downstream response.

**Context efficiency.** The MTX-* scenarios test not just whether context is *retained*, but whether the orchestrator carries it efficiently — passing the minimum necessary state to each downstream agent rather than replaying the full conversation history.

**Framework-agnostic by design.** Scenarios are pure JSON. Any evaluation harness in any language can consume them. The scoring rubric is explicit enough to minimize inter-rater variance.

**Enterprise-first scenarios.** Every scenario reflects a real business domain (HR, Procurement, IT, Finance, Manufacturing) with documented business consequences if the orchestrator fails. Not toy examples.

**Observability-native.** Scenarios ship with `observability_hints` so evaluation runs are first-class traces in your monitoring stack, not black-box pass/fail checks.

**Safety-sensitive scoring.** Critical failure overrides exist for scenarios where a wrong routing decision has legal, financial, or physical safety implications. A high aggregate score cannot mask a catastrophic single failure.

**2025–2026 pattern coverage.** The matrix exercises Orchestrator Principal, Blackboard Architecture, Hot Potato routing, Neuro-Symbolic routing, Supervisor+Swarm hybrids, Strategic Core + Specialist Arms, HITL gating, and persistent memory — the dominant enterprise orchestration *decision* patterns emerging from 2025 into 2026. Protocol compliance (MCP, A2A, REST) is explicitly out of scope: this matrix evaluates the routing and reasoning logic above the transport layer.

---

## License

MIT License. See LICENSE for details.

---

*orch-eval-matrix — Built for engineers who need to know their orchestrator works before it touches production.*

---

**Developer:** [Eduardo Arana](https://github.com/arananet)
